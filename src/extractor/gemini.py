import os
import json
from typing import Optional
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from src.schemas import EvidenceRecord, ConversationTurn, ITSConcept

from pydantic import BaseModel, Field

class SingleTurnExtraction(BaseModel):
    has_evidence: bool = Field(..., description="True if a clear ITS concept (Thwarted Belongingness, Perceived Burdensomeness, Hopelessness, Acquired Capability) is present in the patient's utterance, False otherwise.")
    concept: Optional[ITSConcept] = Field(default=None, description="The ITS concept identified if has_evidence is True.")
    evidence_text: Optional[str] = Field(default=None, description="Exact verbatim quote from the patient's utterance supporting the concept.")
    subject: str = Field(default="patient", description="Who the statement applies to (e.g. 'patient' or 'other'). Statements about other people should note 'other'.")
    confidence: float = Field(default=1.0, description="Confidence score from 0.0 to 1.0.")

class GeminiExtractor:
    """
    Deep module for extracting ITS concepts from conversation turns.
    Hides the complexity of Gemini API interaction, prompt engineering,
    and JSON structured output parsing behind a simple interface.
    """
    def __init__(self, model_name: str = "gemini-3.8-flash", api_key: Optional[str] = None):
        # We rely on the google-genai library to pick up GEMINI_API_KEY from env
        # if api_key is not explicitly provided.
        if api_key and genai is not None:
            try:
                self.client = genai.Client(api_key=api_key, http_options={'timeout': 120000})
            except Exception:
                self.client = None
        elif genai is not None:
            try:
                self.client = genai.Client(http_options={'timeout': 120000})
            except Exception:
                self.client = None
        else:
            self.client = None
        self.model_name = model_name
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def extract(self, turn: ConversationTurn, context_turn: Optional[ConversationTurn] = None) -> Optional[EvidenceRecord]:
        """
        Extracts an ITS concept from a single conversation turn in an online streaming setting.
        
        Args:
            turn: The current patient ConversationTurn object.
            context_turn: Optional preceding turn (e.g. therapist question) for conversational grounding.
            
        Returns:
            An EvidenceRecord if a valid patient ITS concept is found, else None.
        """
        from src.inference.retry import with_retry
        from src.inference.tokens import count_tokens_from_response
        if turn.speaker != "patient":
            return None
            
        prompt = self._build_prompt(turn, context_turn)
        
        from src.inference.cache import get_cache
        cache = get_cache()
        
        def _call_llm():
            response_obj = None
            cached_text = cache.get(self.model_name, prompt, schema="SingleTurnExtraction")
            if cached_text:
                text = cached_text
            else:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=SingleTurnExtraction,
                        temperature=0.0,
                    ),
                )
                text = response.text
                response_obj = response
                cache.set(self.model_name, prompt, text, schema="SingleTurnExtraction")
                
            p_tok, c_tok = count_tokens_from_response(prompt, text, response_obj)
            self.total_prompt_tokens += p_tok
            self.total_completion_tokens += c_tok

            try:
                data = json.loads(text)
                res = SingleTurnExtraction(**data)
                if res.has_evidence and res.concept and res.evidence_text and res.subject == "patient":
                    return EvidenceRecord(
                        concept=res.concept,
                        evidence_text=res.evidence_text,
                        turn_index=turn.turn_index,
                        subject=res.subject,
                        confidence=res.confidence
                    )
                return None
            except Exception as e:
                return None
                
        try:
            return with_retry(_call_llm, error_msg="Extractor network error")
        except Exception:
            return None

    def batch_extract(self, turns: list[ConversationTurn]) -> list[EvidenceRecord]:
        """
        Extracts ITS concepts from multiple conversation turns in a single batch API call.
        This is an optimization for batch experiments to avoid hitting rate limits.
        """
        from src.schemas import Ledger # Import locally or at top
        from src.inference.retry import with_retry
        
        patient_turns = [t for t in turns if t.speaker == "patient"]
        if not patient_turns:
            return []
            
        # Format all turns into a numbered list
        turns_text = "\n".join([f"Turn {t.turn_index}: {t.text}" for t in patient_turns])
        
        prompt = f"""
        You are an expert clinical psychologist analyzing a conversation for signs of the Interpersonal Theory of Suicide (ITS).
        
        Analyze the following conversational turns from the patient:
        
        {turns_text}
        
        Extract ANY prominent ITS concepts present in these texts (Thwarted Belongingness, Perceived Burdensomeness, Hopelessness, or Acquired Capability).
        For each concept found, create a record. Ensure the 'turn_index' precisely matches the turn index provided in the text above.
        Return a JSON object containing a list of 'records'.
        """
        
        def _call_llm():
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Ledger,
                    temperature=0.0,
                ),
            )
            try:
                ledger_data = json.loads(response.text)
                ledger = Ledger(**ledger_data)
                return ledger.records
            except Exception as e:
                print(f"Batch parse error: {e}")
                return []
                
        try:
            return with_retry(_call_llm, error_msg="Batch extractor network error")
        except Exception:
            return []

    def _build_prompt(self, turn: ConversationTurn, context_turn: Optional[ConversationTurn] = None) -> str:
        context_str = ""
        if context_turn:
            context_str = f"PRECEDING CONTEXT:\n[{context_turn.speaker.title()}]: \"{context_turn.text}\"\n\n"
            
        return f"""
        You are an expert clinical psychologist analyzing dialogue turns for signs of the Interpersonal Theory of Suicide (ITS).
        
        {context_str}CURRENT PATIENT UTTERANCE (Turn {turn.turn_index}):
        "{turn.text}"
        
        ITS CONCEPT DEFINITIONS:
        - Thwarted Belongingness: Profound loneliness, feeling completely disconnected, alien, or that no one understands or cares.
        - Perceived Burdensomeness: Feeling that one is a liability/burden to loved ones, and that others would be better off if they were gone.
        - Hopelessness: The explicit belief that painful states will never improve.
        - Acquired Capability: Fearlessness of death or high pain tolerance.
        
        TASK:
        Evaluate whether the current patient utterance contains clear evidence of an ITS concept.
        - If clear evidence is present: set has_evidence=True, select the concept, copy the exact verbatim quote into evidence_text, and specify subject ('patient' or 'other').
        - If this is general everyday distress, stress, fatigue, or neutral conversation without suicidal/ITS risk: set has_evidence=False, concept=null, evidence_text=null.
        """

