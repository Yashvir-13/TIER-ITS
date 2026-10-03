import os
import json
from typing import Optional
from google import genai
from google.genai import types

from src.schemas import EvidenceRecord, ConversationTurn

class GeminiExtractor:
    """
    Deep module for extracting ITS concepts from conversation turns.
    Hides the complexity of Gemini API interaction, prompt engineering,
    and JSON structured output parsing behind a simple interface.
    """
    def __init__(self, model_name: str = "gemini-3.8-flash", api_key: Optional[str] = None):
        # We rely on the google-genai library to pick up GEMINI_API_KEY from env
        # if api_key is not explicitly provided.
        if api_key:
            self.client = genai.Client(api_key=api_key, http_options={'timeout': 120000})
        else:
            self.client = genai.Client(http_options={'timeout': 120000})
        self.model_name = model_name

    def extract(self, turn: ConversationTurn) -> Optional[EvidenceRecord]:
        """
        Extracts an ITS concept from a single conversation turn.
        
        Args:
            turn: A ConversationTurn object.
            
        Returns:
            An EvidenceRecord if a concept is found, else None.
        """
        import time
        prompt = self._build_prompt(turn)
        
        max_retries = 10
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=EvidenceRecord,
                        temperature=0.0,
                    ),
                )
                
                try:
                    record_data = json.loads(response.text)
                    record = EvidenceRecord(**record_data)
                    return record
                except Exception:
                    return None
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Extractor failed after {max_retries} attempts: {e}")
                    return None
                print(f"Network error (attempt {attempt+1}/{max_retries}): {e}. Waiting 10s...")
                time.sleep(10)

    def batch_extract(self, turns: list[ConversationTurn]) -> list[EvidenceRecord]:
        """
        Extracts ITS concepts from multiple conversation turns in a single batch API call.
        This is an optimization for batch experiments to avoid hitting rate limits.
        """
        from src.schemas import Ledger # Import locally or at top
        import time
        
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
        
        max_retries = 10
        for attempt in range(max_retries):
            try:
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
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Batch extractor failed after {max_retries} attempts: {e}")
                    return []
                print(f"Network error (attempt {attempt+1}/{max_retries}): {e}. Waiting 10s...")
                time.sleep(10)
        return []

    def _build_prompt(self, turn: ConversationTurn) -> str:
        return f"""
        You are an expert clinical psychologist analyzing a conversation for signs of the Interpersonal Theory of Suicide (ITS).
        
        Analyze the following conversational turn by the '{turn.speaker}':
        "{turn.text}"
        
        Extract the most prominent ITS concept present in this text (Thwarted Belongingness, Perceived Burdensomeness, Hopelessness, or Acquired Capability).
        If an ITS concept is present, return a JSON object strictly matching the schema.
        If no ITS concept is present, return an empty JSON object {{}}.
        """
