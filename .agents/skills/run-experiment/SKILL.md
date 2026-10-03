---
name: run-experiment
description: Run a TIER-ITS experiment batch (depth, evidence, correction, or intervention). Use when the user wants to execute an experiment from the experiments/ directory with checkpointing and result persistence. Works on any provider (local CPU, Kaggle, Colab, Lightning AI).
---

# Run Experiment

## Pre-flight

Every experiment run begins with this checklist. Skip nothing.

1. **Python env:** Activate the venv. Locally: `.\ml\Scripts\Activate.ps1`. On remote: `pip install -r requirements.txt`.
2. **LLM backend available:** At least one of:
   - Gemini API: `echo $env:GEMINI_API_KEY` (or `echo $GEMINI_API_KEY` on Linux) is set.
   - Ollama: `curl -s --max-time 5 http://127.0.0.1:11434/` → "Ollama is running".
3. **Benchmark exists:** `ls data/benchmark/` — must contain generated conversation files.
4. **Cache directory writable:** `ls data/cache/`.
5. **Previous checkpoints restored** (if resuming on a new provider): `python scripts/restore_checkpoint.py`.

## Which experiment

| Script | Research Question | What it measures |
|:--|:--|:--|
| `experiments/run_depth.py` | RQ1 + RQ2 | F1 drop as evidence moves deeper; TIER-ITS vs baselines |
| `experiments/run_evidence.py` | RQ3 | Evidence precision and recall — do citations point to correct turns |
| `experiments/run_correction.py` | RQ4a | Does the ledger update when a statement is corrected/contradicted |
| `experiments/run_intervention.py` | RQ4b | Does correcting a ledger concept change the report predictably |

## Execution

1. Run the script with `--resume` to skip completed cases:
   ```bash
   python experiments/run_depth.py --resume --checkpoint-interval 10
   ```
2. Results write to `results/` immediately after each case — crash-safe and provider-agnostic.
3. If the run is interrupted (session timeout, quota exhausted), it resumes from the last completed case.
4. LLM response cache is synced to cloud storage at each checkpoint interval.

## Switching providers mid-experiment

This is the normal workflow. When one provider's quota is exhausted:

1. **Save progress:** `python scripts/upload_checkpoint.py` (syncs results + cache to Google Drive).
2. **On the new provider:**
   ```bash
   git clone https://github.com/you/TIER-ITS.git && cd TIER-ITS
   pip install -r requirements.txt
   python scripts/restore_checkpoint.py
   python experiments/run_depth.py --resume
   ```
3. The experiment picks up exactly where it left off.

## Post-run

1. Check `results/` for completeness — every benchmark case should have a result file.
2. Run `experiments/compare.py` to generate cross-method comparison tables.
3. Run `evaluation/analysis.py` for bootstrap confidence intervals and figures.
4. Figures write to `paper/figures/`.
5. Sync final results: `python scripts/upload_checkpoint.py`.

## If it fails mid-run

1. Check the error:
   - **429 / rate limited** → increase delay between requests, or switch to Ollama on GPU.
   - **Session timeout** → normal. Upload checkpoint, switch provider, resume.
   - **OOM on remote GPU** → reduce `num_ctx` or switch to smaller model.
   - **API key issue** → check `GEMINI_API_KEY` is set and valid.
2. Check `results/` — how many cases completed before the failure.
3. Re-run with `--resume`. It will skip completed cases.
