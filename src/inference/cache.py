import hashlib
import json
import pathlib
from typing import Optional, Dict, Any, List

CACHE_DIR = pathlib.Path("data/cache")

def cache_key(model: str, messages: List[Dict[str, str]], format_schema: Optional[Dict[str, Any]] = None, options: Optional[Dict[str, Any]] = None) -> str:
    """Generate a deterministic hash key for LLM inputs."""
    blob = json.dumps({
        "model": model,
        "messages": messages,
        "format": format_schema,
        "options": options
    }, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()

def get_cached(key: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached response if it exists."""
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None

def set_cache(key: str, response: Dict[str, Any]) -> None:
    """Save response to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.json"
    path.write_text(json.dumps(response, indent=2))
