import os
import uuid
import re
from typing import List, Dict
from fastapi import HTTPException, UploadFile
from app.utils.file_utils import ensure_upload_dir
from app.services.llm_service import LLMService

class SimpleVectorStore:
    def __init__(self):
        self.documents = []
        self.metadata = []
        self.all_ids = []
        print("Using Simple Vector Store")
    
    def add_documents(self, documents: list, metadata: list = None):
        if metadata is None:
            metadata = [{}] * len(documents)
        
        new_ids = [str(uuid.uuid4()) for _ in documents]
        self.documents.extend(documents)
        self.metadata.extend(metadata)
        self.all_ids.extend(new_ids)
        
        print(f"Added {len(documents)} chunks. Total chunks in store: {len(self.documents)}")
        return new_ids
    
    def search(self, query: str, n_results: int = 5):
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        results = []
        result_docs = []
        result_metadatas = []
        result_ids = []
        scores = []
        
        for i, doc in enumerate(self.documents):
            doc_lower = doc.lower()
            score = 0
            
            # Exact phrase match (highest priority)
            if query_lower in doc_lower:
                score += 10
            
            # Individual word matches
            for word in query_words:
                if len(word) > 3 and word in doc_lower:
                    score += 1
            
            # If we found any matches, add to results
            if score > 0:
                results.append((score, doc, self.metadata[i], self.all_ids[i]))
        
        # Sort by relevance score (highest first)
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Take top n_results
        for score, doc, metadata, doc_id in results[:n_results]:
            result_docs.append(doc)
            result_metadatas.append(metadata)
            result_ids.append(doc_id)
            scores.append(score)
        
        print(f"🔍 Search for '{query}' found {len(result_docs)} results (from {len(self.documents)} total chunks)")
        if result_docs:
            print(f"📊 Top result score: {scores[0] if scores else 0}")
        
        return {
            "ids": [result_ids],
            "documents": [result_docs],
            "metadatas": [result_metadatas],
            "scores": [scores]
        }

