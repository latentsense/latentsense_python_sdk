from typing import Optional, List, Tuple

from pydantic import BaseModel

from latentsense_sdk.schemas import SimpleTextFile
from latentsense_sdk.segments import Segment


class Redaction(BaseModel):
    score: float
    entity_type: str
    text: str
    start: int
    end: int
    word_pairs: Optional[List[Tuple[float, str, str]]] = None


class RedactionsForSegment(BaseModel):
    segment: Segment
    redacted_text: str
    redactions: List[Redaction]

    @property
    def full_redacted_text(self):
        return self.segment.prefix + self.redacted_text + self.segment.suffix


class RedactionFileAnalysis(BaseModel):
    file: SimpleTextFile
    redacted: str
    redactions_for_segments: List[RedactionsForSegment]
    report: str
    cutoff: float
    relevance_term: Optional[str] = None


class RedactionFileAnalysisWithOriginal(RedactionFileAnalysis):
    runId: str
    originalBytes: str
