---
name: thermal-inference
description: Run LLM inference on a thermally-constrained GPU. Use when the hardware has limited VRAM, degraded cooling, or when running long batch inference jobs that risk thermal throttling.
---

# Thermal-Safe Inference

## The constraint

LLM inference on laptop GPUs with degraded cooling risks: thermal throttling → performance collapse → OOM → crash → lost progress. The mitigation is threefold: **limit power**, **cache responses**, **batch with cooldown**.

## Before any inference run

1. **Check GPU state:**
   ```bash
   nvidia-smi --query-gpu=temperature.gpu,power.draw,memory.used --format=csv,noheader
   ```
2. **Set power limit** (if hardware allows): `sudo nvidia-smi -pl <watts>`. On laptops this may be BIOS-locked; use performance profiles instead (e.g., Fn+Q → "Quiet").
3. **Verify Ollama config** includes: `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`. These are set in `/etc/systemd/system/ollama.service.d/environment.conf`.

## Response caching

Every LLM call goes through a deterministic cache keyed on `hash(model, messages, format_schema)`. Same inputs never hit the GPU twice. This is both a thermal measure and a reproducibility requirement (proposal §7.1).

Cache lives at `data/cache/`. The cache module is at `src/inference/cache.py`.

## Batch with cooldown

For experiment runs (weeks 6–7), process cases in batches of 10 with a thermal guard between batches:

```python
BATCH_SIZE = 10
MAX_TEMP = 78  # Celsius

for i, case in enumerate(cases):
    if i % BATCH_SIZE == 0 and i > 0:
        wait_for_cooldown(MAX_TEMP)
    result = run_case(case)
    save_result(result)  # persist immediately — crash-safe
```

The `wait_for_cooldown` function polls `nvidia-smi` every 5 seconds and blocks until the GPU drops below threshold.

## VRAM budget (6 GB total)

| Component | Budget |
|:--|:--|
| Model weights (Q4_K_M, 4B params) | ~4.0 GB |
| KV cache (4096 context) | ~0.5–1.0 GB |
| Runtime overhead | ~0.5 GB |
| **Headroom** | ~0.5 GB |

- Never exceed `num_ctx: 8192`. Default is 4096.
- Process conversations **turn-by-turn**, not all-at-once.
- If OOM occurs: reduce `num_ctx`, switch to a smaller model, or reduce `num_predict`.

## Monitoring during long runs

Keep a monitoring terminal open:

```bash
watch -n 1 nvidia-smi --query-gpu=temperature.gpu,power.draw,utilization.gpu,memory.used --format=csv,noheader
```
