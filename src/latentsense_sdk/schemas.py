from enum import Enum

from typing import Optional, List, Dict

from pydantic import BaseModel, Field, ConfigDict

from latentsense_sdk.segments import Segment


class PresignedPostFields(BaseModel):
    model_config = ConfigDict(extra="allow")
    key: str = Field(
        ...,
        description=(
            "Target S3 object key template. Replace `${filename}` "
            "with the file's name before uploading."
        ),
        examples=[
            "projects/000/uploads/001/${filename}",
        ],
    )

    AWSAccessKeyId: str
    policy: str
    signature: str


class PresignedPost(BaseModel):
    url: str
    fields: PresignedPostFields


class InitiateUploadResponse(BaseModel):
    presigned_post: PresignedPost = Field(
        ...,
        description=(
            "Temporary S3 presigned POST payload used to upload files directly "
            "to the corpus input prefix. Expires after 60 minutes."
        ),
    )
    s3_input_corpus_prefix: str = Field(
        ...,
        description=(
            "S3 prefix where uploaded files for this corpus should be stored."
        ),
    )
    corpus_id: str = Field(
        ...,
        description=("ID for the corpus associated with the upload location."),
    )


class SimpleTextFile(BaseModel):
    name: str
    segments: List[Segment]

    @property
    def text(self):
        return "".join(segment.text for segment in self.segments)

    @property
    def semantic_segments(self):
        return [
            segment for segment in self.segments if segment.last_semantic_offset >= -1
        ]

    @property
    def semantic_text(self):
        return "".join(segment.inner_text for segment in self.segments)


class Location(BaseModel):
    start: int
    end: int
    text: Optional[str] = None


class TaskStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    COMPLETION_HANDLING_IN_PROGRESS = "completion_handling_in_progress"
    COMPLETION_HANDLED = "completion_handled"
    FAILED = "failed"


class RunDisplay(BaseModel):
    time: str
    name: str
    user_id: Optional[str] = None
    corpus_ids: List[str]
    cog: str
    id: str
    project_name: str
    email: Optional[str] = None
    corpus_names: Optional[List[str]] = None
    cost: Optional[str] = None
    input_size_bytes: int
    results_size_bytes: int
    status: TaskStatus
    output_file_urls: Optional[Dict[str, str]] = None


class RunsPageAndTotal(BaseModel):
    runs: List[RunDisplay]
    total: int


class RunCreationResponse(BaseModel):
    status: str = "waiting"
    run_id: str
