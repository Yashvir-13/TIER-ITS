# AGENTS.md

## Project

**TIER-ITS**: Theory-Indexed Evidence Retrieval for Long Mental-Health Conversations.

Research prototype testing whether an ITS-based memory preserves risk evidence better than full-context, recent-window, or general-summary baselines in long conversations. Not a chatbot, not a clinical tool, not deployment-ready. Research only.

## Domain

Read `GLOSSARY.md` before working in this codebase. ITS terms (TB, PB, AC, C-SSRS, SAFE-T) appear throughout schemas, prompts, and test fixtures.

## Environment

- **WSL2** with mirrored networking (`networkingMode=mirrored`). See `.agents/rules/wsl2-networking.md`.
- **Python env**: `source ~/ml/bin/activate`. Never create a new venv. Never install packages outside this environment.
- **Ollama** running as a systemd service at `127.0.0.1:11434`. See `docs/wsl2-ollama-handbook.md` for operations.
- **GPU**: NVIDIA GeForce RTX 4050 Laptop, 6 GB VRAM, CUDA 8.9, degraded cooling. See `.agents/rules/gpu-thermal-safety.md`.

## Key paths

| Path | Purpose |
|:-----|:--------|
| `src/schemas/` | Pydantic models — the contract layer (evidence records, conversations, reports) |
| `src/extractor/` | ITS concept extraction from conversation turns |
| `src/ledger/` | Evidence ledger CRUD, contradiction detection, persistence |
| `src/retrieval/` | ChromaDB-based conversation retrieval + protocol retrieval |
| `src/inference/` | Ollama client wrapper, response cache, thermal guard |
| `src/baselines/` | All comparison methods (target-only, full-context, recent-window, summary, gold) |
| `src/report/` | Report generation from ledger + retrieval |
| `benchmark/` | Benchmark construction, templates, validation |
| `experiments/` | Experiment runners (depth, evidence, correction, intervention) |
| `evaluation/` | Metrics (F1, evidence P/R, calibration), bootstrap CI, figures |
| `data/` | Raw data, processed data, benchmark files, protocol docs, LLM cache |
| `results/` | Experiment outputs (gitignored) |
| `paper/` | Paper drafts and figures |
| `scripts/` | Helper scripts (Ollama setup, thermal monitor, data download) |
| `docs/` | Handbooks and architecture decision records |

## Ethics constraints

- No live participant interaction. Retrospective text and controlled simulations only.
- No method or means details in generated text.
- No clinical effectiveness claims.
- "Insufficient evidence" is an allowed and expected result.
- Examples in the paper must be paraphrased and stripped of identifying details.
