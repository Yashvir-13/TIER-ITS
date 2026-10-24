import os
import pytest
try:
    from google import genai
except ImportError:
    genai = None
from dotenv import load_dotenv

from src.schemas import EvidenceRecord, ITSConcept, ConversationTurn, InvalidationSentinel
from src.ledger.store import EvidenceLedger
from src.ledger.assessor import MockContradictionAssessor, GeminiContradictionAssessor
from tests.conftest import HAS_INTERNET

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

def test_evidence_ledger_manual_override_and_sentinels():
    ledger = EvidenceLedger(max_active_records=5)
    record = EvidenceRecord(
        concept=ITSConcept.PERCEIVED_BURDENSOMENESS,
        evidence_text="I am a burden.",
        turn_index=8,
        subject="patient",
        contradicted=False,
        contradicted_by_turn=None
    )
    ledger.add_evidence(record)
    assert len(ledger.get_active_evidence()) == 1

    # Clinician invalidates the false alarm
    ledger.manual_override(record_turn_index=8, active=False, concept=ITSConcept.PERCEIVED_BURDENSOMENESS)
    assert len(ledger.get_active_evidence()) == 0
    all_recs = ledger.get_all_evidence()
    assert all_recs[0].contradicted is True
    assert all_recs[0].contradicted_by_turn == int(InvalidationSentinel.CLINICIAN_OVERRIDE)

    # Clinician reinstates the signal
    ledger.manual_override(record_turn_index=8, active=True, concept=ITSConcept.PERCEIVED_BURDENSOMENESS)
    assert len(ledger.get_active_evidence()) == 1
    assert all_recs[0].contradicted is False
    assert all_recs[0].contradicted_by_turn is None

@pytest.mark.skipif(genai is None or not os.getenv("GEMINI_API_KEY") or not HAS_INTERNET, reason="google-genai not installed, GEMINI_API_KEY is not set, or internet unreachable")
def test_real_gemini_contradiction():
    client = genai.Client(http_options={'timeout': 120000})
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

@pytest.mark.skipif(genai is None or not os.getenv("GEMINI_API_KEY") or not HAS_INTERNET, reason="google-genai not installed, GEMINI_API_KEY is not set, or internet unreachable")
def test_real_gemini_batch_contradiction():
    client = genai.Client(http_options={'timeout': 120000})
    assessor = GeminiContradictionAssessor(client=client)
    ledger = EvidenceLedger(assessor=assessor)
    
    # Old evidence record at turn 3
    record = EvidenceRecord(
        concept=ITSConcept.PERCEIVED_BURDENSOMENESS,
        evidence_text="I'm just a huge anchor around everyone's neck. They'd be happier without me.",
        turn_index=3,
        subject="patient",
        contradicted=False,
        contradicted_by_turn=None
    )
    ledger.add_evidence(record)
    
    # Subsequent conversational turns
    turns = [
        ConversationTurn(turn_index=4, speaker="therapist", text="That sounds really painful to carry."),
        ConversationTurn(turn_index=5, speaker="patient", text="Yeah, just trying to get through each day."),
        ConversationTurn(turn_index=6, speaker="therapist", text="How did yesterday evening go?"),
        ConversationTurn(turn_index=7, speaker="patient", text="Actually, my partner sat me down and told me how much they love having me around. It made me realize I'm not a burden at all.")
    ]
    
    ledger.check_contradictions_batch(turns)
    
    # Evidence should now be invalidated
    assert len(ledger.get_active_evidence()) == 0
    all_ev = ledger.get_all_evidence()
    assert len(all_ev) == 1
    assert all_ev[0].contradicted is True
    assert all_ev[0].contradicted_by_turn == 7
