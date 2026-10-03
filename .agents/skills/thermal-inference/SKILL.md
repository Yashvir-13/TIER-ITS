---
name: thermal-inference
description: Run LLM inference for TIER-ITS experiments. Use when running batch inference jobs on remote GPU providers or locally on CPU. Covers provider setup, response caching, and session management.
---

# LLM Inference — Remote & Local

## The setup

TIER-ITS uses LLM inference for two things: (1) extracting ITS concepts from conversation turns, and (2) generating reports. All inference goes through a unified client that supports multiple backends.

## LLM backends (priority order)

| Backend | When to use | Setup |
|:--------|:-----------|:------|
| **Gemini API** (free tier) | Primary for all work | `GEMINI_API_KEY` env var from Google AI Studio |
| **Ollama** (Windows, CPU) | Local dev/test only | `ollama serve` on Windows, models pulled locally |
| **Remote Ollama** (GPU provider) | Batch experiments on Kaggle/Colab/Lightning | Ollama installed in notebook, GPU-accelerated |

## Before any inference run

1. **Check which backend is active:**
   ```python
   from src.inference.client import get_client
   client = get_client()  # auto-selects based on env vars
   ```
2. **Verify cache directory exists:** `data/cache/` — all LLM responses are cached.
3. **Check API key (Gemini):**
   ```powershell
   echo $env:GEMINI_API_KEY  # should be set
   ```

## Response caching

Every LLM call goes through a deterministic cache keyed on `hash(model, messages, format_schema)`. Same inputs never hit the API twice. This is both a cost measure (Gemini free tier has rate limits) and a reproducibility requirement (proposal §7.1).

Cache lives at `data/cache/`. The cache module is at `src/inference/cache.py`.

## Rate limit handling (Gemini free tier)

The Gemini free tier enforces RPM (requests/min), TPM (tokens/min), and RPD (requests/day) limits. The inference client must:

```python
import time

MAX_RPM = 10  # adjust per actual quota in AI Studio
DELAY = 60 / MAX_RPM + 1  # seconds between requests

for case in cases:
    result = run_case(case)  # checks cache first
    save_result(result)      # persist immediately
    if not result.from_cache:
        time.sleep(DELAY)    # respect rate limit
```

## Running on remote GPU providers

### Kaggle Notebook
```python
# Install Ollama in Kaggle
!curl -fsSL https://ollama.com/install.sh | sh
!ollama serve &  # background
!ollama pull qwen3:4b
# Then run experiments normally — GPU-accelerated
```

### Google Colab (Enhanced via Gemini AI Pro)
```python
# Colab has priority GPU access with Gemini AI Pro subscription
# Option 1: Use Gemini API directly (no local model needed)
# Option 2: Install Ollama for local GPU inference
!curl -fsSL https://ollama.com/install.sh | sh
```

### Lightning AI Studio
```bash
# Persistent workspace — Ollama stays installed between sessions
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:4b
# Activate GPU, run experiments
```

## Checkpoint sync

After each batch of results, sync to Google Drive:

```python
# In experiment runner
if i % CHECKPOINT_INTERVAL == 0:
    sync_to_drive(results_dir="results/", cache_dir="data/cache/")
```

## If rate-limited (429 errors)

1. Check your quota in Google AI Studio → Rate Limits.
2. Increase `DELAY` between requests.
3. Switch to a different backend (Ollama on remote GPU) for the current batch.
4. Resume later — the cache ensures no repeated work.
