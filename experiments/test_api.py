import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
import httpx

load_dotenv()

def run_timeout_tests():
    print("Testing Gemini API Timeouts...")
    try:
        print("Testing timeout=120.0")
        client1 = genai.Client(http_options={'timeout': 120.0})
        response = client1.models.generate_content(model='gemini-1.5-flash', contents='Test')
        print("timeout=120.0 passed!")
    except Exception as e:
        print(f"timeout=120.0 failed: {e}")

    try:
        print("Testing timeout=120000 (int)")
        client2 = genai.Client(http_options={'timeout': 120000})
        response = client2.models.generate_content(model='gemini-3.8-flash', contents='Test')
        print("timeout=120000 passed!")
    except Exception as e:
        print(f"timeout=120000 failed: {e}")

    try:
        print("Testing httpx.Timeout(120.0)")
        client3 = genai.Client(http_options={'timeout': httpx.Timeout(120.0)})
        response = client3.models.generate_content(model='gemini-1.5-flash', contents='Test')
        print("httpx.Timeout passed!")
    except Exception as e:
        print(f"httpx.Timeout failed: {e}")

if __name__ == "__main__":
    run_timeout_tests()