class DocumentService:
    def __init__(self):
        self.upload_dir = ensure_upload_dir()
        self.vector_store = SimpleVectorStore()
        self.llm_service = LLMService()
        print(f"DocumentService initialized with upload dir: {self.upload_dir}")
    
    async def process_documents(self, files: List[UploadFile]) -> Dict:
        try:
            processed_files = []
            total_chunks = 0
            
            print(f"Processing {len(files)} files")
            
            if len(files) > 20:
                raise HTTPException(status_code=400, detail="Maximum 20 files allowed")
            
            for file in files:
                print(f"Processing file: {file.filename}")
                
                try:
                    # Read file content
                    content = await file.read()
                    print(f"File size: {len(content)} bytes")
                    
                    if len(content) == 0:
                        raise HTTPException(status_code=400, detail=f"File {file.filename} is empty")
                    
                    # Create upload directory if it doesn't exist
                    os.makedirs(self.upload_dir, exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(self.upload_dir, f"{uuid.uuid4()}_{file.filename}")
                    with open(file_path, "wb") as buffer:
                        buffer.write(content)
                    print(f"File saved to: {file_path}")
                    
                    # Extract text from PDF
                    text, page_count = self._extract_text_from_pdf(file_path)
                    print(f"Extracted text length: {len(text)}, Pages: {page_count}")
                    
                    if page_count > 1000:
                        raise HTTPException(status_code=400, detail=f"PDF has {page_count} pages, maximum is 1000")
                    
                    # Clean the extracted text
                    cleaned_text = self._clean_extracted_text(text)
                    print(f"Cleaned text length: {len(cleaned_text)}")
                    
                    # Chunk the text
                    chunks = self._chunk_text(cleaned_text)
                    print(f"Created {len(chunks)} chunks")
                    
                    # Create metadata
                    metadata = [
                        {
                            "filename": file.filename, 
                            "chunk_id": i, 
                            "total_chunks": len(chunks),
                            "file_size": len(content),
                            "page_count": page_count
                        } 
                        for i in range(len(chunks))
                    ]
                    
                    # Add to vector store
                    self.vector_store.add_documents(chunks, metadata)
                    total_chunks += len(chunks)
                    
                    processed_files.append({
                        "filename": file.filename,
                        "file_path": file_path,
                        "text_length": len(text),
                        "chunks_count": len(chunks),
                        "page_count": page_count,
                        "status": "success"
                    })
                    
                except Exception as e:
                    print(f"Error processing {file.filename}: {str(e)}")
                    processed_files.append({
                        "filename": file.filename,
                        "status": "failed",
                        "error": str(e)
                    })
                    continue
            
            return {
                "processed_files": processed_files, 
                "total_chunks": total_chunks,
                "total_files_processed": len([f for f in processed_files if f["status"] == "success"])
            }
            
        except Exception as e:
            print(f"Error in process_documents: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")
    
    def _extract_text_from_pdf(self, file_path: str):
        """
        Simple PDF text extraction with error handling
        """
        try:
            from PyPDF2 import PdfReader
            
            text = ""
            with open(file_path, "rb") as file:
                pdf_reader = PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                if page_count > 1000:
                    return "", page_count
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        print(f"Error extracting text from page {page_num}: {e}")
                        continue
            
            return text, page_count
            
        except ImportError:
            return "PDF text extraction requires PyPDF2 installation.", 0
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return f"Error extracting text: {str(e)}", 0
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean PDF extracted text to fix common issues
        """
        if not text:
            return ""
        
        # Fix space-separated words (most common issue)
        # This fixes patterns like "r easoning" -> "reasoning", "f orward" -> "forward"
        text = re.sub(r'(\b\w) (\w\b)', r'\1\2', text)
        
        # Fix broken words at line endings
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
        
        # Fix multiple spaces
        text = re.sub(r' +', ' ', text)
        
        # Fix newlines and excessive whitespace
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+\n', '\n', text)
        text = re.sub(r'\n\s+', '\n', text)
        
        # Fix punctuation spacing
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])\s*', r'\1 ', text)
        
        # Fix common PDF artifacts
        text = re.sub(r'\\[ntr]', ' ', text)
        text = re.sub(r'\x0c', '\n', text)
        
        # Ensure proper sentence spacing
        text = re.sub(r'\.(\w)', r'. \1', text)
        text = re.sub(r'\!(\w)', r'! \1', text)
        text = re.sub(r'\?(\w)', r'? \1', text)
        
        return text.strip()
    
    def _chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """
        Split text into chunks with overlap for context preservation
        """
        if not text or len(text.strip()) == 0:
            return []
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                # Try to break at sentence end
                break_pos = text.rfind('. ', start, end)
                if break_pos == -1:
                    break_pos = text.rfind(' ', start, end)
                if break_pos != -1 and break_pos > start + chunk_size // 2:
                    end = break_pos + 1
            
            chunk = text[start:end].strip()
            if chunk and len(chunk) > 50:  # Only add substantial chunks
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def search_documents(self, query: str, n_results: int = 5):
        """
        Search for relevant document chunks and generate LLM response
        """
        try:
            if not query or not query.strip():
                return {
                    "question": query,
                    "answer": "Please provide a valid question.",
                    "sources_count": 0
                }
            
            search_results = self.vector_store.search(query.strip(), n_results)
            
            if search_results and search_results.get('documents') and search_results['documents'][0]:
                context_chunks = search_results['documents'][0]
                llm_response = self.llm_service.generate_response(query, context_chunks)
                
                return {
                    "question": query,
                    "answer": llm_response,
                    "sources_count": len(context_chunks)
                }
            else:
                return {
                    "question": query,
                    "answer": "No relevant information found in the documents.",
                    "sources_count": 0
                }
            
        except Exception as e:
            print(f"Search error: {e}")
            return {
                "question": query,
                "answer": f"Error searching documents: {str(e)}",
                "sources_count": 0
            }
    
    def get_document_stats(self):
        """
        Get statistics about processed documents
        """
        return {
            "upload_directory": self.upload_dir,
            "vector_store_type": "Simple Vector Store",
            "total_chunks_stored": len(self.vector_store.documents),
            "total_documents": len(set([meta.get('filename', '') for meta in self.vector_store.metadata if meta]))
        }