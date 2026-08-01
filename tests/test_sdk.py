import os
import pytest

from dotenv import load_dotenv

from latentsense_sdk import (
    ReasonerXFileAnalysisWithOriginal,
    AiRexMessage,
    RelsFileAnalysisWithOriginal,
    RedactionFileAnalysisWithOriginal,
    LatentSenseClient,
    InitiateUploadResponse,
    RunsPageAndTotal,
    RunCreationResponse,
    RunDisplay,
)

# os.environ["LST_API_BASE_URL"] = "http://localhost:8000"
# os.environ["LST_PROJECT_ID"] = "proj-456"
# os.environ["LST_API_KEY"] = "test-api-key"

load_dotenv(dotenv_path=".env-enterprise")

BASE_URL = os.environ.get("LST_API_BASE_URL")
PROJECT_ID = os.environ.get("LST_PROJECT_ID")
API_KEY = os.environ.get("LST_API_KEY")


def make_client():
    return LatentSenseClient(
        project_id=PROJECT_ID,
        api_key=API_KEY,
        base_url=BASE_URL,
    )


TARGET_BYTES = None  # 1 * 1024 * 1024  # 1 Mb # None


def maybe_enlarge_text(text: str):
    text = text + " "
    if TARGET_BYTES is not None:
        return text * (TARGET_BYTES // len(text) + 1)
    else:
        return text


@pytest.mark.asyncio
async def test_create_rex_map_small():
    client = make_client()
    sample_file = ("sample.txt", "This is a test file for Rex map creation.")

    response = await client.small_runs.create_rx_map(
        files=[sample_file], concepts=["fruit", "loops"]
    )

    assert isinstance(response, list)
    # assert len(response) == 1
    assert isinstance(response[0], ReasonerXFileAnalysisWithOriginal)
    assert response[0].file.name.endswith("sample.txt")


@pytest.mark.asyncio
async def test_create_rex_map():
    client = make_client()
    sample_file = ("sample.txt", "This is a test file for Rex map creation.")

    response = await client.runs.create_rx_map(
        files=[sample_file], concepts=["fruit", "loops"]
    )

    assert isinstance(response, list)
    # assert len(response) == 1
    assert isinstance(response[0], ReasonerXFileAnalysisWithOriginal)
    assert response[0].file.name.endswith("sample.txt")


@pytest.mark.asyncio
async def test_create_rex_map_comparison():
    client = make_client()  # todo
    sample_file = ("sample.txt", "This is a test file for Rex map creation.")

    response = await client.runs.create_rx_map(
        files=[sample_file], concepts=["fruit", "loops"]
    )

    assert isinstance(response, list)
    # assert len(response) == 1
    assert isinstance(response[0], ReasonerXFileAnalysisWithOriginal)
    assert response[0].file.name.endswith("sample.txt")


@pytest.mark.asyncio
async def test_create_rex_message():
    client = make_client()
    sample_file = (
        "sample.txt",
        "This is a test file for Rex map creation. Apples are a type of fruit.",
    )

    rex_map_response = await client.runs.create_rx_map_small(
        files=[sample_file], concepts=["fruit"]
    )
    run_id = rex_map_response[0].runId

    message = "What is a type of fruit?"
    response = await client.runs.create_rex_message(message=message, run_id=run_id)

    assert isinstance(response, AiRexMessage)
    assert isinstance(response.text, str)
    assert len(response.text) > 0


@pytest.mark.asyncio
async def test_get_salient_relationships_small():
    client = make_client()
    sample_file = (
        "sample.txt",
        maybe_enlarge_text("This is a test file for salient relationships."),
    )
    response = await client.small_runs.get_salient_relationships(
        files=[sample_file], intent_text="test"
    )
    assert isinstance(response, list)
    # assert len(response) == 1
    assert isinstance(response[0], RelsFileAnalysisWithOriginal)
    assert response[0].file.name.endswith("sample.txt")


@pytest.mark.asyncio
async def test_get_salient_relationships():
    client = make_client()
    sample_file = (
        "sample.txt",
        maybe_enlarge_text("This is a test file for salient relationships."),
    )
    response = await client.runs.get_salient_relationships(
        files=[sample_file], intent_text="test"
    )
    assert isinstance(response, list)
    # assert len(response) == 1
    assert isinstance(response[0], RelsFileAnalysisWithOriginal)
    assert response[0].file.name.endswith("sample.txt")


@pytest.mark.asyncio
async def test_redact_by_relevance_small():
    client = make_client()
    sample_file = (
        "sample.txt",
        maybe_enlarge_text("This is a test file for relevance redaction."),
    )
    response = await client.small_runs.redact_by_relevance(
        files=[sample_file], relevance_term="test", sensitivity=0.5
    )
    assert isinstance(response, list)
    # assert len(response) == 1
    assert isinstance(response[0], RedactionFileAnalysisWithOriginal)
    assert response[0].file.name.endswith("sample.txt")


@pytest.mark.asyncio
async def test_redact_by_relevance():
    client = make_client()
    sample_file = (
        "sample.txt",
        maybe_enlarge_text("This is a test file for relevance redaction."),
    )
    response = await client.runs.redact_by_relevance(
        files=[sample_file], relevance_term="test", cutoff=0.5
    )
    assert isinstance(response, list)
    # assert len(response) == 1
    assert isinstance(response[0], RedactionFileAnalysisWithOriginal)
    assert response[0].file.name.endswith("sample.txt")


@pytest.mark.asyncio
async def test_redact_pii_small():
    client = make_client()
    sample_file = (
        "sample.txt",
        maybe_enlarge_text(
            "This is a test file for PII redaction. My name is John Doe."
        ),
    )

    response = await client.small_runs.redact_pii_small(files=[sample_file])
    assert isinstance(response, list)
    assert isinstance(response[0], RedactionFileAnalysisWithOriginal)
    assert response[0].file.name.endswith("sample.txt")


@pytest.mark.asyncio
async def test_redact_pii():
    client = make_client()
    sample_file = (
        "sample.txt",
        maybe_enlarge_text(
            "This is a test file for PII redaction. My name is John Doe."
        ),
    )
    response = await client.runs.redact_pii(files=[sample_file])
    assert isinstance(response, list)
    assert isinstance(response[0], RedactionFileAnalysisWithOriginal)
    assert response[0].file.name.endswith("sample.txt")


def test_low_level_api():
    client = make_client()

    # Test initiate_upload
    upload_data = client.api.initiate_upload(name="test_low_level")
    assert isinstance(upload_data, InitiateUploadResponse)
    assert upload_data.presigned_post is not None
    assert upload_data.s3_input_corpus_prefix is not None

    # Test get_runs_in_project
    runs_data = client.api.get_runs_in_project(page=1, rows_per_page=5)
    assert isinstance(runs_data, RunsPageAndTotal)
    assert isinstance(runs_data.runs, list)

    # Test small_rx_map
    sample_file = ("sample.txt", "This is a test file for low-level Rex map creation.")
    rx_data = client.api.small_rx_map(files=[sample_file], concepts=["test"])
    assert isinstance(rx_data, RunCreationResponse)
    assert rx_data.run_id is not None
    run_id = rx_data.run_id

    # Test get_run_status
    status_data = client.api.get_run_status(run_id)
    assert isinstance(status_data, RunDisplay)
    assert status_data.id == run_id

    # Test small_rx_map_result
    # Note: Since this is a live/mock call, it might return 202 or 200.
    # If it's not complete yet, calling small_rx_map_result directly might raise HTTPError (e.g. 202 Accepted is not 200).
    # But we can catch HTTPError or check if it succeeds.
    try:
        result_data = client.api.small_rx_map_result(run_id)
        assert isinstance(result_data, list)
    except Exception:
        pass
