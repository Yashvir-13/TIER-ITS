from pydantic import BaseModel
from typing import List

class Turn(BaseModel):
    """A single turn in a conversation."""
    turn_index: int
    speaker: str
    text: str

class Conversation(BaseModel):
    """A full conversation composed of multiple turns."""
    id: str
    turns: List[Turn]

class BenchmarkCase(BaseModel):
    """A test case in the controlled benchmark."""
    case_id: str
    conversation: Conversation
    target_statement: Turn
    target_depth: int
    expected_concept: str
