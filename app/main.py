from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import sys
from dotenv import load_dotenv
from typing import List

load_dotenv()

app = FastAPI(title="RAG Pipeline API", version="1.0.0")

# Debug imports
try:
    print("Trying to import document_service...")
    from app.services.document_service import DocumentService
    print("DocumentService imported successfully!")
    document_service = DocumentService()
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
    document_service = None

@app.get("/")
async def root():
    return {"message": "RAG Pipeline API is running"}

@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(..., description="Upload up to 20 documents")):
    if document_service is None:
        raise HTTPException(status_code=500, detail="Document service not available")
    
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 files allowed")
    
    try:
        # Print debug info
        print(f"Processing {len(files)} files:")
        for file in files:
            print(f" - {file.filename} (size: {file.size})")
        
        result = await document_service.process_documents(files)
        return {
            "status": "success", 
            "message": f"Processed {len(files)} files",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")

@app.post("/query")
async def query_documents(question: str):
    if document_service is None:
        raise HTTPException(status_code=500, detail="Document service not available")
    
    try:
        results = document_service.search_documents(question)
        return {
            "question": question,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@app.get("/documents")
async def get_documents():
    return {"message": "Documents metadata endpoint - to be implemented"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "RAG Pipeline API"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="127.0.0.1", port=port)