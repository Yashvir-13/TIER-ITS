"""
Token estimation and accounting utilities for LLM inference tracking.
"""
from typing import Optional, Any, Tuple

def estimate_tokens(text: Optional[str]) -> int:
    """
    Estimates token count for a text string using the standard ~4 chars/token heuristic.
    Ensures a minimum of 1 token for non-empty text.
    """
    if not text or not text.strip():
        return 0
    return max(1, (len(text) + 3) // 4)

def count_tokens_from_response(
    prompt: str, 
    response_text: str, 
    response_obj: Optional[Any] = None
) -> Tuple[int, int]:
    """
    Extracts prompt and completion tokens from LLM response usage metadata if present,
    falling back to deterministic character-based token estimation.
    
    Returns:
        (prompt_tokens, completion_tokens)
    """
    prompt_tokens = 0
    completion_tokens = 0
    
    if response_obj and hasattr(response_obj, "usage_metadata") and response_obj.usage_metadata:
        um = response_obj.usage_metadata
        prompt_tokens = getattr(um, "prompt_token_count", 0) or 0
        completion_tokens = getattr(um, "candidates_token_count", 0) or 0
        
    if prompt_tokens <= 0:
        prompt_tokens = estimate_tokens(prompt)
    if completion_tokens <= 0:
        completion_tokens = estimate_tokens(response_text)
        
    return prompt_tokens, completion_tokens
