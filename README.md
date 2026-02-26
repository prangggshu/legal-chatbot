# Legal Chatbot

A full-stack legal document chatbot that combines RAG (retrieval-augmented generation), local or cloud LLMs, and a simple web UI to answer questions, summarize documents, and assess clause risk levels.

## Key Features

- Upload legal documents and query them with natural language.
- Risk analysis with interpretable keyword/regex rules.
- Document summarization using Gemini (if configured).
- Local LLM option (Ollama) with Gemini fallback.
- React frontend with chat UI and document actions.

## Project Structure

- backend/: FastAPI backend, RAG pipeline, risk engine, and LLM routing
- frontend/: React + Vite UI
- docs/: Architecture and API documentation
- vector_db/: Sample FAISS data and metadata

## Quick Start

### Backend

1. Create a Python environment and install deps:
   - cd backend
   - pip install -r requirements.txt
2. Configure environment variables:
   - GEMINI_API_KEY (optional, for summarize/fallback)
3. Run the API server:
   - cd backend/rag_engine
   - uvicorn main:app --reload --host 0.0.0.0 --port 8000

### Frontend

1. Install dependencies:
   - cd frontend
   - npm install
2. Run the dev server:
   - npm run dev
3. Open http://localhost:5173

The Vite dev server proxies /api/* to http://localhost:8000/*.

## Usage Notes

- Upload a document first, then use Analyze or Summarize.
- Risk assessment is rule-based and interpretable.
- If Ollama is not running, the system falls back to Gemini when configured.

## Documentation

- docs/PROJECT_OVERVIEW.md
- docs/ARCHITECTURE.md
- docs/API_REFERENCE.md
- docs/USAGE_GUIDE.md
- docs/TROUBLESHOOTING.md

## Tests

- cd backend/rag_engine
- python rag_test.py

## Troubleshooting

See docs/TROUBLESHOOTING.md for common issues and fixes.
