from pydantic import BaseModel
from typing import List
from .evidence import EvidenceRecord

class ProtocolReference(BaseModel):
    """A reference to a clinical protocol (e.g., C-SSRS)."""
    protocol_name: str
    relevant_passage: str

class InspectableReport(BaseModel):
    """The final generated report, grounded in evidence and protocols."""
    conversation_id: str
    summary: str
    cited_evidence: List[EvidenceRecord]
    protocol_references: List[ProtocolReference]
