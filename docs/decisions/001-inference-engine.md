# ADR 001: Inference Engine — Ollama

**Status:** Accepted
**Date:** 2026-09-30
**Context:** TIER-ITS project needs local LLM inference on a 6 GB VRAM laptop GPU (RTX 4050) with degraded cooling, running inside WSL2 with mirrored networking.

## Decision

Use **Ollama** (v0.35.0) as the inference engine, running as a systemd service inside WSL2.

## Options Considered

| Option | Verdict | Reasoning |
|:-------|:--------|:----------|
| **Ollama** ✅ | Chosen | Wraps llama.cpp; native JSON schema enforcement via `format=`; Python API; manages model lifecycle; systemd integration; no meaningful VRAM overhead vs raw llama.cpp |
| **llama.cpp (raw)** | Rejected | More granular control (layer offloading, KV cache tuning) but unnecessary complexity. Ollama exposes the important knobs. No Python-native API without additional wrapping. |
| **vLLM** | Rejected | Pre-allocates large PagedAttention KV cache; designed for 24 GB+ multi-GPU. Will OOM on 6 GB VRAM. Enterprise-grade throughput optimization irrelevant for single-user research. |
| **Cloud APIs (OpenAI, etc.)** | Rejected | Proposal requires response caching for reproducibility; cloud APIs add cost and latency. Also, the proposal's ethics section restricts sending raw user text to external APIs unless dataset agreements allow it. |

## Key Configuration

- **Bind address:** `127.0.0.1:11434` (not `0.0.0.0` — mirrored networking constraint)
- **Flash attention:** enabled (reduces KV cache VRAM by ~30–50%)
- **Max loaded models:** 1 (thermal protection)
- **Parallel requests:** 1 (thermal protection)
- **Default context:** 4096 tokens (VRAM constraint)

## Primary Model

**Qwen3 4B** (Q4_K_M quantization, ~4 GB VRAM) — best balance of capability, structured output adherence, and VRAM headroom for a 6 GB card.

## Consequences

- All LLM calls go through `src/inference/client.py` which wraps the Ollama Python API.
- Structured extraction uses `format=<PydanticModel>.model_json_schema()` — grammar-based, single-pass enforcement.
- Response caching in `src/inference/cache.py` is mandatory for reproducibility and thermal management.
- If a larger model is needed later, we can switch to Qwen3 8B (Q4_K_M, ~5.8 GB) but must reduce `num_ctx` to 4096 or lower.
- Ollama is installed only inside WSL2. Any Windows-side Ollama remnants must be removed to prevent port conflicts.
