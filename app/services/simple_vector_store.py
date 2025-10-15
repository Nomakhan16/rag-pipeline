import uuid
from typing import List, Dict

class SimpleVectorStore:
    def __init__(self):
        self.documents = []
        self.metadata = []
    
    def add_documents(self, documents: list, metadata: list = None):
        self.documents.extend(documents)
        if metadata:
            self.metadata.extend(metadata)
        return [str(uuid.uuid4()) for _ in documents]
    
    def search(self, query: str, n_results: int = 3):
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