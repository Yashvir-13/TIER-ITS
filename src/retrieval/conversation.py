import chromadb
from typing import List
from src.schemas import ConversationTurn

class ConversationRetriever:
    """
    Deep module hiding the complexity of ChromaDB and embedding models.
    Provides a simple interface to retrieve relevant past turns.
    """
    def __init__(self, persist_directory: str = "chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="conversations")

    def add_turns(self, turns: List[ConversationTurn]):
        """
        Embeds and stores new conversation turns.
        """
        if not turns:
            return
            
        documents = [turn.text for turn in turns]
        metadatas = [{"speaker": turn.speaker, "turn_index": turn.turn_index} for turn in turns]
        ids = [f"turn_{turn.turn_index}" for turn in turns]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def retrieve_relevant_turns(self, query: str, top_k: int = 5) -> List[ConversationTurn]:
        """
        Retrieves the most semantically relevant conversation turns for a given query.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        turns = []
        if not results['documents'] or not results['documents'][0]:
            return turns
            
        for i in range(len(results['documents'][0])):
            text = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            turns.append(ConversationTurn(
                turn_index=meta["turn_index"],
                speaker=meta["speaker"],
                text=text
            ))
            
        return turns
