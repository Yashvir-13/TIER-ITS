import time
from typing import Callable, TypeVar, Any

T = TypeVar('T')

def with_retry(func: Callable[[], T], max_retries: int = 10, wait_seconds: int = 10, error_msg: str = "Network error") -> T:
    """
    Executes a function with a retry loop, sleeping between attempts.
    
    Args:
        func: The zero-argument function to execute.
        max_retries: Maximum number of attempts.
        wait_seconds: Seconds to wait between attempts.
        error_msg: Prefix for the error message printed on failure.
        
    Returns:
        The result of the function if successful.
        
    Raises:
        Exception: The last exception encountered if all retries fail.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"{error_msg} failed after {max_retries} attempts: {e}")
                raise e
            print(f"{error_msg} (attempt {attempt+1}/{max_retries}): {e}. Waiting {wait_seconds}s...")
            time.sleep(wait_seconds)
