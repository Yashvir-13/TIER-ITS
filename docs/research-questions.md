# TIER-ITS Research Questions (RQs)

**Frozen as of Phase 1**

*   **RQ1 (Depth Retention):** As evidence of Thwarted Belongingness (TB) or Perceived Burdensomeness (PB) recedes deeper into a conversation’s past, at what turn depth do baseline LLM architectures (full-context, recent-window, general-summary) fail to retrieve it for risk assessment?
*   **RQ2 (ITS Ledger Efficacy):** Does maintaining an explicit "ITS Evidence Ledger" preserve F1-score for risk identification at depth=100 equivalently to depth=0, compared to the drop-off experienced by baseline methods?
*   **RQ3 (Evidence Precision):** When a baseline model correctly identifies risk, does it cite the correct conversational turn as evidence, or is it hallucinating the rationale? How does the TIER-ITS ledger compare in evidence precision and recall?
*   **RQ4 (State Correction & Intervention):**
    *   **RQ4a:** If a patient explicitly contradicts a previously stated feeling of PB later in the conversation, does the ITS Evidence Ledger correctly update its state to invalidate the prior evidence?
    *   **RQ4b:** Does manually correcting a misclassified concept in the ITS Ledger predictably and safely alter the final generated risk report, demonstrating system inspectability and clinician override?
