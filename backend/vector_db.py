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
            },
            {
                "case_id": "C-130",
                "description": "SIM swap fraud leading to unauthorized password reset and instant wire transfer to offshore crypto exchange.",
                "outcome": "FRAUD"
            },
            {
                "case_id": "C-142",
                "description": "Routine online grocery order matching long-term historical purchase velocity, customer home IP, and registered iOS device.",
                "outcome": "LEGITIMATE"
            },
            {
                "case_id": "C-155",
                "description": "Card-not-present transaction spree involving multiple digital gift cards across 4 different merchants within 10 minutes.",
                "outcome": "FRAUD"
            },
            {
                "case_id": "C-168",
                "description": "Authorized push payment (APP) scam where victim was coerced via phone phishing into initiating high-value wire transfer.",
                "outcome": "FRAUD"
            },
            {
                "case_id": "C-174",
                "description": "Monthly recurring SaaS subscription charge from established vendor with zero velocity anomalies or location mismatches.",
                "outcome": "LEGITIMATE"
            },
            {
                "case_id": "C-189",
                "description": "Synthetic identity fraud using stolen SSN with recently opened account attempting rapid credit line drain.",
                "outcome": "FRAUD"
            },
            {
                "case_id": "C-201",
                "description": "GEO-location mismatch where mobile transaction originated 5,000 km away from physical store POS scan 15 minutes prior.",
                "outcome": "FRAUD"
            },
            {
                "case_id": "C-215",
                "description": "Micro-deposit probing attack testing stolen credit card numbers against non-profit donation gateway.",
                "outcome": "FRAUD"
            },
            {
                "case_id": "C-228",
                "description": "Salary direct deposit cleared into verified checking account followed by regular bill payments.",
                "outcome": "LEGITIMATE"
            },
            {
                "case_id": "C-240",
                "description": "Triangulation fraud using compromised merchant API keys to route fake orders through third-party fulfillment.",
                "outcome": "FRAUD"
            },
            {
                "case_id": "C-255",
                "description": "First-party friendly fraud where account holder placed valid order but falsely claimed non-receipt of goods.",
                "outcome": "FRAUD"
            },
            {
                "case_id": "C-270",
                "description": "ATM cash withdrawal using chip-and-PIN from primary cardholder at local branch near home address.",
                "outcome": "LEGITIMATE"
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
