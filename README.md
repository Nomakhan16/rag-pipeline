# RAG Pipeline

A Retrieval-Augmented Generation pipeline for document Q&A.

## Features
- Upload PDF documents
- Vector search with ChromaDB
- AI responses using Gemini
- FastAPI REST API
- Docker containerized

## Setup
1. Clone repository
2. Add `.env` with `GEMINI_API_KEY=your_key`
3. Run `docker-compose up`
4. Visit `http://localhost:8000/docs`

## API Endpoints
- `POST /upload` - Upload documents
- `POST /query` - Ask questions
- `GET /documents` - View metadata