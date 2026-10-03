# AGENTS.md

## Project

**TIER-ITS**: Theory-Indexed Evidence Retrieval for Long Mental-Health Conversations.

Research prototype testing whether an ITS-based memory preserves risk evidence better than full-context, recent-window, or general-summary baselines in long conversations. Not a chatbot, not a clinical tool, not deployment-ready. Research only.

## Domain

Read `GLOSSARY.md` before working in this codebase. ITS terms (TB, PB, AC, C-SSRS, SAFE-T) appear throughout schemas, prompts, and test fixtures.

## Environment

- **Windows native** (Python 3.12.4). No WSL2.
- **Python venv**: `d:\Projects\TIER-ITS\ml\`. Activate with `.\ml\Scripts\Activate.ps1` (PowerShell) or `ml\Scripts\activate.bat` (cmd). Never create a new venv. Never install packages outside this environment.
- **LLM inference**: Gemini API (free tier via Google AI Studio) as primary LLM. Ollama on Windows as optional local fallback for CPU-only dev/test. See `docs/llm-inference.md`.
- **GPU**: No local GPU. All GPU-intensive work runs on remote providers (Kaggle, Colab, Lightning AI). See `docs/gpu-strategy.md`.
- **Subscriptions**: Gemini AI Pro plan ($10/mo GCP credits, enhanced Colab access, Gemini API). GitHub Student Developer Pack ($100 Azure credits, Copilot, JetBrains, Camber GPU hours).

## Key paths

| Path | Purpose |
|:-----|:--------|
| `src/schemas/` | Pydantic models — the contract layer (evidence records, conversations, reports) |
| `src/extractor/` | ITS concept extraction from conversation turns |
| `src/ledger/` | Evidence ledger CRUD, contradiction detection, persistence |
| `src/retrieval/` | ChromaDB-based conversation retrieval + protocol retrieval |
| `src/inference/` | LLM client wrapper (Gemini/Ollama), response cache |
| `src/baselines/` | All comparison methods (target-only, full-context, recent-window, summary, gold) |
| `src/report/` | Report generation from ledger + retrieval |
| `benchmark/` | Benchmark construction, templates, validation |
| `experiments/` | Experiment runners (depth, evidence, correction, intervention) |
| `evaluation/` | Metrics (F1, evidence P/R, calibration), bootstrap CI, figures |
| `data/` | Raw data, processed data, benchmark files, protocol docs, LLM cache |
| `results/` | Experiment outputs (gitignored) |
| `paper/` | Paper drafts and figures |
| `scripts/` | Helper scripts (data download, checkpoint sync, provider setup) |
| `docs/` | Handbooks, architecture decision records, GPU strategy |

## GPU provider rotation

All GPU work runs on free remote providers. Code must be provider-agnostic.

| Priority | Provider | Free Tier | Notes |
|:---------|:---------|:----------|:------|
| 1 | Kaggle | 30 hrs/wk (P100 or T4×2) | Most predictable quota |
| 2 | Google Colab | Enhanced access via Gemini AI Pro | Priority GPU, compute units included |
| 3 | Lightning AI | 80 hrs free + academic discount | Best IDE, persistent workspace |
| 4 | SageMaker Studio Lab | ~4 hrs GPU/day | Daily drip, 15GB persistent |
| 5 | Camber (GitHub Student) | 5 GPU hrs/mo | Small but free |

## Checkpointing contract

Every experiment runner must:
1. Save results per-case to `results/` immediately after each case completes.
2. Skip already-completed cases on re-run (resume from checkpoint).
3. Sync LLM response cache to Google Drive periodically.
4. Work identically whether run locally (CPU) or on any remote GPU provider.

## Ethics constraints

- No live participant interaction. Retrospective text and controlled simulations only.
- No method or means details in generated text.
- No clinical effectiveness claims.
- "Insufficient evidence" is an allowed and expected result.
- Examples in the paper must be paraphrased and stripped of identifying details.
