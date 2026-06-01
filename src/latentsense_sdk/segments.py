from typing import Optional

from pydantic import BaseModel


class FileDetail(BaseModel):
    path: str
    category: Optional[str] = None


class Segment(BaseModel):
    first_index: int  # First char's index in the source text
    first_semantic_offset: int  # first text char's index in the segment
    last_semantic_offset: int  # last text char's index in the segment
    last_index: int  # last char's index in the source text (redundant given text)
    text: str
    file_detail: FileDetail
    is_hidden: bool = False

    @property
    def inner_text(self) -> str:
        return self.text[self.first_semantic_offset : self.last_semantic_offset + 1]

    @property
    def prefix(self) -> str:
        return self.text[: self.first_semantic_offset]

    @property
    def suffix(self) -> str:
        return self.text[self.last_semantic_offset + 1 :]

    @property
    def is_semantic(self) -> bool:
        return bool(self.inner_text)

    @classmethod
    def new(
        cls,
        first_index: int,
        text: str,
        file_detail: FileDetail,
        is_semantic: bool = True,
        first_semantic_offset: int = None,
        last_semantic_offset: int = None,
        is_hidden: bool = False,
    ):
        last_index = first_index + len(text) - 1

        if is_semantic:
            if first_semantic_offset is None:
                first_semantic_offset = 0
            if last_semantic_offset is None:
                last_semantic_offset = last_index - first_index
        else:
            first_semantic_offset = 0
            last_semantic_offset = -1

        return cls(
            first_index=first_index,
            last_index=last_index,
            text=text,
            first_semantic_offset=first_semantic_offset,
            last_semantic_offset=last_semantic_offset,
            is_hidden=is_hidden,
            file_detail=file_detail,
        )

    def __hash__(self):
        # treats text as redundant
        return hash(
            (
                self.first_index,
                self.last_index,
                self.first_semantic_offset,
                self.last_semantic_offset,
            )
        )
