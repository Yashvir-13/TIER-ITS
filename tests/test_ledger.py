import os
import pytest
from google import genai
from dotenv import load_dotenv

from src.schemas import EvidenceRecord, ITSConcept, ConversationTurn
from src.ledger.store import EvidenceLedger
from src.ledger.assessor import MockContradictionAssessor, GeminiContradictionAssessor

load_dotenv()

def test_evidence_ledger_tracks_active_evidence():
    ledger = EvidenceLedger()
    
    # Add a piece of evidence
    record1 = EvidenceRecord(
        concept=ITSConcept.THWARTED_BELONGINGNESS,
        evidence_text="I feel totally alone.",
        turn_index=2,
        subject="patient",
        contradicted=False,
        contradicted_by_turn=None
    )
    
    ledger.add_evidence(record1)
    
    active = ledger.get_active_evidence()
    assert len(active) == 1
    assert active[0].concept == ITSConcept.THWARTED_BELONGINGNESS

def test_evidence_ledger_handles_contradiction_with_mock():
    assessor = MockContradictionAssessor()
    ledger = EvidenceLedger(assessor=assessor)
    
    # Old evidence
    record1 = EvidenceRecord(
        concept=ITSConcept.PERCEIVED_BURDENSOMENESS,
        evidence_text="I am a massive burden to everyone.",
        turn_index=5,
        subject="patient",
        contradicted=False,
        contradicted_by_turn=None
    )
    ledger.add_evidence(record1)
    
    # New turn that contradicts the old evidence
    turn = ConversationTurn(
        turn_index=15,
        speaker="patient",
        text="Actually, my family needs me. I am valuable to them."
    )
    
    ledger.check_for_contradictions(turn)
    
    assert len(ledger.get_active_evidence()) == 0
    assert len(ledger.get_all_evidence()) == 1
    
    all_ev = ledger.get_all_evidence()
    assert all_ev[0].contradicted is True
    assert all_ev[0].contradicted_by_turn == 15

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY is not set")
def test_real_gemini_contradiction():
    client = genai.Client()
    assessor = GeminiContradictionAssessor(client=client)
    ledger = EvidenceLedger(assessor=assessor)
    
    # Old evidence
    record1 = EvidenceRecord(
        concept=ITSConcept.PERCEIVED_BURDENSOMENESS,
        evidence_text="I am a massive burden to everyone. They'd be better off without me.",
        turn_index=5,
        subject="patient",
        contradicted=False,
        contradicted_by_turn=None
    )
    ledger.add_evidence(record1)
    
    # New turn that contradicts the old evidence
    turn = ConversationTurn(
        turn_index=15,
        speaker="patient",
        text="Actually, I had a good talk with my daughter. She made me realize how much they need me around."
    )
    
    ledger.check_for_contradictions(turn)
    
    assert len(ledger.get_active_evidence()) == 0
    
    # Test a turn that does NOT contradict
    turn_no_contradict = ConversationTurn(
        turn_index=16,
        speaker="patient",
        text="I still feel tired all the time, though."
    )
    
    # Add another record so we can test non-contradiction
    record2 = EvidenceRecord(
        concept=ITSConcept.THWARTED_BELONGINGNESS,
        evidence_text="I feel totally alone.",
        turn_index=10,
        subject="patient"
    )
    ledger.add_evidence(record2)
    
    ledger.check_for_contradictions(turn_no_contradict)
    
    # Record 2 should still be active
    assert len(ledger.get_active_evidence()) == 1
    assert ledger.get_active_evidence()[0].concept == ITSConcept.THWARTED_BELONGINGNESS
