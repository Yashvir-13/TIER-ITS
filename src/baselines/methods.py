from abc import ABC, abstractmethod
from typing import List, Optional
from google import genai
from google.genai import types

from src.schemas import ConversationTurn

class BaselineMethod(ABC):
    """
    Abstract interface for all baseline evaluation methods.
    """
    def __init__(self, client: Optional[genai.Client] = None):
        self.client = client or genai.Client()
        self.model_name = 'gemini-3.8-flash'

    @abstractmethod
    def generate_report(self, turns: List[ConversationTurn], protocol_text: str) -> str:
        """
        Generates a risk report from the provided conversation turns and protocol.
        """
        pass

class FullContextBaseline(BaselineMethod):
    """
    Feeds the entire conversation history into the LLM context window.
    """
    def generate_report(self, turns: List[ConversationTurn], protocol_text: str) -> str:
        turns_str = "\n".join([f"[{t.turn_index}] {t.speaker.title()}: {t.text}" for t in turns])
        
        prompt = f"""
        You are an AI assisting in a clinical context. Generate a concise risk summary based on the provided protocol guidelines.
        
        PROTOCOL GUIDELINES:
        {protocol_text}
        
        FULL CONVERSATION CONTEXT:
        {turns_str}
        
        TASK:
        Write a short clinical summary of the patient's current risk status. 
        Ground the summary in the provided guidelines.
        Do NOT make clinical recommendations; only summarize the evidence.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            return response.text
        except Exception as e:
            return f"Error generating full-context report: {e}"

class RecentWindowBaseline(BaselineMethod):
    """
    Feeds only the last N turns into the LLM context window.
    """
    def __init__(self, client: Optional[genai.Client] = None, window_size: int = 10):
        super().__init__(client)
        self.window_size = window_size

    def generate_report(self, turns: List[ConversationTurn], protocol_text: str) -> str:
        recent_turns = turns[-self.window_size:] if len(turns) > self.window_size else turns
        turns_str = "\n".join([f"[{t.turn_index}] {t.speaker.title()}: {t.text}" for t in recent_turns])
        
        prompt = f"""
        You are an AI assisting in a clinical context. Generate a concise risk summary based on the provided protocol guidelines.
        
        PROTOCOL GUIDELINES:
        {protocol_text}
        
        RECENT CONVERSATION CONTEXT:
        {turns_str}
        
        TASK:
        Write a short clinical summary of the patient's current risk status. 
        Ground the summary in the provided guidelines.
        Do NOT make clinical recommendations; only summarize the evidence.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            return response.text
        except Exception as e:
            return f"Error generating recent-window report: {e}"

class SummaryBaseline(BaselineMethod):
    """
    Maintains a running summary of the conversation. 
    For simplicity in this baseline, we assume we summarize every N turns and keep a rolling summary.
    """
    # This requires more complex state management. For now, it's a stub to be implemented.
    def generate_report(self, turns: List[ConversationTurn], protocol_text: str) -> str:
        return "Summary Baseline not fully implemented yet."
