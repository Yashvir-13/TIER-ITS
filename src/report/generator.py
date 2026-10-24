from typing import List, Optional
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from src.schemas import EvidenceRecord, ConversationTurn
from src.retrieval.protocol import ProtocolRetriever

class ReportGenerator:
    """
    Generates a structured clinical risk report using the current state of the 
    EvidenceLedger, relevant conversation turns, and clinical protocols.
    """
    def __init__(self, client: Optional[object] = None):
        if client is not None:
            self.client = client
        elif genai is not None:
            try:
                self.client = genai.Client(http_options={'timeout': 120000})
            except Exception:
                self.client = None
        else:
            self.client = None
        self.model_name = 'gemini-3.8-flash'
        self.protocol_retriever = ProtocolRetriever()
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        
    def generate_report(self, active_evidence: List[EvidenceRecord], relevant_turns: List[ConversationTurn], protocol_name: str = "SAFE-T") -> str:
        """
        Synthesizes the memory (ledger), context (retrieved turns), and guidelines (protocol)
        into a final report.
        """
        from src.inference.tokens import count_tokens_from_response
        protocol_text = self.protocol_retriever.get_protocol(protocol_name)
        
        evidence_str = "\n".join([f"- [Turn {r.turn_index}] {r.concept.value}: \"{r.evidence_text}\"" for r in active_evidence])
        turns_str = "\n".join([f"[{t.turn_index}] {t.speaker.title()}: {t.text}" for t in relevant_turns])
        
        prompt = f"""
        You are an AI assisting in a clinical context. Generate a concise risk summary based on the {protocol_name} protocol.
        
        {protocol_name} GUIDELINES:
        {protocol_text}
        
        ACTIVE RISK FACTORS (From ITS Memory):
        {evidence_str if evidence_str else "None explicitly tracked."}
        
        RELEVANT RECENT CONVERSATION CONTEXT:
        {turns_str if turns_str else "No recent relevant context."}
        
        TASK:
        Write a short (3-4 sentences) clinical summary of the patient's current risk status. 
        Focus heavily on the Active Risk Factors. Ground the summary in the provided guidelines.
        Do NOT make clinical recommendations; only summarize the evidence.
        """
        
        from src.inference.cache import get_cache
        cache = get_cache()
        def _call_llm():
            response_obj = None
            cached_text = cache.get(self.model_name, prompt, task="report")
            if cached_text:
                text = cached_text
            else:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.0)
                )
                text = response.text
                response_obj = response
                cache.set(self.model_name, prompt, text, task="report")
                
            p_tok, c_tok = count_tokens_from_response(prompt, text, response_obj)
            self.total_prompt_tokens += p_tok
            self.total_completion_tokens += c_tok
            return text
            
        try:
            from src.inference.retry import with_retry
            return with_retry(_call_llm, error_msg="ReportGenerator error")
        except Exception as e:
            return f"Error generating report: {e}"
