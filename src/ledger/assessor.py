from abc import ABC, abstractmethod
from pydantic import BaseModel
from src.schemas import EvidenceRecord, ConversationTurn

class ContradictionResult(BaseModel):
    contradicts: bool
    rationale: str

class ContradictionAssessor(ABC):
    """
    Adapter interface (Seam) for assessing contradictions.
    Decouples the domain logic from specific LLM implementations.
    """
    @abstractmethod
    def assess(self, record: EvidenceRecord, turn: ConversationTurn) -> bool:
        pass

class GeminiContradictionAssessor(ContradictionAssessor):
    def __init__(self, client):
        self.client = client
        self.model_name = 'gemini-3.8-flash'
        
    def assess(self, record: EvidenceRecord, turn: ConversationTurn) -> bool:
        from google.genai import types
        import json
        
        prompt = f"""
        You are a clinical psychologist tracking suicide risk factors.
        
        Previously, the patient expressed the following risk factor ({record.concept.value}):
        "{record.evidence_text}"
        
        Now, the patient says:
        "{turn.text}"
        
        Does this new statement directly contradict or resolve the previous risk factor?
        Answer according to the provided schema.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ContradictionResult,
                    temperature=0.0,
                ),
            )
            result = ContradictionResult(**json.loads(response.text))
            return result.contradicts
        except Exception as e:
            print(f"Gemini Assessor failed: {e}")
            return False

class MockContradictionAssessor(ContradictionAssessor):
    def assess(self, record: EvidenceRecord, turn: ConversationTurn) -> bool:
        return "Actually" in turn.text
