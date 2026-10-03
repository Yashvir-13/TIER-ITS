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
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client()
        self.model_name = model_name

    def extract(self, turn: ConversationTurn) -> Optional[EvidenceRecord]:
        """
        Extracts an ITS concept from a single conversation turn.
        
        Args:
            turn: A ConversationTurn object.
            
        Returns:
            An EvidenceRecord if a concept is found, else None.
        """
        prompt = self._build_prompt(turn)
        
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
            # If the model returns empty strings or nulls for the required fields, 
            # it means no valid concept was found. The schema enforces required fields.
            record = EvidenceRecord(**record_data)
            
            # Since the prompt asks to return the concept if present, 
            # we need a way for the model to indicate "no concept". 
            # In a refined schema, we might add a "NONE" concept, but for now 
            # we assume the model throws a validation error or returns a specific shape if empty.
            return record
        except Exception as e:
            # If it fails to parse or validate, we assume no valid concept was extracted.
            # In a production system, we would log this error.
            return None

    def _build_prompt(self, turn: ConversationTurn) -> str:
        return f"""
        You are an expert clinical psychologist analyzing a conversation for signs of the Interpersonal Theory of Suicide (ITS).
        
        Analyze the following conversational turn by the '{turn.speaker}':
        "{turn.text}"
        
        Extract the most prominent ITS concept present in this text (Thwarted Belongingness, Perceived Burdensomeness, Hopelessness, or Acquired Capability).
        If an ITS concept is present, return a JSON object strictly matching the schema.
        If no ITS concept is present, return an empty JSON object {{}}.
        """
