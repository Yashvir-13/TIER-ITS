---
name: run-experiment
description: Run a TIER-ITS experiment batch (depth, evidence, correction, or intervention). Use when the user wants to execute an experiment from the experiments/ directory with thermal guards and result persistence.
---

# Run Experiment

## Pre-flight

Every experiment run begins with this checklist. Skip nothing.

1. **Python env:** `source ~/ml/bin/activate`.
2. **Ollama running:** `curl -s --max-time 5 http://127.0.0.1:11434/` → "Ollama is running".
3. **GPU temp below 70°C:** `nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader`.
4. **Benchmark exists:** `ls data/benchmark/` — must contain generated conversation files.
5. **Model pulled:** `ollama list | grep qwen3:4b`.
6. **Cache directory writable:** `ls data/cache/`.

## Which experiment

| Script | Research Question | What it measures |
|:--|:--|:--|
| `experiments/run_depth.py` | RQ1 + RQ2 | F1 drop as evidence moves deeper; TIER-ITS vs baselines |
| `experiments/run_evidence.py` | RQ3 | Evidence precision and recall — do citations point to correct turns |
| `experiments/run_correction.py` | RQ4a | Does the ledger update when a statement is corrected/contradicted |
| `experiments/run_intervention.py` | RQ4b | Does correcting a ledger concept change the report predictably |

## Execution

1. Run the script. Thermal guards are built into the runner (batch-with-cooldown).
2. Results write to `results/` immediately after each case — crash-safe.
3. If the run is interrupted, it resumes from the last completed case (the runner checks `results/` for existing output).
4. Monitor GPU in a second terminal: `watch -n 1 nvidia-smi`.

## Post-run

1. Check `results/` for completeness — every benchmark case should have a result file.
2. Run `experiments/compare.py` to generate cross-method comparison tables.
3. Run `evaluation/analysis.py` for bootstrap confidence intervals and figures.
4. Figures write to `paper/figures/`.

## If it crashes mid-run

1. Check GPU temp — was it thermal? If so, lower `MAX_TEMP` threshold or `BATCH_SIZE`.
2. Check `results/` — how many cases completed before the crash.
3. Re-run the same script. It will skip completed cases and resume.
4. If the crash is OOM, reduce `num_ctx` in the Ollama call or switch to a smaller model.
