# Legal AI Chatbot - Project Overview

## Executive Summary

The Legal AI Chatbot is an intelligent document analysis system that combines:
- **Retrieval-Augmented Generation (RAG)** for accurate legal Q&A
- **Local authentication** (no external databases)
- **Multi-tier LLM architecture** (local + cloud fallback)
- **Automated risk detection** and document summarization
- **Semantic document search** using vector embeddings

Target Users: Lawyers, legal teams, contract reviewers, compliance officers

---

## 🎯 Core Features

### 1. Document Intelligence
- **Upload PDFs**: Process legal contracts and documents
- **Semantic Search**: Find relevant clauses using embeddings
- **Risk Detection**: Automatically identify problematic clauses
- **Summarization**: Get document overview in seconds
- **Multi-level Chunking**: Break documents into meaningful segments

### 2. Q&A System
- **RAG-based Answers**: Retrieve relevant clauses, then generate answers
- **Spell Correction**: Handle typos and misspellings
- **Legal References**: Parse "Section X of Act Y" directly
- **Fuzzy Matching**: Find similar questions even with different wording
- **Fallback Intelligence**: Use Gemini API for out-of-knowledge-base questions

### 3. Security
- **Local Authentication**: No external database, PBKDF2 hashing
- **Token-based Auth**: HMAC-signed tokens with expiration
- **Session Persistence**: Remember login across browser refreshes
- **Secure Storage**: Credentials stored locally with salt + hash

### 4. Analysis & Insights
- **Risk Scoring**: High/Medium/Low classification
- **Clause Extraction**: Identify key terms and conditions
- **Metadata Tracking**: Know document source and retrieval confidence
- **Confidence Scores**: Understand answer reliability

---

## 🏗️ System Architecture

### High-Level Data Flow

```
User ──→ Frontend (React) ──→ API (FastAPI) ──→ Backend Services
                                  ↓
                        ┌─────────────────────┐
                        │  RAG Engine         │
                        ├─────────────────────┤
                        │ ▪ FAISS Index       │
                        │ ▪ Embeddings        │
                        │ ▪ Vector Search     │
                        └─────────────────────┘
                                  ↓
                        ┌─────────────────────┐
                        │  LLM Routing        │
                        ├─────────────────────┤
                        │ ▪ Ollama (local)    │
                        │ ▪ Gemini (fallback) │
                        │ ▪ Timeout handling  │
                        └─────────────────────┘
                                  ↓
                        ┌─────────────────────┐
                        │  Analysis Engine    │
                        ├─────────────────────┤
                        │ ▪ Risk Detection    │
                        │ ▪ Summarization     │
                        │ ▪ Metadata Tracking │
                        └─────────────────────┘
```

### Component Responsibilities

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Frontend** | User interface | React, TypeScript, Tailwind |
| **API Layer** | HTTP endpoints | FastAPI, Pydantic |
| **RAG Engine** | Document search | FAISS, Sentence Transformers |
| **Auth System** | User management | PBKDF2, HMAC, JSON store |
| **LLM Layer** | Answer generation | Ollama, Google Gemini |
| **Storage** | Persistence | FAISS index, JSON files |

---

## 📊 User Journey

### Journey 1: Upload & Analyze Document

```
1. User logs in
   └─ Email/password → Auth API
   └─ Receive bearer token
   └─ Token stored in localStorage

2. User uploads PDF
   └─ POST /upload with file
   └─ Backend extracts text, chunks it
   └─ Embeds chunks, adds to FAISS index
   └─ Returns: chunks created/added count

3. User requests analysis
   └─ GET /analyze
   └─ Backend scans all chunks for risk
   └─ Returns: risk summary + detailed sections

4. User sees results
   └─ Dashboard shows risks by severity
   └─ Clauses highlighted with explanations
```

### Journey 2: Ask Question

```
1. User enters query
   └─ "What is the termination clause?"

2. Query Processing
   ├─ Spell correction
   ├─ Legal reference extraction (Section X check)
   ├─ Exact question match (fuzzy)
   └─ If no match: proceed to semantic search

3. Semantic Search
   ├─ Embed query (384-dim vector)
   ├─ FAISS search top 50 chunks
   ├─ Score by: embedding (82%) + keywords (15%) + source (3%)
   └─ Return top match

4. LLM Generation
   ├─ Try Ollama (4s timeout)
   ├─ If timeout/error: Use Gemini API
   └─ Return generated answer

5. Risk Detection
   └─ Scan clause for risk keywords
   └─ Assign risk: High/Medium/Low

6. Response Format
   └─ JSON with answer, source, confidence, risk
```

