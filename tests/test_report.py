import os
import pytest
try:
    from google import genai
except ImportError:
    genai = None

from src.schemas import EvidenceRecord, ITSConcept, ConversationTurn
from src.report.generator import ReportGenerator
from tests.conftest import HAS_INTERNET

@pytest.mark.skipif(genai is None or not os.getenv("GEMINI_API_KEY") or not HAS_INTERNET, reason="google-genai not installed, GEMINI_API_KEY is not set, or internet unreachable")
def test_report_generator_creates_clinical_summary():
    generator = ReportGenerator()
    
    active_evidence = [
        EvidenceRecord(
            concept=ITSConcept.THWARTED_BELONGINGNESS,
            evidence_text="I just feel completely disconnected from everyone. No one understands.",
            turn_index=10,
            subject="patient"
        )
    ]
    
    relevant_turns = [
        ConversationTurn(turn_index=9, speaker="therapist", text="How have you been feeling with your family lately?"),
        ConversationTurn(turn_index=10, speaker="patient", text="I just feel completely disconnected from everyone. No one understands.")
    ]
    
    report = generator.generate_report(active_evidence, relevant_turns, protocol_name="C-SSRS")
    
    assert report is not None
    assert len(report) > 10
    # The report should mention isolation/belongingness or the protocol context
    assert "risk" in report.lower() or "isolation" in report.lower() or "belongingness" in report.lower() or "c-ssrs" in report.lower()
