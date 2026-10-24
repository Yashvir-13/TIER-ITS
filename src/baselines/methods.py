from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from src.schemas import ConversationTurn

class BaselineMethod(ABC):
    """
    Abstract interface for all baseline evaluation methods.
    """
    def __init__(self, client: Optional[object] = None):
        if client is not None:
            self.client = client
        elif genai is not None:
            try:
                self.client = genai.Client()
            except Exception:
                self.client = None
        else:
            self.client = None
        self.model_name = 'gemini-3.8-flash'

    def _cached_generate(self, prompt: str, task: str = "baseline") -> str:
        from src.inference.cache import get_cache
        from src.inference.retry import with_retry
        cache = get_cache()
        cached = cache.get(self.model_name, prompt, task=task)
        if cached:
            return cached
            
        def _call():
            resp = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            text = resp.text or ""
            cache.set(self.model_name, prompt, text, task=task)
            return text
            
        res = with_retry(_call, error_msg=f"{task} error")
        return res or ""

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
            return self._cached_generate(prompt, task="full_context")
        except Exception as e:
            return f"Error generating full-context report: {e}"

class RecentWindowBaseline(BaselineMethod):
    """
    Feeds only the last N turns into the LLM context window.
    """
    def __init__(self, client: Optional[object] = None, window_size: int = 10):
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
            return self._cached_generate(prompt, task="recent_window")
        except Exception as e:
            return f"Error generating recent-window report: {e}"

class SummaryBaseline(BaselineMethod):
    """
    Maintains a running clinical prose summary of the conversation updated recursively 
    every W turns (default W=10). At report time, generates the final clinical summary 
    from the accumulated running summary and clinical protocol.
    """
    def __init__(self, client: Optional[object] = None, chunk_size: int = 10):
        super().__init__(client)
        self.chunk_size = chunk_size

    def update_summary(self, previous_summary: str, turns_chunk: List[ConversationTurn]) -> str:
        """
        Recursively updates the running clinical summary given a new chunk of dialogue turns.
        """
        from src.inference.retry import with_retry
        chunk_str = "\n".join([f"[{t.turn_index}] {t.speaker.title()}: {t.text}" for t in turns_chunk])
        
        prompt = f"""
        You are an expert clinical summarizer. Maintain a running clinical summary of this therapeutic conversation.
        
        CURRENT SUMMARY:
        {previous_summary if previous_summary else "No previous summary (start of conversation)."}
        
        NEW CONVERSATIONAL TURNS:
        {chunk_str}
        
        TASK:
        Provide an updated, concise running clinical summary incorporating any new psychological disclosures, 
        risk factors, protective factors, or resolutions from the new turns. 
        Retain any critical prior information while keeping the summary concise (1-2 paragraphs).
        """
        def _call_llm():
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            return response.text
            
        try:
            return self._cached_generate(prompt, task="summary_update")
        except Exception:
            return previous_summary

    def generate_report(self, turns: List[ConversationTurn], protocol_text: str) -> str:
        # Incrementally update summary across chunks
        running_summary = ""
        for i in range(0, len(turns), self.chunk_size):
            chunk = turns[i:i + self.chunk_size]
            running_summary = self.update_summary(running_summary, chunk)
            
        prompt = f"""
        You are an AI assisting in a clinical context. Generate a concise risk summary based on the provided protocol guidelines.
        
        PROTOCOL GUIDELINES:
        {protocol_text}
        
        ACCUMULATED RUNNING CLINICAL SUMMARY:
        {running_summary}
        
        TASK:
        Write a short clinical summary of the patient's current risk status.
        Ground the summary in the provided guidelines.
        Do NOT make clinical recommendations; only summarize the evidence.
        """
        try:
            return self._cached_generate(prompt, task="summary_report")
        except Exception as e:
            return f"Error generating summary baseline report: {e}"

class TargetOnlyBaseline(BaselineMethod):
    """
    Feeds only the target disclosure turn(s) directly to the LLM.
    Represents the upper bound / ceiling of model detection capability on isolated evidence.
    """
    def generate_report(self, turns: List[ConversationTurn], protocol_text: str, target_turn_indices: Optional[List[int]] = None) -> str:
        if target_turn_indices:
            target_turns = [t for t in turns if t.turn_index in target_turn_indices]
        else:
            # Fallback: find patient turns
            target_turns = [t for t in turns if t.speaker == "patient"][:1]
            
        turns_str = "\n".join([f"[{t.turn_index}] {t.speaker.title()}: {t.text}" for t in target_turns])
        
        prompt = f"""
        You are an AI assisting in a clinical context. Generate a concise risk summary based on the provided protocol guidelines.
        
        PROTOCOL GUIDELINES:
        {protocol_text}
        
        TARGET PATIENT STATEMENT:
        {turns_str}
        
        TASK:
        Write a short clinical summary of the patient's current risk status. 
        Ground the summary in the provided guidelines.
        Do NOT make clinical recommendations; only summarize the evidence.
        """
        try:
            return self._cached_generate(prompt, task="target_only")
        except Exception as e:
            return f"Error generating target-only report: {e}"

