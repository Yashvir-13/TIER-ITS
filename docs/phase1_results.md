# TIER-ITS: Phase 1 Depth Experiment Conclusions & Literature Comparison

## 1. Experimental Results Summary

The completion of the depth experiment (56 simulated clinical cases) allows us to definitively answer the first two research questions (RQ1 and RQ2).

### Overall Accuracy
| Architecture | Overall Detection Accuracy |
|:---|:---|
| **Full Context** | 100.0% |
| **Recent Window (N=10)** | 25.0% |
| **TIER-ITS** | **100.0%** |

### Accuracy by Conversational Depth
| Depth (turns since evidence) | Full Context | Recent Window | TIER-ITS |
|:---|:---|:---|:---|
| **0** (Immediate) | 100% | 100% | 100% |
| **20** | 100% | 0% | 100% |
| **50** | 100% | 0% | 100% |
| **100** | 100% | 0% | 100% |

### Accuracy by Clinical Nuance
| Nuance | Full Context | Recent Window | TIER-ITS |
|:---|:---|:---|:---|
| **Explicit** (Direct statements) | 100% | 25% | 100% |
| **Implicit** (Indirect statements) | 100% | 25% | 100% |
| **Fragmented** (Across multiple turns) | 100% | 25% | 100% |

---

## 2. Answering the Research Questions

**RQ1 (Depth Retention):** *At what turn depth do baseline LLM architectures fail to retrieve risk evidence?*
*   **Recent Window** fails immediately once the evidence passes outside the fixed N=10 window (Depth ≥ 20 yields 0% recall). This confirms that simply summarizing recent history is dangerously lossy for clinical risk factors stated early in a session.
*   **Full Context** maintains perfect recall up to Depth 100. Our benchmark (106 turns max) did not exceed the operational limits of Gemini's context window.

**RQ2 (ITS Ledger Efficacy):** *Does maintaining an explicit "ITS Evidence Ledger" preserve F1-score for risk identification at depth=100?*
*   **Yes.** TIER-ITS flawlessly matches the Full Context baseline (100% accuracy) at all depths and across all nuance types. The explicit memory mechanism prevents any evidence decay.

---

## 3. Comparison with Existing Literature

How does TIER-ITS sit within the current state of AI research?

### A. vs. Full-Context Prompting ("Lost in the Middle")
Our Full Context baseline scored 100% on the single-session benchmark. Does this mean TIER-ITS is unnecessary? **No.** 
*   **The Literature:** The seminal paper *"Lost in the Middle: How Language Models Use Long Contexts"* (Liu et al., 2023) proved that as context windows grow (e.g., >10k tokens), LLMs suffer severe degradation in retrieving facts hidden in the middle of the prompt.
*   **Architectural Trade-Off:** While Full Context performs at parity ($F1=1.00$) on our 106-turn single-session synthetic benchmark, real-world psychiatric care spans multiple sessions and thousands of turns. A purely in-context approach incurs growing latency and potential degradation over long horizons. TIER-ITS maintains a **bounded active working set ($K \le 10$ records)** for report synthesis, preventing prompt-length explosion, while retaining past records in an append-only audit ledger and episodic conversation retriever. Note that while the active risk working set is bounded, total system storage scales linearly ($\mathcal{O}(N)$) with conversation history due to the vector retrieval index and historical audit log.

### B. vs. Conversational AI Memory (MemGPT)
*   **The Literature:** *"MemGPT: Towards LLMs as Operating Systems"* (Packer et al., 2023) introduced hierarchical memory for LLMs, allowing them to page information between a "main context" and an "external database" via function calls.
*   **Domain-Specific Structuring:** MemGPT is a general-purpose memory manager with no semantic understanding of clinical theory. TIER-ITS enforces a **domain-specific ontology** (The Interpersonal Theory of Suicide). By mapping conversation turns into explicit schemas (Thwarted Belongingness, Acquired Capability), TIER-ITS guarantees that critical clinical safety evidence is explicitly tracked and auditable rather than relying on heuristic paging. 

### C. vs. Retrieval-Augmented Generation (RAG)
*   **The Literature:** Traditional RAG embeds text into a vector database and retrieves chunks based on semantic similarity to a query.
*   **Capturing Longitudinal Nuance:** Our results show TIER-ITS achieves 100% accuracy on **Fragmented** and **Implicit** evidence. Standard RAG can struggle with fragmented conversations (where pronouns and context are split across multiple turns) because isolated text chunks lose semantic meaning. Because TIER-ITS evaluates turns sequentially and maintains structured records, it captures fragmented risk that vector similarity queries alone might miss.

---

## 4. Final Conclusions & Research Scope

**What TIER-ITS provides:**
1. **Bounded Working State:** It maintains a bounded active clinical state ($K \le 10$ active records) for report generation, matching Full Context accuracy on the synthetic benchmark without prompt ballooning.
2. **Clinical Grounding:** It anchors AI memory explicitly in established clinical psychology (SAFE-T / ITS) rather than unstructured free-form context.
3. **Inspectability & Provenance:** The ITS Ledger provides an auditable trail of *why* the AI tracks a risk factor, citing specific conversational turn indices.

**Scope, Limitations, and Future Work:**
1. **Synthetic & LLM-Judged Evaluation:** All current results are derived from a controlled synthetic dialogue benchmark evaluated by an LLM judge. They demonstrate structural and computational feasibility, but do not establish real-world clinical effectiveness or replace human clinical trials.
2. **Clinical Protocol Summary:** Bundled protocol files (e.g., SAFE-T) provide condensed triage summaries to ground prompt context rather than exhaustive clinical manuals.
3. **Contradiction Resolution:** Phase 2 (Correction Experiment) evaluates dynamic belief revision when patients explicitly resolve or contextualize past disclosures.
4. **Attribution Scope:** Reported turn attribution metrics evaluate the exact turn indices recorded in the structured EvidenceLedger (`tier_evidence_turns`), not inline citations in generated natural language reports.
