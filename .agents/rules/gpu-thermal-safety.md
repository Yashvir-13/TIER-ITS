# GPU Thermal Safety

This machine has a 6 GB RTX 4050 Laptop GPU with degraded cooling.

- **Check GPU temperature** before any inference-heavy operation: `nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader`.
- **Never set `num_ctx` above 8192** for any Ollama model. 4096 is the default and preferred value.
- **Use response caching** (`src/inference/cache.py`) for all LLM calls. Same inputs must never hit the GPU twice.
- **Batch inference** in groups of 10 with `wait_for_cooldown(max_temp=78)` between batches.
- **Ollama is configured** with `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1` via systemd override at `/etc/systemd/system/ollama.service.d/environment.conf`.
- **If OOM occurs**: reduce `num_ctx` first, then try a smaller model, then reduce `num_predict`.
