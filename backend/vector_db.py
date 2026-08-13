import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

class FraudVectorDB:
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Use a lightweight sentence-transformer model for local embeddings
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Create or get the collection
        self.collection = self.client.get_or_create_collection(
            name="historical_fraud_cases",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )
        
        # Pre-seed if empty
        if self.collection.count() == 0:
            self._seed_database()
            
    def _seed_database(self):
        cases = [
            {
                "case_id": "C-101",
                "description": "High value electronics purchase from a new device with unknown OS, originating from high-risk IP. Fraudulent chargeback initiated 2 days later.",
                "outcome": "FRAUD"
            },
            {
                "case_id": "C-102",
                "description": "Standard travel booking from known home location and recognized device fingerprint.",
                "outcome": "LEGITIMATE"
            },
            {
                "case_id": "C-112",
                "description": "Suspicious transaction with unknown OS and high merchant fraud rate. The transaction was flagged by rules engine due to velocity.",
                "outcome": "FRAUD"
            },
            {
                "case_id": "C-125",
                "description": "Multiple small transactions followed by a massive transfer. Account takeover suspected. Location was RU.",
                "outcome": "FRAUD"
            }
        ]
        
        self.collection.add(
            documents=[c["description"] for c in cases],
            metadatas=[{"case_id": c["case_id"], "outcome": c["outcome"]} for c in cases],
            ids=[c["case_id"] for c in cases]
        )
        print("Vector Database seeded with initial historical cases.")

    def similarity_search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        if self.collection.count() == 0:
            return []
            
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        formatted_results = []
        if results["documents"] and len(results["documents"]) > 0:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "case_id": results["ids"][0][i],
                    "description": results["documents"][0][i],
                    "outcome": results["metadatas"][0][i]["outcome"],
                    "similarity_distance": results["distances"][0][i] if results["distances"] else 0.0
                })
        return formatted_results

_vector_store_instance = None

def get_vector_store() -> FraudVectorDB:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = FraudVectorDB()
    return _vector_store_instance

class LazyVectorStoreProxy:
    """Proxy object that defers FraudVectorDB instantiation until first call."""
    def similarity_search(self, *args, **kwargs):
        return get_vector_store().similarity_search(*args, **kwargs)

    @property
    def collection(self):
        return get_vector_store().collection

    @collection.setter
    def collection(self, value):
        get_vector_store().collection = value

# Singleton proxy instance
vector_store = LazyVectorStoreProxy()
