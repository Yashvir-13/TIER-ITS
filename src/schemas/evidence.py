from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime

class ITSConcept(str, Enum):
    THWARTED_BELONGINGNESS = "thwarted_belongingness"
    PERCEIVED_BURDENSOMENESS = "perceived_burdensomeness"
    HOPELESSNESS = "hopelessness"
    ACQUIRED_CAPABILITY = "acquired_capability"
    FEARLESSNESS_ABOUT_DEATH = "fearlessness_about_death"

class EvidenceDirection(str, Enum):
    SUPPORTS = "supports"
    REJECTS = "rejects"
    UNCERTAIN = "uncertain"

class SubjectType(str, Enum):
    SPEAKER = "speaker"
    OTHER_PERSON = "other_person"
    QUOTATION = "quotation"

class Temporality(str, Enum):
    PRESENT = "present"
    PAST = "past"

class EvidenceRecord(BaseModel):
    """Single evidence record in the ITS ledger."""
    concept: ITSConcept
    direction: EvidenceDirection
    turn_index: int = Field(description="0-indexed turn where evidence was found")
    text_span: str = Field(description="Exact quoted text from the turn")
    subject: SubjectType
    temporality: Temporality
    confidence: float = Field(ge=0.0, le=1.0)
    contradiction_of: Optional[int] = Field(
        default=None,
        description="turn_index of a previous record this contradicts"
    )
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

class ITSLedger(BaseModel):
    """Complete evidence ledger for one conversation."""
    conversation_id: str
    records: list[EvidenceRecord] = []
    total_turns_processed: int = 0
