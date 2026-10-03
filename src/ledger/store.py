from typing import List, Optional
from src.schemas import EvidenceRecord, ConversationTurn, ITSConcept
from src.ledger.assessor import ContradictionAssessor

class EvidenceLedger:
    """
    Deep module representing the memory state of the ITS system.
    Hides the complexity of tracking evidence over time and handling contradictions.
    """
    def __init__(self, assessor: Optional[ContradictionAssessor] = None):
        self._records: List[EvidenceRecord] = []
        self.assessor = assessor

    def add_evidence(self, record: EvidenceRecord):
        """
        Adds new evidence to the ledger.
        """
        self._records.append(record)

    def check_for_contradictions(self, turn: ConversationTurn):
        """
        Checks if the new conversational turn contradicts any currently active evidence.
        If it does, marks the old evidence as contradicted.
        """
        active_records = self.get_active_evidence()
        if not active_records or not self.assessor:
            return
            
        for record in active_records:
            if self.assessor.assess(record, turn):
                record.contradicted = True
                record.contradicted_by_turn = turn.turn_index

    def get_active_evidence(self) -> List[EvidenceRecord]:
        """
        Returns all evidence that has not been contradicted.
        """
        return [r for r in self._records if not r.contradicted]
        
    def get_all_evidence(self) -> List[EvidenceRecord]:
        """
        Returns the entire historical ledger, including contradicted items.
        """
        return list(self._records)
