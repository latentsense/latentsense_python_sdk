from typing import List, Literal, Optional

from pydantic import BaseModel

from latentsense_sdk.schemas import SimpleTextFile, Location
from latentsense_sdk.segments import Segment


class RelationshipMeasures(BaseModel):
    salience: float
    relevance: float


class RelationshipPartSpan(BaseModel):
    location: Location
    text: Optional[str] = None


class GraphEdge(BaseModel):
    source: str
    canonical_relation: str
    to: str
    num_reasoning_signifiers: int
    original_triplet: str
    proposition: str
    segment: Segment

    @property
    def category(self):
        return self.segment.file_detail.category


class GraphInfo(BaseModel):
    nodes: List[str]
    edges: List[GraphEdge]


class RelationshipAnalysis(BaseModel):
    id: int
    parent: RelationshipPartSpan
    child: RelationshipPartSpan
    relation: RelationshipPartSpan
    measures: RelationshipMeasures
    segment: Segment
    previous_segments: List[Segment]

    def __str__(self):
        return f"{self.parent} - {self.relation} - {self.child}"


class ReasonerXFileAnalysis(BaseModel):
    file: SimpleTextFile
    graph: GraphInfo


class RelsFileAnalysis(BaseModel):
    file: SimpleTextFile
    relationships: List[RelationshipAnalysis]
    concepts: List[str]


class RelsFileAnalysisWithOriginal(RelsFileAnalysis):
    runId: str
    originalBytes: str


class ReasonerXFileAnalysisWithOriginal(ReasonerXFileAnalysis):
    runId: str
    originalBytes: str


### Chat Types


class RexMessage(BaseModel):
    text: str
    type: str


class AiRexMessage(RexMessage):
    type: Literal["ai"] = "ai"
    evidence: List[str]

    def __str__(self):
        evidence_str = "\n".join(f"- {item}" for item in self.evidence)
        return f"{self.text}\n\nEVIDENCE:\n{evidence_str}"

    @classmethod
    def from_text(cls, text) -> "AiRexMessage":
        # todo also pass in list of valid propositions
        #  and validate evidence list here matches them

        if "EVIDENCE:" in text:
            response_text, evidence_string = text.split("EVIDENCE:", 1)
            raw_evidence = [
                citation.strip()
                for citation in evidence_string.split("\n")
                if "-" in citation
            ]
            evidence = []
            for citation in raw_evidence:
                citation = citation.replace("-", "").strip()
                if citation[0] in ("'", '"'):
                    citation = citation[1:]
                if citation[-1] in ("'", '"'):
                    citation = citation[:-1]
                evidence.append(citation)
        else:
            response_text = text
            evidence = []

        ai_rex_message = AiRexMessage(text=response_text, evidence=evidence)

        return ai_rex_message
