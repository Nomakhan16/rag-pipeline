import uuid
from typing import List

class VectorStore:
    def __init__(self):
        self.documents = []
        self.metadata = []
        print("Using Simple Vector Store (ChromaDB removed for Docker compatibility)")
    
    def add_documents(self, documents: list, metadata: list = None):
        if metadata is None:
            metadata = [{}] * len(documents)
        
        self.documents.extend(documents)
        self.metadata.extend(metadata)
        
        ids = [str(uuid.uuid4()) for _ in documents]
        return ids
    
    def search(self, query: str, n_results: int = 3):
        # Simple keyword-based search
        results = []
        for i, doc in enumerate(self.documents):
            if query.lower() in doc.lower():
                if len(results) < n_results:
                    results.append(doc)
        
        return {
            "ids": [[str(uuid.uuid4()) for _ in results]],
            "documents": [results],
            "metadatas": [[self.metadata[i] for i in range(len(results))]]
        }