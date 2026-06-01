from typing import Optional, List

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