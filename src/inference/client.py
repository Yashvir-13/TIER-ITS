from ollama import chat
from typing import List, Dict, Any, Optional
from .cache import cache_key, get_cached, set_cache

# Using a standard function, not decorating directly to allow manual control if needed
def generate_response(
    model: str,
    messages: List[Dict[str, str]],
    format_schema: Optional[Dict[str, Any]] = None,
    temperature: float = 0.0,
    num_ctx: int = 4096,
    use_cache: bool = True
) -> str:
    """
    Generate response from Ollama, using local cache when possible.
    Includes default thermal-safe options (num_ctx=4096).
    """
    options = {"temperature": temperature, "num_ctx": num_ctx}
    
    if use_cache:
        key = cache_key(model, messages, format_schema, options)
        cached_result = get_cached(key)
        if cached_result:
            return cached_result["response"]

    # We do not apply wait_for_cooldown here for every single call because
    # caching means we often don't hit the GPU. We rely on the batch runner
    # to call wait_for_cooldown explicitly when doing heavy loops.
    
    response = chat(
        model=model,
        messages=messages,
        format=format_schema,
        options=options
    )
    
    content = response.message.content
    
    if use_cache:
        set_cache(key, {"response": content})
        
    return content