### Journey 3: Get Document Summary

```
1. User requests summary
   └─ GET /summarize

2. Full Document Processing
   └─ Extract all text from uploaded PDF
   └─ Pass to Gemini API

3. Gemini Analysis
   └─ Identified: parties, purpose, scope, terms, obligations
   └─ Generate 2-3 paragraph summary

4. User Views Summary
   └─ Key points displayed
   └─ Can drill down to full scan
```

---

## 🔍 Technical Decisions

### Why FAISS for Vector Search?

- ✅ **Fast L2 distance search** (50ms for 50K vectors)
- ✅ **Persistent storage** (serialize/deserialize)
- ✅ **No external service** (runs locally)
- ✅ **Scalable** (can handle 1M+ vectors)
- ❌ Trade-off: No approximate search needed yet

### Why Multi-Tier LLM?

- ✅ **Privacy**: Ollama stays local, no data to cloud
- ✅ **Cost**: Free after initial model download
- ✅ **Speed**: 1-3 seconds for small queries
- ⚠️ **Reliability**: Falls back to Gemini if timeout
- ✅ **Fallback**: Gemini handles complex queries

### Why Local Authentication?

- ✅ **No database**, just JSON file
- ✅ **PBKDF2 hashing**, 120K iterations
- ✅ **Stateless tokens**, can add to any request
- ✅ **Simple deployment**, no DB migrations
- ❌ Trade-off: No token revocation (no blacklist)

### Why Multi-Level Chunking?

- ✅ **Semantic coherence**: Chunks follow document structure
- ✅ **Granular analysis**: Risk at clause level, not whole doc
- ✅ **Better retrieval**: Smaller vectors, more precise search
- ✅ **Flexible**: ARTICLE → clause → sliding window fallback
- ✅ **Constraint**: 50-1000 words ensures meaningful content

---

## 📈 Data Flow Details

### Query to Answer Pipeline

```
Input: "What is liability in this contract?"
   ↓
Step 1: Spell Correct
   "What is liabl..." → "What is liability..."
   ↓
Step 2: Extract Legal Reference
   Pattern: (section|clause) + (number) + (act)
   Result: None (not "Section X" pattern)
   ↓
Step 3: Exact Question Match (Fuzzy)
   Search DB: "What is the liability...?"
   Similarity: 0.87 (≥0.85 threshold) ✓ Found!
   ↓
Step 4: (Skip semantic search, already matched)
   Return confidence: 0.99
   ↓
Step 5: LLM Generation (Router)
   Start Ollama (4s timeout)
   → If success: return answer
   → If timeout: use Gemini API
   ↓
Step 6: Risk Detection
   Scan clause: "liability limited to..."
   Keywords found: "liability"
   Risk Level: Medium
   ↓
Output: JSON Response
{
  "answer": "Liability is limited to...",
  "confidence_score": 0.99,
  "risk_level": "Medium",
  "clause_reference": "Section 8"
}
```

### Document Upload Pipeline

```
Input: contract.pdf (10 MB)
   ↓
Step 1: Extract Text
   Use pdfplumber to read all pages
   Result: Raw text 50K words
   ↓
Step 2: Multi-Level Chunking
   Level 1: Split by ARTICLE/SECTION
   Result: 8 articles
   ↓
   Level 2: Split by numbered clauses (3.14)
   Result: 45 chunks (50-300 words each)
   ↓
   Level 3: Sliding window (if needed)
   Target: 150 words per chunk
   ↓
Step 3: Vector Embedding
   Model: Sentence Transformers (all-MiniLM-L6-v2)
   Per chunk: 45 → 45 embeddings (384-dim)
   ↓
Step 4: FAISS Indexing
   Add vectors to IndexFlatL2
   Store chunks in JSON
   ↓
Step 5: Persistence
   Save to disk:
   - legal_qa.index (binary)
   - legal_qa_chunks.json
   - legal_qa_sources.json
   ↓
Output: Chunks Created: 45
        Chunks Added: 42
```

