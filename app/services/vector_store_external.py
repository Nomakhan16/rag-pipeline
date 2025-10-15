import chromadb
from chromadb.config import Settings
import os
from sentence_transformers import SentenceTransformer
import uuid

class VectorStoreExternal:
    def __init__(self):
        # Connect to external ChromaDB
        self.client = chromadb.HttpClient(host="chroma-db", port=8000)
        self.collection = self.client.get_or_create_collection(name="documents")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def add_documents(self, documents: list, metadata: list = None):
        """Add documents to vector database"""
        if metadata is None:
            metadata = [{}] * len(documents)
        
        embeddings = self.embedder.encode(documents).tolist()
        ids = [str(uuid.uuid4()) for _ in documents]
        
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadata,
            ids=ids
        )
        return ids
    
    def search(self, query: str, n_results: int = 3):
        """Search for similar documents"""
        query_embedding = self.embedder.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        return results