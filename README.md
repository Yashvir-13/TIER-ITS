# TIER-ITS: Theory-Indexed Evidence Retrieval for Long Mental-Health Conversations

## Project Overview
**TIER-ITS** is a research prototype that tests whether an Intelligent Tutoring System (ITS)-based memory preserves risk evidence better than standard LLM baselines (like Full-Context, Recent-Window, or General-Summary) over the course of extremely long conversations.

**Note:** This is a research prototype. It is not a chatbot, not a clinical tool, and not deployment-ready.

## Motivation (RQ1)
Standard Large Language Models suffer from "context decay" or the "Lost in the Middle" phenomenon when processing long conversations. In high-stakes domains like suicide risk assessment (e.g., C-SSRS, SAFE-T), losing track of a risk factor (like Thwarted Belongingness) mentioned an hour ago can be catastrophic. TIER-ITS seeks to solve this by abstracting the memory into a structured, theory-indexed Evidence Ledger, combined with a Vector Retrieval Pipeline (ChromaDB).

## Current Progress Tracker (8-Week Plan)

- [x] **Phase 1: Foundation Setup**
  - Project scaffolding, virtual environment (`ml/`).
  - Pydantic models for `EvidenceRecord`, `ConversationTurn`, `Ledger`.
  - Defined clinical dictionaries (`GLOSSARY.md`, `ethics-checklist.md`).
- [x] **Phase 2: Benchmark Construction**
  - Generated nuanced synthetic conversational data (Explicit, Implicit, Fragmented).
  - Built `BenchmarkGenerator` to inject targets at controlled depths (0, 20, 50, 100 turns).
- [x] **Phase 3: Extractor & ITS Ledger**
  - Implemented `GeminiExtractor` to convert raw text to Pydantic models.
  - Implemented `EvidenceLedger` to track active vs. contradicted evidence.
  - Refactored Ledger to use a `ContradictionAssessor` seam.
- [x] **Phase 4: Retrieval Pipeline**
  - Integrated `ChromaDB` for `ConversationRetriever`.
  - Created `ProtocolRetriever` for `C-SSRS` and `SAFE-T`.
  - Built `ReportGenerator` to synthesize memory, context, and protocols into a final summary.
- [x] **Phase 5: Baselines Setup**
  - Scaffolded `FullContextBaseline`, `RecentWindowBaseline`, and `SummaryBaseline`.
- [x] **Phase 6: Depth Experiment (RQ1)**
  - Experiment runner completed (160 balanced cases).
  - TIER-ITS achieves F1=1.00 at parity with Full-Context on the synthetic benchmark, while significantly outperforming Recent-Window ($p < .001$). See [Phase 1 Results](docs/phase1_results.md) and [Full Context Analysis](docs/tier_vs_full_context_analysis.md).
- [x] **Phase 7: Correction Experiment (RQ4)**
  - Implemented dynamic belief revision and state machine contradiction invalidation.
  - Generated realistic clinical benchmark with strict speaker alternation (48 cases).
  - Achieved 100% ledger invalidation accuracy and zero false-positive active risk. See [Phase 2 Correction Results](docs/phase2_correction_results.md).
- [ ] **Phase 8: Analysis & Paper Writing**

## Research Scope & Clinical Disclaimers
- **Synthetic Feasibility Study:** All evaluation benchmarks (depth and correction) are synthetic and evaluated using an automated LLM judge. Results demonstrate architectural feasibility, turn-level evidence provenance, and structured state tracking; they do not establish real-world clinical efficacy or replace licensed clinician evaluation.
- **Protocol Summaries:** Bundled protocol files (`data/protocols/safe-t.txt` and `c-ssrs.txt`) provide condensed clinical protocol summaries for prompt grounding rather than exhaustive clinical assessment manuals.
- **Memory Architecture:** TIER-ITS maintains a bounded active clinical working set ($K \le 10$ records) for report generation, while retaining historical transitions in an audit log and dialogue turns in episodic vector storage ($\mathcal{O}(N)$ system storage).
- **Evidence Provenance Scope:** Reported turn-level provenance metrics evaluate exact turn numbers recorded in the structured EvidenceLedger (`tier_evidence_turns`), not inline citations in generated natural language reports.

## Tech Stack
- **Python 3.12**
- **LLM Client:** `google-genai` (Gemini API: `gemini-3.8-flash`)
- **Vector DB:** `chromadb`
- **Testing:** `pytest`

## Running Tests
```bash
d:\Projects\TIER-ITS\ml\Scripts\python.exe -m pytest -v -s
```
