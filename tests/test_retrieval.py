import pytest
import chromadb
from src.schemas import ConversationTurn
from src.retrieval.conversation import ConversationRetriever

def test_conversation_retriever_adds_and_retrieves_turns(tmp_path):
    # Use a temporary directory for ChromaDB so tests don't pollute local state
    retriever = ConversationRetriever(persist_directory=str(tmp_path))
    
    turns = [
        ConversationTurn(turn_index=0, speaker="patient", text="I like walking in the park."),
        ConversationTurn(turn_index=1, speaker="therapist", text="That sounds relaxing."),
        ConversationTurn(turn_index=2, speaker="patient", text="Honestly, I feel like a massive burden to my family."),
        ConversationTurn(turn_index=3, speaker="therapist", text="I am sorry you are feeling that way."),
    ]
    
    retriever.add_turns(turns)
    
    # Query for something related to perceived burdensomeness
    results = retriever.retrieve_relevant_turns("feeling like a burden", top_k=1)
    
    assert len(results) == 1
    assert results[0].turn_index == 2
    assert "burden" in results[0].text