class GoldLedgerBaseline(BaselineMethod):
    """
    Bypasses the automatic extraction LLM by populating the ledger with ground-truth
    concept annotations. Disentangles concept extraction errors from retrieval and report synthesis.
    """
    def generate_report_with_gold(self, gold_records: list, relevant_turns: List[ConversationTurn], protocol_text: str) -> str:
        evidence_str = "\n".join([f"- {r.concept.value}: {r.evidence_text}" for r in gold_records])
        turns_str = "\n".join([f"[{t.turn_index}] {t.speaker.title()}: {t.text}" for t in relevant_turns])
        
        prompt = f"""
        You are an AI assisting in a clinical context. Generate a concise risk summary based on the provided protocol guidelines.
        
        PROTOCOL GUIDELINES:
        {protocol_text}
        
        ACTIVE RISK FACTORS (From Verified Gold Clinical Memory):
        {evidence_str if evidence_str else "None explicitly tracked."}
        
        RELEVANT RECENT CONVERSATION CONTEXT:
        {turns_str if turns_str else "No recent relevant context."}
        
        TASK:
        Write a short (3-4 sentences) clinical summary of the patient's current risk status. 
        Focus heavily on the Active Risk Factors. Ground the summary in the provided guidelines.
        Do NOT make clinical recommendations; only summarize the evidence.
        """
        try:
            return self._cached_generate(prompt, task="gold_ledger")
        except Exception as e:
            return f"Error generating gold-ledger report: {e}"

    def generate_report(self, turns: List[ConversationTurn], protocol_text: str) -> str:
        # Default fallback
        return self.generate_report_with_gold([], turns[-3:], protocol_text)

class GenericQuoteRecord(BaseModel):
    quote: str
    turn_index: int
    is_active: bool = True
    resolved_by_turn: Optional[int] = None

class GenericLedgerBaseline(BaselineMethod):
    """
    Generic Structured-Memory Baseline (Ablation):
    Maintains an ordinary structured memory ledger with verbatim patient quotes and temporal status
    (active vs contradicted/resolved) WITHOUT the Interpersonal Theory of Suicide (ITS) construct taxonomy.
    Tests whether clinical theory indexing (TB/PB/AC ontology) provides an empirical advantage 
    over generic structured note-taking.
    """
    def __init__(self, client: Optional[object] = None, max_active_records: int = 10):
        super().__init__(client)
        self.max_active_records = max_active_records

    def extract_quotes_from_turn(self, turn: ConversationTurn) -> List[str]:
        if turn.speaker != "patient":
            return []
        prompt = f"""
        Extract any notable patient statements expressing distress, problems, or personal hardship.
        If the turn is casual conversation, pleasantries, or life routine without distress, return 'NONE'.
        
        TURN [{turn.turn_index}] PATIENT:
        "{turn.text}"
        
        Extracted Quote (or NONE):
        """
        resp = (self._cached_generate(prompt, task="generic_quote_extract") or "").strip()
        if "NONE" in resp.upper() or len(resp) < 5:
            return []
        return [resp.strip('"\n ')]

    def check_generic_resolution(self, quote: str, turn: ConversationTurn) -> bool:
        prompt = f"""
        Does this subsequent patient turn resolve, contradict, or invalidate the prior problem statement?
        
        PRIOR STATEMENT:
        "{quote}"
        
        NEW TURN [{turn.turn_index}]:
        "{turn.text}"
        
        Answer strictly 'YES' or 'NO':
        """
        resp = (self._cached_generate(prompt, task="generic_resolution_check") or "").strip()
        return "YES" in resp.upper()

    def process_turns(self, turns: List[ConversationTurn]) -> List[GenericQuoteRecord]:
        records: List[GenericQuoteRecord] = []
        for t in turns:
            if t.speaker == "patient":
                # Check if this turn resolves any prior active quote
                for r in records:
                    if r.is_active and r.turn_index < t.turn_index:
                        if self.check_generic_resolution(r.quote, t):
                            r.is_active = False
                            r.resolved_by_turn = t.turn_index
                # Extract any new quote
                quotes = self.extract_quotes_from_turn(t)
                for q in quotes:
                    records.append(GenericQuoteRecord(quote=q, turn_index=t.turn_index, is_active=True))
                    # Enforce capacity
                    active = [rec for rec in records if rec.is_active]
                    if len(active) > self.max_active_records:
                        active[0].is_active = False
                        active[0].resolved_by_turn = -2
        return records

    def generate_report(self, turns: List[ConversationTurn], protocol_text: str) -> str:
        records = self.process_turns(turns)
        active_quotes = [r for r in records if r.is_active]
        resolved_quotes = [r for r in records if not r.is_active]
        
        active_str = "\n".join([f"- [Turn {r.turn_index}]: \"{r.quote}\"" for r in active_quotes])
        resolved_str = "\n".join([f"- [Turn {r.turn_index}] (Resolved by Turn {r.resolved_by_turn}): \"{r.quote}\"" for r in resolved_quotes])
        
        prompt = f"""
        You are an AI assisting in a clinical context. Generate a concise risk summary based on the provided protocol guidelines.
        
        PROTOCOL GUIDELINES:
        {protocol_text}
        
        STRUCTURED EVIDENCE LEDGER (Generic Quote Tracking):
        Active Disclosures:
        {active_str if active_str else "None currently active."}
        
        Resolved Disclosures:
        {resolved_str if resolved_str else "None resolved."}
        
        TASK:
        Write a short clinical summary of the patient's current risk status.
        Focus on active disclosures while noting any resolved issues.
        Ground the summary in the provided guidelines.
        Do NOT make clinical recommendations; only summarize the evidence.
        """
        try:
            return self._cached_generate(prompt, task="generic_ledger_report")
        except Exception as e:
            return f"Error generating generic ledger report: {e}"

