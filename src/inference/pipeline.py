from typing import List, Optional, Iterable, Iterator
from dotenv import load_dotenv
load_dotenv()
try:
    from google import genai
except ImportError:
    genai = None

from src.schemas import ConversationTurn, EvidenceRecord
from src.extractor.gemini import GeminiExtractor
from src.ledger.store import EvidenceLedger
from src.ledger.assessor import GeminiContradictionAssessor
from src.retrieval.conversation import ConversationRetriever
from src.report.generator import ReportGenerator

from pydantic import BaseModel, Field

class StreamResult(BaseModel):
    report: str
    active_evidence: List[EvidenceRecord] = Field(default_factory=list)
    all_evidence: List[EvidenceRecord] = Field(default_factory=list)
    retrieved_turns: List[ConversationTurn] = Field(default_factory=list)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

class ClinicalMemoryOrchestrator:
    """
    Coordinates the entire TIER-ITS pipeline: Extraction -> Ledger -> Retrieval -> Reporting.
    Implements true online streaming execution: each turn is processed sequentially,
    maintaining a bounded active clinical working set (K <= max_active_records, default 10)
    for report generation, while persisting historical records in the ledger for compliance
    audit trails and storing conversation turns in vector retrieval for contextual grounding.
    """
    def __init__(self, client: Optional[object] = None, max_active_records: int = 10):
        if client is not None:
            self.client = client
        elif genai is not None:
            try:
                self.client = genai.Client(http_options={'timeout': 120000})
            except Exception:
                self.client = None
        else:
            self.client = None
            
        self.extractor = GeminiExtractor(api_key=self.client.api_key if self.client and hasattr(self.client, 'api_key') else None)
        self.assessor = GeminiContradictionAssessor(client=self.client)
        self.ledger = EvidenceLedger(assessor=self.assessor, max_active_records=max_active_records)
        self.retriever = ConversationRetriever(in_memory=True)
        self.report_generator = ReportGenerator(client=self.client)

        # Streaming session state for incremental step-by-step ingestion
        self._last_turn: Optional[ConversationTurn] = None
        self._stream_local_prompt_tokens: int = 0
        self._stream_local_completion_tokens: int = 0
        self._stream_init_p_tokens: int = 0
        self._stream_init_c_tokens: int = 0
        self._stream_active: bool = False

    def reset_stream_session(self):
        """
        Resets incremental streaming state and snapshots baseline component token counts.
        """
        self._last_turn = None
        self._stream_local_prompt_tokens = 0
        self._stream_local_completion_tokens = 0
        self._stream_init_p_tokens = (
            getattr(self.extractor, "total_prompt_tokens", 0) +
            getattr(self.assessor, "total_prompt_tokens", 0) +
            getattr(self.report_generator, "total_prompt_tokens", 0)
        )
        self._stream_init_c_tokens = (
            getattr(self.extractor, "total_completion_tokens", 0) +
            getattr(self.assessor, "total_completion_tokens", 0) +
            getattr(self.report_generator, "total_completion_tokens", 0)
        )
        self._stream_active = True

    def step(self, turn: ConversationTurn) -> Optional[EvidenceRecord]:
        """
        Incremental online streaming step for a single conversation turn.
        Demonstrates live, turn-by-turn ingestion without requiring a pre-materialized list.

        At turn t:
          1. If patient: extracts ITS concepts using a local (t-1, t) context window.
          2. If evidence found: updates the ledger with capacity bounds.
          3. Evaluates if turn t contradicts prior active evidence in the ledger.
          4. Stores turn in conversation retriever.
        Returns the extracted EvidenceRecord if new risk was identified, else None.
        """
        from src.inference.tokens import estimate_tokens

        if not self._stream_active:
            self.reset_stream_session()

        record: Optional[EvidenceRecord] = None
        if turn.speaker == "patient":
            # 1. Local context extraction (bounded context window)
            record = self.extractor.extract(turn, context_turn=self._last_turn)
            if record:
                self.ledger.add_evidence(record)
                self._stream_local_completion_tokens += estimate_tokens(record.evidence_text) + 20
            self._stream_local_prompt_tokens += estimate_tokens(turn.text + (self._last_turn.text if self._last_turn else "")) + 120

            # 2. Sequential contradiction resolution against active records
            active_before = len(self.ledger.get_active_evidence())
            self.ledger.check_for_contradictions(turn)
            if active_before > 0:
                self._stream_local_prompt_tokens += active_before * (estimate_tokens(turn.text) + 80)
                self._stream_local_completion_tokens += active_before * 15

        # 3. Add turn to retriever
        self.retriever.add_turns([turn])
        self._last_turn = turn

        return record

    def finish_session(self, protocol_name: str = "SAFE-T") -> StreamResult:
        """
        Concludes a streaming session:
          1. Retrieves relevant turns around active concepts from the retriever.
          2. Synthesizes final clinical report using active evidence and protocol summary.
          3. Tallies exact or estimated tokens consumed during the session.
        """
        from src.inference.tokens import estimate_tokens

        active_evidence = self.ledger.get_active_evidence()
        all_evidence = self.ledger.get_all_evidence()

        # Retrieve context around active concepts (or general triage query)
        query_str = " ".join([e.concept.value for e in active_evidence]) if active_evidence else "suicide risk factors"
        relevant_turns = self.retriever.retrieve_relevant_turns(query_str, top_k=3)

        # Generate final report
        report = self.report_generator.generate_report(active_evidence, relevant_turns, protocol_name)

        context_str = " ".join([t.text for t in relevant_turns])
        evidence_str = " ".join([e.evidence_text for e in active_evidence])
        self._stream_local_prompt_tokens += estimate_tokens(context_str + evidence_str + protocol_name) + 200
        self._stream_local_completion_tokens += estimate_tokens(report)

        # Calculate incremental token counts from components
        comp_p_tokens = (
            getattr(self.extractor, "total_prompt_tokens", 0) +
            getattr(self.assessor, "total_prompt_tokens", 0) +
            getattr(self.report_generator, "total_prompt_tokens", 0)
        ) - self._stream_init_p_tokens
        comp_c_tokens = (
            getattr(self.extractor, "total_completion_tokens", 0) +
            getattr(self.assessor, "total_completion_tokens", 0) +
            getattr(self.report_generator, "total_completion_tokens", 0)
        ) - self._stream_init_c_tokens

        final_prompt_tokens = comp_p_tokens if comp_p_tokens > 0 else self._stream_local_prompt_tokens
        final_completion_tokens = comp_c_tokens if comp_c_tokens > 0 else self._stream_local_completion_tokens

        # Reset streaming session flags
        self._stream_active = False
        self._last_turn = None

        return StreamResult(
            report=report,
            active_evidence=active_evidence,
            all_evidence=all_evidence,
            retrieved_turns=relevant_turns,
            total_prompt_tokens=final_prompt_tokens,
            total_completion_tokens=final_completion_tokens
        )

    def process_stream(self, turns: Iterable[ConversationTurn], protocol_name: str = "SAFE-T") -> StreamResult:
        """
        True online streaming execution accepting any iterable or generator of ConversationTurn.
        Processes turns sequentially turn-by-turn via self.step(), then concludes session via self.finish_session().
        """
        self.reset_stream_session()
        for turn in turns:
            self.step(turn)
        return self.finish_session(protocol_name=protocol_name)

    def process_session(self, turns: Iterable[ConversationTurn], protocol_name: str = "SAFE-T") -> str:
        """
        Processes a session using the online streaming pipeline and returns the generated report.
        """
        result = self.process_stream(turns, protocol_name=protocol_name)
        return result.report

    def process_session_batch(self, turns: List[ConversationTurn], protocol_name: str = "SAFE-T") -> str:
        """
        Legacy batch execution (for testing and offline acceleration).
        """
        extracted_records = self.extractor.batch_extract(turns)
        for record in extracted_records:
            self.ledger.add_evidence(record)
        self.ledger.check_contradictions_batch(turns)
        self.retriever.add_turns(turns)
        active_evidence = self.ledger.get_active_evidence()
        query_str = " ".join([e.concept.value for e in active_evidence]) if active_evidence else "suicide risk factors"
        relevant_turns = self.retriever.retrieve_relevant_turns(query_str, top_k=3)
        return self.report_generator.generate_report(active_evidence, relevant_turns, protocol_name)

