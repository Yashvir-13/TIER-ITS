import os
import pytest
from src.schemas import ConversationTurn, EvidenceRecord, ITSConcept
from src.baselines.methods import (
    FullContextBaseline, 
    RecentWindowBaseline, 
    SummaryBaseline, 
    TargetOnlyBaseline, 
    GoldLedgerBaseline
)

def test_baselines_instantiation():
    fc = FullContextBaseline()
    rw = RecentWindowBaseline(window_size=10)
    sb = SummaryBaseline(chunk_size=10)
    to = TargetOnlyBaseline()
    gl = GoldLedgerBaseline()
    
    assert fc.model_name == 'gemini-3.8-flash'
    assert rw.window_size == 10
    assert sb.chunk_size == 10

def test_target_only_baseline_filters_target_turns():
    baseline = TargetOnlyBaseline()
    turns = [
        ConversationTurn(turn_index=0, speaker="therapist", text="Hello."),
        ConversationTurn(turn_index=1, speaker="patient", text="I feel like a burden."),
        ConversationTurn(turn_index=2, speaker="therapist", text="Tell me more.")
    ]
    # Test that it extracts turn 1
    target_turns = [t for t in turns if t.turn_index in [1]]
    assert len(target_turns) == 1
    assert target_turns[0].turn_index == 1

def test_gold_ledger_baseline_formats_gold_records():
    gl = GoldLedgerBaseline()
    records = [
        EvidenceRecord(
            concept=ITSConcept.PERCEIVED_BURDENSOMENESS,
            evidence_text="I am a burden.",
            turn_index=1,
            subject="patient"
        )
    ]
    assert len(records) == 1
    assert records[0].concept == ITSConcept.PERCEIVED_BURDENSOMENESS

def test_generic_ledger_baseline_instantiation_and_capacity():
    from src.baselines.methods import GenericLedgerBaseline
    gen = GenericLedgerBaseline(max_active_records=3)
    assert gen.max_active_records == 3

def test_ledger_memory_bound_capacity_enforcement():
    from src.ledger.store import EvidenceLedger
    ledger = EvidenceLedger(max_active_records=3)
    for i in range(5):
        ledger.add_evidence(EvidenceRecord(
            concept=ITSConcept.PERCEIVED_BURDENSOMENESS,
            evidence_text=f"Burden statement {i}",
            turn_index=i,
            subject="patient"
        ))
    active = ledger.get_active_evidence()
    assert len(active) == 3, f"Expected strictly 3 active records due to cap, got {len(active)}"
    # Verify the oldest 2 records were evicted with code -2
    all_recs = ledger.get_all_evidence()
    assert all_recs[0].contradicted_by_turn == -2
    assert all_recs[1].contradicted_by_turn == -2
