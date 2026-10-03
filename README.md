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
  - Experiment runner completed.
  - Successfully proved TIER-ITS achieves 100% accuracy, matching Full-Context while scaling cleanly. See [Phase 1 Results](docs/phase1_results.md).
- [ ] **Phase 7: Correction Experiment (RQ2)**
  - *(Next Up)* Test contradiction resolution in the ledger.
- [ ] **Phase 8: Analysis & Paper Writing**

## Tech Stack
- **Python 3.12**
- **LLM Client:** `google-genai` (Gemini API: `gemini-3.8-flash`)
- **Vector DB:** `chromadb`
- **Testing:** `pytest`

## Running Tests
```bash
d:\Projects\TIER-ITS\ml\Scripts\python.exe -m pytest -v -s
```
