import subprocess
import time
import sys

def main():
    while True:
        print("Starting run_depth.py...")
        # Start the process
        process = subprocess.Popen(
            [sys.executable, "experiments/run_depth.py"],
            env={"PYTHONPATH": ".", "PYTHONUNBUFFERED": "1", **os.environ} if "os" in sys.modules else None
        )
        
        # We need os.environ, so let's just do it simpler
        pass

# let's write a proper watchdog
