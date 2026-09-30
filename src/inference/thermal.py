import subprocess
import time

def get_gpu_temp() -> int:
    """Read current GPU temperature using nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
            capture_output=True, text=True, check=True
        )
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        # Fallback if nvidia-smi fails (e.g. not available in current environment)
        # Should ideally log a warning here.
        return 0

def wait_for_cooldown(max_temp: int = 75, poll_interval: int = 5):
    """Block execution until GPU temperature drops below threshold."""
    while get_gpu_temp() > max_temp:
        print(f"⏳ GPU at {get_gpu_temp()}°C — cooling down to {max_temp}°C...")
        time.sleep(poll_interval)

def thermal_guard(max_temp: int = 75):
    """Decorator that pauses execution before function call if GPU is too hot."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            wait_for_cooldown(max_temp)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
