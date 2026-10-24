from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel
from src.schemas import EvidenceRecord, ConversationTurn

class ContradictionResult(BaseModel):
    contradicts: bool
    rationale: str

class ContradictionResolution(BaseModel):
    record_turn_index: int
    contradicted: bool
    contradicted_by_turn: Optional[int] = None
    rationale: str = ""

class BatchContradictionResult(BaseModel):
    resolutions: List[ContradictionResolution] = []

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
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        
    def assess(self, record: EvidenceRecord, turn: ConversationTurn) -> bool:
        try:
            from google.genai import types
        except ImportError:
            types = None
        import json
        from src.inference.tokens import count_tokens_from_response
        
        prompt = f"""
        You are a clinical psychologist tracking suicide risk factors.
        
        Previously, the patient expressed the following risk factor ({record.concept.value}):
        "{record.evidence_text}"
        
        Now, the patient says:
        "{turn.text}"
        
        Does this new statement directly contradict or resolve the previous risk factor?
        Answer according to the provided schema.
        """
        from src.inference.cache import get_cache
        cache = get_cache()
        def _call_llm():
            response_obj = None
            cached_text = cache.get(self.model_name, prompt, schema="ContradictionResult")
            if cached_text:
                text = cached_text
            else:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ContradictionResult,
                        temperature=0.0,
                    ),
                )
                text = response.text
                response_obj = response
                cache.set(self.model_name, prompt, text, schema="ContradictionResult")
                
            p_tok, c_tok = count_tokens_from_response(prompt, text, response_obj)
            self.total_prompt_tokens += p_tok
            self.total_completion_tokens += c_tok

            result = ContradictionResult(**json.loads(text))
            return result.contradicts
            
        try:
            from src.inference.retry import with_retry
            return with_retry(_call_llm, error_msg="Gemini Assessor network error")
        except Exception as e:
            print(f"Gemini Assessor failed: {e}")
            return False

    def batch_assess(self, records: List[EvidenceRecord], turns: List[ConversationTurn]) -> List[ContradictionResolution]:
        """
        Assesses multiple active records against subsequent conversation turns in a single batched LLM call.
        """
        try:
            from google.genai import types
        except ImportError:
            types = None
        import json
        
        patient_turns = [t for t in turns if t.speaker == "patient"]
        if not records or not patient_turns:
            return []
            
        records_text = "\n".join([
            f"[Record Turn {r.turn_index}] Concept: {r.concept.value} | Quote: \"{r.evidence_text}\""
            for r in records
        ])
        
        turns_text = "\n".join([
            f"[Turn {t.turn_index}] {t.text}"
            for t in patient_turns
        ])
        
        prompt = f"""
        You are an expert clinical psychologist evaluating a therapy conversation for the resolution or contradiction of suicide risk factors (Interpersonal Theory of Suicide).
        
        ACTIVE RISK EVIDENCE TO EVALUATE:
        {records_text}
        
        PATIENT CONVERSATIONAL TURNS:
        {turns_text}
        
        TASK:
        For each active risk record, determine if any subsequent turn from the patient (occurring after the record's turn) directly contradicts, invalidates, or resolves that stated risk factor (e.g. genuine reconnection with family, realizing they are loved and valued, or clarifying that earlier negative feelings were distorted).
        
        Return a resolution object for each record specifying:
        - 'record_turn_index': The turn index of the evaluated record.
        - 'contradicted': True if a subsequent turn resolved or contradicted it, False otherwise.
        - 'contradicted_by_turn': The turn index of the turn that contradicted it (or null if not contradicted).
        - 'rationale': Brief clinical rationale.
        """
        
        def _call_llm():
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=BatchContradictionResult,
                    temperature=0.0,
                ),
            )
            data = json.loads(response.text)
            batch_res = BatchContradictionResult(**data)
            return batch_res.resolutions
            
        try:
            from src.inference.retry import with_retry
            return with_retry(_call_llm, error_msg="Gemini Batch Assessor network error")
        except Exception as e:
            print(f"Gemini Batch Assessor failed: {e}")
            return []

class MockContradictionAssessor(ContradictionAssessor):
    def assess(self, record: EvidenceRecord, turn: ConversationTurn) -> bool:
        return "Actually" in turn.text