---

## 🗂️ File Organization

```
legal-chatbot/
├── frontend/                     # React application
│   ├── src/
│   │   ├── App.tsx              # Main component (auth + chat)
│   │   ├── components/          # Reusable components
│   │   ├── services/            # API integration
│   │   ├── types.ts             # TypeScript definitions
│   │   └── styles/              # CSS (Tailwind)
│   └── package.json
│
├── backend/                      # FastAPI application
│   ├── rag_engine/              # Core modules
│   │   ├── main.py              # API endpoints
│   │   ├── rag_core.py          # Vector search
│   │   ├── auth_local.py        # Auth system
│   │   ├── document_processor.py # PDF handling
│   │   ├── llm_router.py        # LLM selection
│   │   ├── gemini_engine.py     # Cloud LLM
│   │   ├── llm_engine.py        # Local LLM
│   │   ├── risk_engine.py       # Risk detection
│   │   └── relevance_reranker.py # Fine-tuning
│   ├── uploads/                 # User PDFs
│   ├── vector_db/               # FAISS index
│   ├── local_users.json         # Auth store
│   └── requirements.txt
│
└── docs/                         # Documentation (YOU ARE HERE)
    ├── README.md                # Documentation hub
    ├── PROJECT_OVERVIEW.md      # This file
    ├── SETUP_GUIDE.md
    ├── BACKEND_GUIDE.md
    ├── FRONTEND_GUIDE.md
    ├── API_REFERENCE.md
    ├── ARCHITECTURE.md
    └── TROUBLESHOOTING.md
```

---

## 🔄 Integration Points

### Frontend ↔ Backend
- **Protocol**: HTTP/REST
- **Format**: JSON request/response
- **Auth**: Bearer token in header
- **Base URL**: `/api` (proxied by Vite dev server)

### Backend ↔ LLM Services
- **Local**: Ollama at `http://localhost:11434`
- **Cloud**: Google Gemini API with `GEMINI_API_KEY`

### Backend ↔ Storage
- **Vector DB**: FAISS persistent files
- **Auth**: `local_users.json`
- **Uploads**: `uploads/` directory
- **Metadata**: JSON files in `vector_db/`

---

## 📊 Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Document Upload (10 MB) | 5-10s | PDF extract + chunk + embed + index |
| Query Processing | ~100ms | Embedding + FAISS search |
| Semantic Search | 50ms | Top 50 candidates |
| Ollama Generation | 1-3s | Local model (llama3) |
| Gemini Generation | 2-4s | Cloud API + network |
| Risk Analysis | 2-5s | Scan all chunks |
| Summarization | 3-8s | Full document → Gemini |

---

## 🔐 Security Architecture

### Authentication Flow

```
Register:
  username + password
    ↓
  Validate (unique, ≥6 chars)
    ↓
  Generate salt (16 random hex bytes)
    ↓
  Hash: PBKDF2(password, salt, 120K iterations)
    ↓
  Store: {salt, hash} in local_users.json
    
Login:
  username + password
    ↓
  Load user from file
    ↓
  Recompute hash: PBKDF2(password, stored_salt)
    ↓
  Compare using constant-time compare
    ↓
  If match: Create token
    Payload: {sub, iat, exp}
    Sign: HMAC-SHA256(payload, secret)
    Token: base64(payload).base64(sig)
    
Verify:
  Extract payload, sig from token
    ↓
  Verify HMAC signature
    ↓
  Check exp > now
    ↓
  Return payload or error
```

---

## 🚀 Deployment Architecture

### Local Development
```
Frontend: Vite dev server (port 3000)
Backend: Uvicorn (port 8000)
Storage: Local filesystem
Auth: local_users.json
```

### Production Ready
```
Frontend: Built React bundle + CDN
Backend: Uvicorn + Gunicorn
Storage: FAISS index + cloud backup
Auth: local_users.json or integrate with DB
```

---

## 📝 Next Steps

- **Start Using**: See [USAGE_GUIDE.md](USAGE_GUIDE.md)
- **Set Up Locally**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Develop Backend**: See [BACKEND_GUIDE.md](BACKEND_GUIDE.md)
- **Develop Frontend**: See [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md)
- **Fix Issues**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Version:** 1.0  
**Last Updated:** February 24, 2026
