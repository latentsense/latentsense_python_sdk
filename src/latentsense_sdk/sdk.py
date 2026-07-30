import os
import asyncio

import requests
from typing import List, Optional, Any, Union, Tuple, IO, Dict, Type, TypeVar
from pydantic import BaseModel

from latentsense_sdk.schemas import InitiateUploadResponse
from latentsense_sdk.workers.redaction import RedactionFileAnalysisWithOriginal
from latentsense_sdk.workers.relationships import (
    ReasonerXFileAnalysisWithOriginal,
    RelsFileAnalysisWithOriginal,
    AiRexMessage,
)
from latentsense_sdk.results import extract_tar_zst_results

FileInput = Union[str, Tuple[str, str]]
ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class LatentSenseClient:
    """
    A Python client for the LatentSense Interactive API.

    This client handles authentication, project ID, and the complexities
    of file uploads, supporting both file paths and in-memory string content.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.session = SessionCore(
            project_id=project_id, api_key=api_key, base_url=base_url
        )
        self.runs = RunsClient(session=self.session)
        self.small_runs = SmallRunsClient(session=self.session)

    async def create_rex_message(
        self, message: str, run_id: str, graph_info: Optional[Dict[str, Any]] = None
    ) -> AiRexMessage:
        """
        Sends a message to a specific ReasonerX (Rex) graph session to get a response.

        message: The message/question to send to the graph.
        run_id: The ID of the Rex graph run to interact with. This is found
                as `runId` for each file in the response from `create_rex_map`.
        """
        endpoint = (
            f"{self.session.base_url}/api/chat/{self.session.project_id}/rex-message"
        )
        params = {
            "message": message,
            "run_id": run_id,
        }

        response = self.session.requests_session.post(
            endpoint, params=params, json=graph_info
        )
        response.raise_for_status()
        return AiRexMessage.model_validate(response.json())


class BaseRunsClient:
    def __init__(self, session: "SessionCore"):
        self.session = session


class RunsClient(BaseRunsClient):
    def __init__(self, session: "SessionCore"):
        super().__init__(session=session)

    async def create_rx_map(
        self,
        files: List[FileInput],
        concepts: Optional[List[str]] = None,
    ) -> List[ReasonerXFileAnalysisWithOriginal]:
        """
        Creates a RxMap knowledge map to analyze the files using the multi-stage process.
        This is useful for breaking down large texts into facts for later analysis, querying semantic spaces in the corpus, or question answering, backed with evidence.
        LLM analysis of the rxMap can be created with `create_rex_message`.

        Each file can be provided as:
        - A string representing the file path (e.g., "my_docs/report.txt").
        - A tuple of (filename, content) (e.g., ("report.txt", "This is my content...")).

        files: A list of primary files to be analyzed.
        concepts: Optional list of concepts expected to exist in the corpus or a related rxMap. Particularly useful if you are extending existing rxMap(s), so the new graph can join onto them.
        """
        payload = {}
        if concepts:
            payload["concepts"] = concepts

        return await self._run_multistage(
            endpoint_path="/runs/rx-map",
            files=files,
            payload=payload,
            response_model=ReasonerXFileAnalysisWithOriginal,
        )

    async def get_salient_relationships(
        self, files: List[FileInput], intent_text: str = None
    ) -> List[RelsFileAnalysisWithOriginal]:
        """
        Lists relationship propositions in the documents that are deemed salient
        and relevant to the intent text.

        Relationships are (subject, predicate, object) triplets. Each has a salience
        score (how much it stands out) and a relevance score (how relevant it is
        to the intent text). This is a paid endpoint.

        files: A list of files to be analyzed. Each file can be a path (str)
               or a (filename, content) tuple.
        intent_text (optional): Text to check for relevance against (e.g., a term, concept, or phrase).
        """
        payload = {"concepts": []}
        if intent_text:
            payload["concepts"].append(intent_text)

        return await self._run_multistage(
            endpoint_path="/runs/relationships-discovery",
            files=files,
            payload=payload,
            response_model=RelsFileAnalysisWithOriginal,
        )

    async def redact_pii(
        self, files: List[FileInput]
    ) -> List[RedactionFileAnalysisWithOriginal]:
        """
        Redacts PII (Personally Identifiable Information) from documents.

        Removes names, dates, addresses, contact info, etc., to make sensitive
        documents safer for sharing or analysis.
        This is a paid endpoint.

        files: A list of files to be redacted. Each file can be a path (str)
               or a (filename, content) tuple.
        """
        return await self._run_multistage(
            endpoint_path="/runs/redact-pii",
            files=files,
            payload={},
            response_model=RedactionFileAnalysisWithOriginal,
        )

    async def _run_multistage(
        self,
        endpoint_path: str,
        files: List[FileInput],
        payload: dict,
        response_model: Type[ResponseModelT],
    ) -> List[ResponseModelT]:
        upload_data = self._initiate_upload()
        self._upload_files(files=files, upload_data=upload_data)
        run_id = self._request_run(
            payload=payload, endpoint_path=endpoint_path, upload_data=upload_data
        )
        output_file_urls = await self._get_run_result(run_id=run_id)
        results = self._download_results(
            output_file_urls=output_file_urls,
            run_id=run_id,
            response_model=response_model,
        )

        return results

    def _request_run(
        self, payload: dict, endpoint_path: str, upload_data: InitiateUploadResponse
    ):
        run_payload = {
            "input_prefixes": [upload_data.s3_input_corpus_prefix],
            "parameters": payload,
        }
        run_resp = self.session.requests_session.post(
            f"{self.session.base_url}{endpoint_path}", json=run_payload
        )
        run_resp.raise_for_status()
        run_id = run_resp.json()["run_id"]
        return run_id

    def _initiate_upload(self) -> InitiateUploadResponse:
        upload_resp = self.session.requests_session.post(
            f"{self.session.base_url}/projects/{self.session.project_id}/uploads",
            json={},
        )
        upload_resp.raise_for_status()
        upload_data = InitiateUploadResponse(**upload_resp.json())
        return upload_data

    def _upload_files(
        self, files: List[FileInput], upload_data: InitiateUploadResponse
    ):
        for file_input in files:
            if isinstance(file_input, str):
                filename = os.path.basename(file_input)
                with open(file_input, "rb") as f:
                    file_content = f.read()
            else:
                filename, file_content = file_input

            field_json = upload_data.presigned_post.fields.model_dump()
            # fields.key = fields.key.replace("${filename}", filename)
            field_json["key"] = field_json["key"].replace("${filename}", filename)

            files_dict = {"file": (filename, file_content)}
            upload_res = requests.post(
                upload_data.presigned_post.url,
                data=field_json,
                files=files_dict,
            )
            upload_res.raise_for_status()

    async def _get_run_result(self, run_id: str) -> Dict[str, str]:
        while True:
            await asyncio.sleep(5)
            status_resp = self.session.requests_session.get(
                f"{self.session.base_url}/runs/{run_id}"
            )
            status_resp.raise_for_status()
            status_data = status_resp.json()
            if status_data["status"] == "complete":
                break
            elif status_data["status"] == "failed":
                raise Exception(f"Run {run_id} failed")
        return status_data.get("output_file_urls", {})

    def _download_results(
        self,
        output_file_urls: Dict[str, str],
        run_id: str,
        response_model: Type[ResponseModelT],
    ) -> List[ResponseModelT]:
        results: List[ResponseModelT] = []
        for key, url in output_file_urls.items():
            file_resp = requests.get(url)
            file_resp.raise_for_status()
            results.extend(
                extract_tar_zst_results(file_resp.content, run_id, response_model)
            )
        return results


class SmallRunsClient(BaseRunsClient):
    def __init__(self, session: "SessionCore"):
        super().__init__(session=session)

    async def create_rx_map(
        self,
        files: List[FileInput],
        concepts: Optional[List[str]] = None,
    ) -> List[ReasonerXFileAnalysisWithOriginal]:
        """
        Creates a RxMap knowledge map to analyze the files using the small job endpoint.
        This is useful for breaking down large texts into facts for later analysis, querying semantic spaces in the corpus, or question answering, backed with evidence.
        LLM analysis of the rxMap can be created with `create_rex_message`.

        Each file can be provided as:
        - A string representing the file path (e.g., "my_docs/report.txt").
        - A tuple of (filename, content) (e.g., ("report.txt", "This is my content...")).

        files: A list of primary files to be analyzed.
        concepts: Optional list of concepts expected to exist in the corpus or a related rxMap. Particularly useful if you are extending existing rxMap(s), so the new graph can join onto them.
        """
        endpoint = (
            f"{self.session.base_url}/runs/small/{self.session.project_id}/rx-map"
        )
        opened_files = []

        try:
            file_parts = {"files": files}
            multipart_payload, opened_files = self._prepare_payload(**file_parts)

            data_payload = {}
            if concepts:
                data_payload["concepts"] = concepts

            json_response = self.session.requests_session.post(
                endpoint,
                files=multipart_payload,
                data=data_payload,
            )
            json_response.raise_for_status()
            run_id = json_response.json()["run_id"]

            return await self._wait_for_small_run_result(
                run_id=run_id,
                endpoint_suffix="rx-map",
                response_model=ReasonerXFileAnalysisWithOriginal,
            )
        finally:
            for f in opened_files:
                f.close()

    async def get_salient_relationships(
        self, files: List[FileInput], intent_text: str = None
    ) -> List[RelsFileAnalysisWithOriginal]:
        """
        Lists relationship propositions in the documents that are deemed salient
        and relevant to the intent text.

        Relationships are (subject, predicate, object) triplets. Each has a salience
        score (how much it stands out) and a relevance score (how relevant it is
        to the intent text). This is a paid endpoint.

        files: A list of files to be analyzed. Each file can be a path (str)
               or a (filename, content) tuple.
        intent_text (optional): Text to check for relevance against (e.g., a term, concept, or phrase).
        """
        endpoint = f"{self.session.base_url}/runs/small/{self.session.project_id}/relationships-discovery"
        opened_files = []
        try:
            file_parts = {"files": files}
            multipart_payload, opened_files = self._prepare_payload(**file_parts)

            data = {"concepts": []}
            if intent_text:
                data["concepts"].append(intent_text)

            response = self.session.requests_session.post(
                endpoint,
                files=multipart_payload,
                data=data,
            )
            response.raise_for_status()
            run_id = response.json()["run_id"]

            return await self._wait_for_small_run_result(
                run_id=run_id,
                endpoint_suffix="relationships-discovery",
                response_model=RelsFileAnalysisWithOriginal,
            )
        finally:
            for f in opened_files:
                f.close()

    async def redact_by_relevance(
        self, files: List[FileInput], relevance_term: str, sensitivity: float
    ) -> List[RedactionFileAnalysisWithOriginal]:
        """
        Removes information from documents that is relevant to a given term.

        You can tune how much text is redacted with the `sensitivity` parameter. A value
        closer to 0 will redact more, and a value closer to 1 will redact less.
        This is a paid endpoint.

        files: A list of files to be redacted. Each file can be a path (str)
               or a (filename, content) tuple.
        relevance_term: The concept, term, or phrase to redact.
        sensitivity: A number between 0 and 1 where a lower number results in more redaction.
        """
        endpoint = f"{self.session.base_url}/runs/small/{self.session.project_id}/redact-relevance"
        opened_files = []
        try:
            file_parts = {"files": files}
            multipart_payload, opened_files = self._prepare_payload(**file_parts)

            data_payload = {
                "relevance_term": relevance_term,
                "sensitivity": sensitivity,
            }

            response = self.session.requests_session.post(
                endpoint,
                data=data_payload,
                files=multipart_payload,
            )
            response.raise_for_status()
            run_id = response.json()["run_id"]

            return await self._wait_for_small_run_result(
                run_id=run_id,
                endpoint_suffix="redact-relevance",
                response_model=RedactionFileAnalysisWithOriginal,
            )
        finally:
            for f in opened_files:
                f.close()

    async def redact_pii(
        self, files: List[FileInput]
    ) -> List[RedactionFileAnalysisWithOriginal]:
        """
        Redacts PII (Personally Identifiable Information) from documents.

        Removes names, dates, addresses, contact info, etc., to make sensitive
        documents safer for sharing or analysis.
        This is a paid endpoint.

        files: A list of files to be redacted. Each file can be a path (str)
               or a (filename, content) tuple.
        """
        endpoint = (
            f"{self.session.base_url}/runs/small/{self.session.project_id}/redact-pii"
        )
        opened_files = []
        try:
            multipart_payload, opened_files = self._prepare_payload(files=files)

            response = self.session.requests_session.post(
                url=endpoint,
                files=multipart_payload,
            )
            response.raise_for_status()
            run_id = response.json()["run_id"]

            return await self._wait_for_small_run_result(
                run_id=run_id,
                endpoint_suffix="redact-pii",
                response_model=RedactionFileAnalysisWithOriginal,
            )
        finally:
            for f in opened_files:
                f.close()

    async def _wait_for_small_run_result(
        self, run_id: str, endpoint_suffix: str, response_model: Type[ResponseModelT]
    ) -> List[ResponseModelT]:
        url = f"{self.session.base_url}/runs/small/{run_id}/result/{endpoint_suffix}"
        await asyncio.sleep(5)
        while True:
            res = self.session.requests_session.get(url)
            if res.status_code == 202:
                await asyncio.sleep(5)
                continue
            res.raise_for_status()
            return [response_model.model_validate(obj) for obj in res.json()]

    def _prepare_payload(self, **file_parts) -> Tuple[List[Tuple[str, str]], List[IO]]:
        """Prepares the multipart/form-data payload and tracks opened files."""
        multipart_payload = []
        opened_files = []

        def add_to_payload(part_name: str, file_input: FileInput):
            if isinstance(file_input, str):  # Input is a file path
                # Open the file and add its object to the tracking list
                f = open(file_input, "rb")
                opened_files.append(f)
                multipart_payload.append(
                    (part_name, (os.path.basename(file_input), f, "text/plain"))
                )
            elif (
                isinstance(file_input, tuple) and len(file_input) == 2
            ):  # Input is (filename, content)
                filename, content = file_input
                # Content can be passed directly
                multipart_payload.append((part_name, (filename, content, "text/plain")))
            else:
                raise TypeError(
                    f"Invalid file input type for '{part_name}': {file_input}. Must be a path (str) or a (filename, content) tuple."
                )

        for part_name, file_inputs in file_parts.items():
            if not file_inputs:
                continue

            if isinstance(file_inputs, list):
                for file_input in file_inputs:
                    add_to_payload(part_name, file_input)
            else:
                add_to_payload(part_name, file_inputs)

        return multipart_payload, opened_files


class SessionCore:
    def __init__(
        self,
        project_id: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.project_id = project_id or os.environ.get("LST_PROJECT_ID")
        self.api_key = api_key or os.environ.get("LST_API_KEY")

        if not self.project_id:
            raise ValueError(
                "Project ID must be provided or set as LST_PROJECT_ID environment variable."
            )
        if not self.api_key:
            raise ValueError(
                "API key must be provided or set as LST_API_KEY environment variable."
            )

        self.base_url = base_url or os.environ.get(
            "LST_API_BASE_URL", "https://controller.latentsense.com"
        )
        self.requests_session = requests.Session()
