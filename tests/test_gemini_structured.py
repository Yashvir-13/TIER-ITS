import os
import json
import pytest
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

from src.schemas import EvidenceRecord, ITSConcept

# To run this test:
# 1. Set GEMINI_API_KEY in your environment (.env)
# 2. Run: pytest tests/test_gemini_structured.py -v

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY is not set")
def test_gemini_structured_extraction():
    """Test that Gemini can extract ITS concepts and return them strictly matching the Pydantic schema."""
    
    # Initialize the Gemini GenAI client
    client = genai.Client()
    
    # Example patient turn exhibiting Thwarted Belongingness
    conversation_turn = "Honestly, I just feel like I'm completely alone in this world. Nobody understands me, and I don't fit in anywhere. It's like I'm invisible to my own family."
    
    prompt = f"""
    You are an expert clinical psychologist analyzing a conversation for signs of the Interpersonal Theory of Suicide (ITS).
    
    Analyze the following conversational turn:
    "{conversation_turn}"
    
    Extract the most prominent ITS concept present in this text.
    Return the result strictly matching the provided JSON schema.
    """
    
    # Call the API using structured output (response_schema)
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EvidenceRecord,
            temperature=0.0,
        ),
    )
    
    # Parse the response back into our Pydantic model
    try:
        # The SDK returns the text content which should be valid JSON
        record_data = json.loads(response.text)
        record = EvidenceRecord(**record_data)
    except Exception as e:
        pytest.fail(f"Failed to parse model output into EvidenceRecord: {e}\nOutput was: {response.text}")
        
    # Validate the extraction
    assert record.concept == ITSConcept.THWARTED_BELONGINGNESS
    assert "alone" in record.evidence_text.lower() or "invisible" in record.evidence_text.lower()
    
    print(f"\nSuccessfully extracted: {record.model_dump_json(indent=2)}")
