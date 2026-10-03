from pydantic import BaseModel, Field
from typing import List

class ConversationTurn(BaseModel):
    """A single utterance or turn in a conversation."""
    turn_index: int = Field(..., description="0-based index of the turn.")
    speaker: str = Field(..., description="The speaker, e.g., 'patient' or 'therapist'.")
    text: str = Field(..., description="The exact text of the conversational turn.")

class Conversation(BaseModel):
    """A complete clinical conversation or simulated benchmark case."""
    case_id: str = Field(..., description="Unique identifier for the conversation case.")
    turns: List[ConversationTurn] = Field(default_factory=list, description="Chronological list of conversation turns.")
