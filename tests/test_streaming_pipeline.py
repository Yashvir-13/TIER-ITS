import pytest
from typing import List, Optional
from src.schemas import ConversationTurn, EvidenceRecord, ITSConcept
from src.ledger.store import EvidenceLedger
from src.ledger.assessor import MockContradictionAssessor
from src.inference.pipeline import ClinicalMemoryOrchestrator, StreamResult
from src.inference.tokens import count_tokens_from_response, estimate_tokens

class MockExtractor:
    def __init__(self, step_prompt: int = 0, step_comp: int = 0):
        self.step_prompt = step_prompt
        self.step_comp = step_comp
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def extract(self, turn: ConversationTurn, context_turn: Optional[ConversationTurn] = None) -> Optional[EvidenceRecord]:
        self.total_prompt_tokens += self.step_prompt
        self.total_completion_tokens += self.step_comp
        if "burden" in turn.text.lower():
            return EvidenceRecord(
                concept=ITSConcept.PERCEIVED_BURDENSOMENESS,
                evidence_text=turn.text,
                turn_index=turn.turn_index,
                subject="patient"
            )
        return None

class MockAssessor(MockContradictionAssessor):
    def __init__(self, step_prompt: int = 0, step_comp: int = 0):
        super().__init__()
        self.step_prompt = step_prompt
        self.step_comp = step_comp
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def assess(self, record: EvidenceRecord, turn: ConversationTurn) -> bool:
        self.total_prompt_tokens += self.step_prompt
        self.total_completion_tokens += self.step_comp
        return super().assess(record, turn)

class MockReportGenerator:
    def __init__(self, step_prompt: int = 0, step_comp: int = 0):
        self.step_prompt = step_prompt
        self.step_comp = step_comp
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def generate_report(self, active_evidence, relevant_turns, protocol_name="SAFE-T"):
        self.total_prompt_tokens += self.step_prompt
        self.total_completion_tokens += self.step_comp
        concepts = [e.concept.value for e in active_evidence]
        return f"Risk report based on {protocol_name}: {', '.join(concepts) if concepts else 'None'}"

def test_streaming_orchestrator_sequential_updates():
    """Verifies sequential state updates and non-zero fallback token tracking."""
    orchestrator = ClinicalMemoryOrchestrator()
    orchestrator.extractor = MockExtractor()
    orchestrator.assessor = MockContradictionAssessor()
    orchestrator.ledger = EvidenceLedger(assessor=orchestrator.assessor)
    orchestrator.report_generator = MockReportGenerator()
    
    turns = [
        ConversationTurn(turn_index=0, speaker="therapist", text="How are you?"),
        ConversationTurn(turn_index=1, speaker="patient", text="I feel like a huge burden to my family."),
        ConversationTurn(turn_index=2, speaker="therapist", text="Tell me more about that."),
        ConversationTurn(turn_index=3, speaker="patient", text="Actually, my partner told me today that I am valuable.")
    ]
    
    result = orchestrator.process_stream(turns, protocol_name="SAFE-T")
    
    assert isinstance(result, StreamResult)
    # The initial disclosure was extracted at turn 1
    assert len(result.all_evidence) == 1
    assert result.all_evidence[0].turn_index == 1
    assert result.all_evidence[0].concept == ITSConcept.PERCEIVED_BURDENSOMENESS
    # At turn 3, MockContradictionAssessor saw 'Actually' and invalidated it
    assert result.all_evidence[0].contradicted is True
    assert result.all_evidence[0].contradicted_by_turn == 3
    # Active evidence should now be empty
    assert len(result.active_evidence) == 0
    assert "None" in result.report
    # Verify fallback token accounting is nonzero
    assert result.total_prompt_tokens > 0
    assert result.total_completion_tokens > 0

def test_provider_usage_metadata_extraction():
    """Verifies that count_tokens_from_response accurately extracts provider usage metadata."""
    class FakeUsageMetadata:
        prompt_token_count = 142
        candidates_token_count = 37

    class FakeResponse:
        usage_metadata = FakeUsageMetadata()

    prompt = "Clinical evaluation prompt text"
    text = "Model completion output text"
    p_tok, c_tok = count_tokens_from_response(prompt, text, FakeResponse())
    assert p_tok == 142
    assert c_tok == 37

    # When usage metadata is missing, verify character-based fallback estimation
    p_est, c_est = count_tokens_from_response("A" * 40, "B" * 20, response_obj=None)
    assert p_est == 10
    assert c_est == 5

