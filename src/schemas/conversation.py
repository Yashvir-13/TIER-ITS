from typing import List, Optional
from pydantic import BaseModel, Field

class ConversationTurn(BaseModel):
    """A single utterance or turn in a conversation."""
    turn_index: int = Field(..., description="0-based index of the turn.")
    speaker: str = Field(..., description="The speaker, e.g., 'patient' or 'therapist'.")
    text: str = Field(..., description="The exact text of the conversational turn.")

class Conversation(BaseModel):
    """A complete clinical conversation or simulated benchmark case."""
    case_id: str = Field(..., description="Unique identifier for the conversation case.")
    turns: List[ConversationTurn] = Field(default_factory=list, description="Chronological list of conversation turns.")
    concept: Optional[str] = Field(default=None, description="Target ITS concept if benchmark case.")
    nuance_level: Optional[str] = Field(default=None, description="Nuance level (explicit, implicit, fragmented).")
    initial_turn_index: Optional[int] = Field(default=None, description="Turn index of initial disclosure.")
    correction_turn_index: Optional[int] = Field(default=None, description="Turn index of correction utterance.")
    gap: Optional[int] = Field(default=None, description="Number of turns between disclosure and correction.")
    expected_final_risk: Optional[bool] = Field(default=None, description="Expected risk assessment outcome at end of session.")
    is_negative_control: bool = Field(default=False, description="True if case is a negative control with no ITS concepts.")
    is_non_correction_control: bool = Field(default=False, description="True if case is a non-correction control where risk persists.")
    target_evidence_turns: List[int] = Field(default_factory=list, description="Exact list of turn indices containing target risk evidence.")
