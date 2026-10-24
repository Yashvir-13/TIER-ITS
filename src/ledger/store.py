from typing import List, Optional
from src.schemas import EvidenceRecord, ConversationTurn, ITSConcept, InvalidationSentinel
from src.ledger.assessor import ContradictionAssessor

class EvidenceLedger:
    """
    Two-tier structured memory module for the Interpersonal Theory of Suicide (ITS).
    
    Architecture:
    1. Active Working Set (`self._active_records`):
       - Strictly bounded to `max_active_records` (K <= 10).
       - Provides O(1) bounded per-turn compute and O(1) prompt context for report generation.
       - Direct addition, contradiction checking, and retrieval operate solely on this bounded set.
    2. Archival Audit Log (`self._records`):
       - Append-only linear history (O(M)) maintaining all historical evidence and contradiction
         events (with turn indices and resolution rationale) for retrospective clinical audit.
    """
    def __init__(self, assessor: Optional[ContradictionAssessor] = None, max_active_records: int = 10):
        self._records: List[EvidenceRecord] = []
        self._active_records: List[EvidenceRecord] = []
        self.assessor = assessor
        self.max_active_records = max_active_records

    def add_evidence(self, record: EvidenceRecord):
        """
        Adds new evidence to the ledger, strictly enforcing bounded capacity (max_active_records).
        Appends to the archival log, and maintains the bounded active set in O(1) operations.
        If active count exceeds max_active_records, the oldest active record is pruned.
        """
        self._records.append(record)
        if not record.contradicted:
            self._active_records.append(record)
            if len(self._active_records) > self.max_active_records:
                # Capacity eviction: prune oldest active evidence to maintain O(1) bound
                oldest = self._active_records.pop(0)
                oldest.contradicted = True
                oldest.contradicted_by_turn = int(InvalidationSentinel.CAPACITY_EVICTION)  # -2 designates capacity eviction under bounded memory

    def check_for_contradictions(self, turn: ConversationTurn):
        """
        Evaluates the new conversational turn against currently active evidence in O(K) bounded compute.
        If a contradiction is detected, marks the record as contradicted and prunes it from the active set.
        """
        if not self._active_records or not self.assessor or turn.speaker != "patient":
            return
            
        still_active: List[EvidenceRecord] = []
        for record in self._active_records:
            # A turn can only contradict evidence disclosed prior to it
            if record.turn_index < turn.turn_index and self.assessor.assess(record, turn):
                record.contradicted = True
                record.contradicted_by_turn = turn.turn_index
            else:
                still_active.append(record)
                
        self._active_records = still_active

    def manual_override(self, record_turn_index: int, active: bool, concept: Optional[ITSConcept] = None):
        """
        Clinician-in-the-loop manual override (RQ4b): Allows a clinician to manually
        invalidate a false positive or reinstate a true positive in the ledger.
        """
        for r in self._records:
            if r.turn_index == record_turn_index and (concept is None or r.concept == concept):
                r.contradicted = not active
                if active:
                    r.contradicted_by_turn = None
                else:
                    r.contradicted_by_turn = int(InvalidationSentinel.CLINICIAN_OVERRIDE)  # -1 represents clinician manual override
                    
        # Synchronize bounded active set from audit history
        self._active_records = [r for r in self._records if not r.contradicted][-self.max_active_records:]

    def check_contradictions_batch(self, turns: List[ConversationTurn]):
        """
        Checks all active records against subsequent patient turns in a batch.
        Uses batch_assess if supported by the assessor, otherwise falls back to turn-by-turn check.
        """
        if not self._active_records or not self.assessor:
            return
            
        if hasattr(self.assessor, "batch_assess"):
            resolutions = self.assessor.batch_assess(self._active_records, turns)
            resolved_turn_indices = set()
            for res in resolutions:
                if res.contradicted and res.contradicted_by_turn is not None:
                    resolved_turn_indices.add(res.record_turn_index)
                    for r in self._records:
                        if r.turn_index == res.record_turn_index and not r.contradicted:
                            r.contradicted = True
                            r.contradicted_by_turn = res.contradicted_by_turn
            self._active_records = [r for r in self._active_records if r.turn_index not in resolved_turn_indices and not r.contradicted]
        else:
            for turn in turns:
                if turn.speaker == "patient":
                    self.check_for_contradictions(turn)

    def get_active_evidence(self) -> List[EvidenceRecord]:
        """
        Returns all evidence that is currently active in O(K) bounded compute (K <= max_active_records).
        Does not scan historical records.
        """
        return list(self._active_records)
        
    def get_all_evidence(self) -> List[EvidenceRecord]:
        """
        Returns the entire historical ledger audit trail, including contradicted and evicted items.
        """
        return list(self._records)