def test_exact_token_aggregation_across_pipeline():
    """Verifies exact arithmetic aggregation of provider tokens across all pipeline components."""
    orchestrator = ClinicalMemoryOrchestrator()
    # Inject components with known provider token counts per call
    orchestrator.extractor = MockExtractor(step_prompt=150, step_comp=40)
    orchestrator.assessor = MockAssessor(step_prompt=100, step_comp=25)
    orchestrator.ledger = EvidenceLedger(assessor=orchestrator.assessor)
    orchestrator.report_generator = MockReportGenerator(step_prompt=200, step_comp=60)

    turns = [
        ConversationTurn(turn_index=0, speaker="therapist", text="Hello."),
        ConversationTurn(turn_index=1, speaker="patient", text="I am a burden to everyone."),
        ConversationTurn(turn_index=2, speaker="patient", text="Wait, I am reconsidering that thought.")
    ]

    result = orchestrator.process_stream(turns, protocol_name="SAFE-T")
    
    # Assert exact sum: 
    # 2 extractions (300 p, 80 c) + 1 assessor check (100 p, 25 c) + 1 report (200 p, 60 c)
    # = 600 prompt, 165 completion
    assert result.total_prompt_tokens == 600
    assert result.total_completion_tokens == 165

def test_ledger_bounded_active_set_and_compute():
    """Verifies that EvidenceLedger maintains a bounded active set (K <= 10) without scanning history."""
    ledger = EvidenceLedger(max_active_records=10)
    
    # Add 25 records
    for i in range(25):
        rec = EvidenceRecord(
            concept=ITSConcept.THWARTED_BELONGINGNESS,
            evidence_text=f"Loneliness statement {i}",
            turn_index=i * 2 + 1,
            subject="patient"
        )
        ledger.add_evidence(rec)

    # Historical audit log retains all 25 records
    assert len(ledger.get_all_evidence()) == 25
    
    # Active working set is strictly capped at max_active_records (10)
    active = ledger.get_active_evidence()
    assert len(active) == 10
    # The active set should contain only the latest 10 items (indices 15..24)
    assert active[0].turn_index == 15 * 2 + 1
    assert active[-1].turn_index == 24 * 2 + 1
    
    # Earlier items (0..14) are marked as evicted under bounded memory
    evicted = [r for r in ledger.get_all_evidence() if r.contradicted_by_turn == -2]
    assert len(evicted) == 15

def test_streaming_step_by_step_and_generator_ingestion():
    """Verifies live incremental step-by-step ingestion and lazy generator processing."""
    orchestrator = ClinicalMemoryOrchestrator()
    orchestrator.extractor = MockExtractor(step_prompt=150, step_comp=40)
    orchestrator.assessor = MockAssessor(step_prompt=100, step_comp=25)
    orchestrator.ledger = EvidenceLedger(assessor=orchestrator.assessor, max_active_records=10)
    orchestrator.report_generator = MockReportGenerator(step_prompt=200, step_comp=60)

    # 1. Test live incremental step() calls
    turn0 = ConversationTurn(turn_index=0, speaker="therapist", text="Hello, how are you?")
    res0 = orchestrator.step(turn0)
    assert res0 is None
    assert len(orchestrator.ledger.get_active_evidence()) == 0

    turn1 = ConversationTurn(turn_index=1, speaker="patient", text="I feel like such a burden to everyone.")
    res1 = orchestrator.step(turn1)
    assert res1 is not None
    assert res1.concept == ITSConcept.PERCEIVED_BURDENSOMENESS
    assert len(orchestrator.ledger.get_active_evidence()) == 1

    turn2 = ConversationTurn(turn_index=2, speaker="therapist", text="Can you tell me more about that?")
    res2 = orchestrator.step(turn2)
    assert res2 is None

    # Finish session via step API
    res_session = orchestrator.finish_session(protocol_name="SAFE-T")
    assert len(res_session.active_evidence) == 1
    assert "perceived_burdensomeness" in res_session.report

    # 2. Test lazy generator ingestion via process_stream
    orchestrator_gen = ClinicalMemoryOrchestrator()
    orchestrator_gen.extractor = MockExtractor(step_prompt=150, step_comp=40)
    orchestrator_gen.assessor = MockAssessor(step_prompt=100, step_comp=25)
    orchestrator_gen.ledger = EvidenceLedger(assessor=orchestrator_gen.assessor, max_active_records=10)
    orchestrator_gen.report_generator = MockReportGenerator(step_prompt=200, step_comp=60)

    raw_turns = [
        ConversationTurn(turn_index=0, speaker="patient", text="Just regular chat."),
        ConversationTurn(turn_index=1, speaker="patient", text="I am a massive burden."),
        ConversationTurn(turn_index=2, speaker="therapist", text="I hear you.")
    ]
    # Pass a lazy generator rather than a materialized list
    generator_input = (t for t in raw_turns)
    gen_result = orchestrator_gen.process_stream(generator_input, protocol_name="SAFE-T")
    assert len(gen_result.active_evidence) == 1
    assert gen_result.active_evidence[0].concept == ITSConcept.PERCEIVED_BURDENSOMENESS
    assert "perceived_burdensomeness" in gen_result.report

