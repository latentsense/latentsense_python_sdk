import io
import json
import tarfile
from typing import List, Type, TypeVar

import zstandard
from pydantic import BaseModel

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


def extract_tar_zst_results(
        compressed_content: bytes,
        run_id: str,
        response_model: Type[ResponseModelT]
) -> List[ResponseModelT]:
    results = []
    zstd_decompressor = zstandard.ZstdDecompressor()
    tar_bytes = zstd_decompressor.decompress(compressed_content)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r") as tar:
        for member in tar.getmembers():
            if member.isfile():
                f = tar.extractfile(member)
                if f is not None:
                    content = f.read().decode("utf-8")
                    content_objs = json.loads(content)
                    for content_obj in content_objs:
                        content_obj["runId"] = run_id
                        content_obj["originalBytes"] = ""
                        results.append(response_model.model_validate(content_obj))
    return results
