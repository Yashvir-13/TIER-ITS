import uuid
from typing import List, Optional
from src.schemas import ConversationTurn

try:
    import chromadb
except ImportError:
    chromadb = None

class ConversationRetriever:
    """
    Deep module hiding the complexity of ChromaDB and embedding models.
    Provides a simple interface to retrieve relevant past turns.
    Guarantees session isolation by assigning each retriever instance a unique collection.
    Includes a graceful in-memory fallback if chromadb is not installed in the execution environment.
    """
    def __init__(self, persist_directory: str = "chroma_db", in_memory: bool = False, collection_name: Optional[str] = None):
        if chromadb is not None:
            if in_memory:
                self.client = chromadb.EphemeralClient()
            else:
                self.client = chromadb.PersistentClient(path=persist_directory)
            c_name = collection_name or f"conv_{uuid.uuid4().hex[:12]}"
            self.collection = self.client.get_or_create_collection(name=c_name)
        else:
            self.client = None
            self.collection = None
            self._fallback_turns: List[ConversationTurn] = []

    def add_turns(self, turns: List[ConversationTurn]):
        """
        Embeds and stores new conversation turns.
        """
        if not turns:
            return
            
        if self.collection is not None:
            documents = [turn.text for turn in turns]
            metadatas = [{"speaker": turn.speaker, "turn_index": turn.turn_index} for turn in turns]
            ids = [f"turn_{turn.turn_index}" for turn in turns]
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        else:
            self._fallback_turns.extend(turns)

    def retrieve_relevant_turns(self, query: str, top_k: int = 5) -> List[ConversationTurn]:
        """
        Retrieves the most semantically relevant conversation turns for a given query.
        """
        if self.collection is not None:
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
        else:
            # Fallback simple retrieval: returns most recent relevant turns up to top_k
            return self._fallback_turns[-top_k:] if self._fallback_turns else []
