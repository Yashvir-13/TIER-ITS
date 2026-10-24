import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Any

class LLMResponseCache:
    """
    Persistent key-value cache for LLM API responses.
    Caches completions based on sha256(model_name + prompt + config).
    Provides instant replay of identical inferences, eliminates redundant API calls,
    prevents rate-limit throttling, and guarantees experimental reproducibility.
    """
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_key(self, model: str, prompt: str, **kwargs) -> str:
        payload = f"{model}::{prompt}::{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
        
    def get(self, model: str, prompt: str, **kwargs) -> Optional[str]:
        key = self._get_key(model, prompt, **kwargs)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("response")
            except Exception:
                return None
        return None
        
    def set(self, model: str, prompt: str, response: str, **kwargs):
        key = self._get_key(model, prompt, **kwargs)
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "model": model,
                    "prompt": prompt,
                    "response": response,
                    "extra": kwargs
                }, f, indent=2)
        except Exception:
            pass

# Global shared instance
_global_cache = LLMResponseCache()

def get_cache() -> LLMResponseCache:
    return _global_cache
