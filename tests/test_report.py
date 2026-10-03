import os
import pytest
from src.schemas import EvidenceRecord, ITSConcept, ConversationTurn
from src.report.generator import ReportGenerator

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY is not set")
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
