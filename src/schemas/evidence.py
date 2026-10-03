from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional

class ITSConcept(str, Enum):
    """Core concepts from the Interpersonal Theory of Suicide (ITS)."""
    THWARTED_BELONGINGNESS = "thwarted_belongingness"
    PERCEIVED_BURDENSOMENESS = "perceived_burdensomeness"
    HOPELESSNESS = "hopelessness"
    ACQUIRED_CAPABILITY = "acquired_capability"

class EvidenceRecord(BaseModel):
    """A structured record of an extracted ITS concept from the conversation."""
    concept: ITSConcept = Field(..., description="The ITS concept identified.")
    evidence_text: str = Field(..., description="Exact quote from the conversation supporting the concept.")
    turn_index: int = Field(..., description="The 0-based index of the conversation turn where the evidence was found.")
    subject: str = Field(default="patient", description="Who the evidence applies to (e.g., patient, family member).")
    contradicted: bool = Field(default=False, description="Whether this evidence was later contradicted or corrected.")
    contradicted_by_turn: Optional[int] = Field(default=None, description="The turn index that contradicted this evidence, if any.")

class Ledger(BaseModel):
    """The central state mechanism representing the system's memory of ITS evidence."""
    records: List[EvidenceRecord] = Field(default_factory=list, description="All collected ITS evidence records.")
