from typing import List, Optional
from google import genai
from google.genai import types

from src.schemas import EvidenceRecord, ConversationTurn
from src.retrieval.protocol import ProtocolRetriever

class ReportGenerator:
    """
    Generates a structured clinical risk report using the current state of the 
    EvidenceLedger, relevant conversation turns, and clinical protocols.
    """
    def __init__(self, client: Optional[genai.Client] = None):
        self.client = client or genai.Client()
        self.model_name = 'gemini-3.8-flash'
        self.protocol_retriever = ProtocolRetriever()
        
    def generate_report(self, active_evidence: List[EvidenceRecord], relevant_turns: List[ConversationTurn], protocol_name: str = "SAFE-T") -> str:
        """
        Synthesizes the memory (ledger), context (retrieved turns), and guidelines (protocol)
        into a final report.
        """
        protocol_text = self.protocol_retriever.get_protocol(protocol_name)
        
        evidence_str = "\n".join([f"- {r.concept.value}: {r.evidence_text}" for r in active_evidence])
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
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            return response.text
        except Exception as e:
            return f"Error generating report: {e}"
