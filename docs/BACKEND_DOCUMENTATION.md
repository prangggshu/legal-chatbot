# Legal AI Chatbot - Backend Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Module Structure](#module-structure)
4. [API Endpoints](#api-endpoints)
5. [Data Flow](#data-flow)
6. [Core Components](#core-components)
7. [Query Processing Pipeline](#query-processing-pipeline)
8. [Database & Vector Storage](#database--vector-storage)
9. [Authentication System](#authentication-system)
10. [Error Handling](#error-handling)

---

## System Overview

The Legal AI Chatbot backend is a FastAPI-based application that provides:
- **RAG (Retrieval-Augmented Generation)** for legal document Q&A
- **Multi-tier LLM routing** (local Ollama + Gemini API fallback)
- **Document analysis** with risk detection and summarization
- **Local authentication** (no database required)
- **Vector-based semantic search** using FAISS

**Tech Stack:**
- Framework: FastAPI
- Vector DB: FAISS (Facebook AI Similarity Search)
- Embeddings: Sentence Transformers (all-MiniLM-L6-v2)
- Local LLM: Ollama (llama3)
- Cloud LLM: Google Gemini 2.5 Flash
- Document Processing: pdfplumber
- Auth: PBKDF2 + HMAC signing

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│                     (main.py)                                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Auth Routes  │  │ Chat Routes  │  │ Upload Routes│       │
│  │ /auth/*      │  │ /ask         │  │ /upload      │       │
│  │ /verify      │  │ /analyze     │  │ /summarize   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                          ▼                                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────┐                     │
│  │    RAG Core (rag_core.py)           │                     │
│  │  - Vector Search (FAISS)            │                     │
│  │  - Query Processing                 │                     │
│  │  - Legal Reference Extraction       │                     │
│  │  - Embedding Management             │                     │
│  └─────────────────────────────────────┘                     │
│                 ▼                                             │
├─────────────────────────────────────────────────────────────┤
│  Document Processing      │   LLM Orchestration             │
│  ├─ extract_text()        │   ├─ llm_router.py             │
│  ├─ chunk_text()          │   │  - LLM switching            │
│  └─ Risk Detection        │   │  - Timeout handling         │
│                           │   ├─ Ollama (local)            │
│                           │   ├─ Gemini (fallback)         │
│                           │   └─ Reranking                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────┐                     │
│  │    Storage Layer                    │                     │
│  │  ├─ FAISS Index                     │                     │
│  │  ├─ local_users.json (auth)         │                     │
│  │  └─ Vector DB files                 │                     │
│  └─────────────────────────────────────┘                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Structure

### File Organization
```
backend/
├── rag_engine/
│   ├── main.py                    # FastAPI app & routes
│   ├── rag_core.py               # Vector search & retrieval
│   ├── auth_local.py             # Local auth (PBKDF2 + tokens)
│   ├── document_processor.py      # PDF extraction & chunking
│   ├── risk_engine.py            # Risk detection logic
│   ├── gemini_engine.py          # Google Gemini integration
│   ├── llm_engine.py             # Ollama (local LLM)
│   ├── llm_router.py             # LLM selection logic
│   ├── relevance_reranker.py     # Fine-grained ranking
│   └── __init__.py
├── uploads/                       # User-uploaded PDFs
├── vector_db/                     # FAISS index & metadata
├── requirements.txt              # Python dependencies
└── local_users.json             # User credentials (auto-created)
```

---

## API Endpoints

### Authentication Endpoints

#### 1. **POST `/auth/register`**
Register a new local user with username and password.

**Request:**
```json
{
  "username": "john_lawyer",
  "password": "SecurePass123"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "detail": "User registered successfully.",
  "username": "john_lawyer"
}
```

**Validation:**
- Username cannot be empty
- Password must be ≥6 characters
- Username must be unique

---

#### 2. **POST `/auth/login`**
Login with username/password to receive a bearer token.

**Request:**
```json
{
  "username": "john_lawyer",
  "password": "SecurePass123"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "access_token": "eyJzdWIiOiJqb2huX2xhd3llciIsImlhdCI6MTcxMTg2NzM1MywiZXhwIjoxNzExODcwOTUzfQ.mKD335ouKLfnBICRWPS1",
  "token_type": "bearer",
  "username": "john_lawyer"
}
```

**Token Details:**
- Format: `payload.signature` (custom JWT-like format)
- Payload: `{sub, iat, exp}` (Base64 encoded)
- Signature: HMAC-SHA256 with secret key
- TTL: 1 hour (3600 seconds) by default

---

#### 3. **GET `/auth/verify?token=<TOKEN>`**
Verify if a token is valid and not expired.

**Response (Valid):**
```json
{
  "status": "success",
  "username": "john_lawyer",
  "expires_at": 1771887095
}
```

**Response (Expired):**
```json
{
  "status": "error",
  "detail": "Invalid or expired token."
}
```

---

### Document Upload & Analysis

#### 4. **POST `/upload`**
Upload a PDF document for processing and indexing.

**Request:** Multipart form data with file
```
Content-Disposition: form-data; name="file"; filename="contract.pdf"
...binary PDF data...
```

**Response:**
```json
{
  "status": "Document uploaded and processed",
  "chunks_created": 45,
  "chunks_added": 42
}
```

**Process:**
1. Save PDF to `uploads/` directory
2. Extract text from all pages
3. Split into semantic chunks
4. Add chunks to FAISS index
5. Persist index to disk

---

#### 5. **GET `/analyze`**
Analyze the most recently uploaded document for risk sections.

**Response:**
```json
{
  "status": "Risk analysis completed",
  "summary": {
    "total_chunks": 45,
    "risk_sections": 8,
    "high_risk": 2,
    "medium_risk": 6
  },
  "risk_sections": [
    {
      "section_index": 3,
      "risk_level": "High",
      "risk_reason": "Employer can terminate without prior notice",
      "section_text": "ARTICLE 2: Section 2.1 This employment..."
    },
    {
      "section_index": 7,
      "risk_level": "Medium",
      "risk_reason": "Financial penalty imposed",
      "section_text": "ARTICLE 3: Section 3.4 Liquidated damages..."
    }
  ]
}
```

---

#### 6. **GET `/summarize`**
Generate a brief summary of the most recently uploaded document.

**Response:**
```json
{
  "status": "success",
  "summary": "This is an Employment Agreement between ABC Corp and [Employee]. The agreement outlines the terms of employment including compensation, benefits, and termination clauses. Key provisions include a competitive non-compete clause with 2-year restriction and automatic renewal provisions..."
}
```

---

### Query & Chat

#### 7. **POST `/ask`**
Ask a question about uploaded documents and legal knowledge base.

**Request:**
```json
{
  "query": "What is section 1 of aadhaar act?"
}
```

**Response:**
```json
{
  "question": "What is section 1 of aadhaar act?",
  "answer": "Short title, extent and commencement. (1) This Act may be called the Aadhaar (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act, 2016...",
  "answer_source": "retrieval",
  "clause_reference": "Section 1",
  "confidence_score": 0.95,
  "risk_level": "Low",
  "risk_reason": "Standard legal clause"
}
```

**Answer Sources:**
- `retrieval`: From knowledge base via RAG
- `retrieval_direct_clause`: Direct section lookup
- `reranker`: Fine-tuned model ranking
- `gemini_fallback`: Gemini API (question not in KB)

---

### Utility Endpoints

#### 8. **GET `/`**
Health check endpoint.

**Response:**
```json
{
  "status": "Legal AI Backend Running"
}
```

---

## Data Flow

### Question Answering Flow

```
User Query
    ▼
1. Legal Reference Extraction
   └─ Check if "Section X of Y" pattern
   └─ If yes → Direct match in knowledge base
    ▼
2. Exact Question Match (with fuzzy tolerance)
   └─ Check for pre-stored Q&A pairs
   └─ Allow 85%+ similarity (spelling tolerance)
    ▼
3. Semantic Search (FAISS)
   └─ Embed query using Sentence Transformers
   └─ Find top 50 similar chunks
   └─ Score by: Embedding similarity (82%) + Keywords (15%) + Source (3%)
    ▼
4. Candidate Reranking (optional)
   └─ Use fine-tuned BERT model if available
   └─ Re-score top candidates
    ▼
5. LLM Generation
   └─ Route through llm_router:
   │  ├─ Try Ollama (4s timeout)
   │  ├─ If timeout/error → Gemini
   └─ Return generated answer
    ▼
6. Risk Detection
   └─ Scan answer for risk keywords
   └─ Assign risk_level: High/Medium/Low
    ▼
7. Response Formatting
   └─ Return structured JSON with metadata
```

---

### Document Upload Flow

```
PDF Upload
    ▼
1. File Storage
   └─ Save to uploads/{filename}
    ▼
2. Text Extraction
   └─ Use pdfplumber to read all pages
   └─ Concatenate with page breaks
    ▼
3. Multi-Level Chunking
   └─ Level 1: Split by ARTICLE/SECTION headers
   └─ Level 2: Split by numbered clauses (e.g., 3.14)
   └─ Level 3: Sliding window for remainder
   └─ Constraints: 50-1000 words per chunk, target 150
    ▼
4. Vector Embedding
   └─ Encode each chunk using Sentence Transformers
   └─ Generate 384-dimensional vectors
    ▼
5. FAISS Indexing
   └─ Add vectors to L2 distance index
   └─ Store chunk text in JSON
   └─ Persist index to disk
    ▼
6. Metadata Tracking
   └─ Record source: "upload" vs "legal_qa"
   └─ Track chunk count
```

---

## Core Components

### 1. **rag_core.py** - Vector Search & Retrieval

#### Global State
```python
index: faiss.IndexFlatL2          # FAISS vector index
chunks_store: list[str]           # All document chunks
chunk_sources: list[str]          # Source of each chunk
embedder: SentenceTransformer     # "all-MiniLM-L6-v2" model
```

#### Key Functions

**`build_index(chunks, persist=False, source="legal_qa")`**
- Creates a new FAISS index from scratch
- Encodes chunks to embeddings
- Initializes IndexFlatL2 (L2 distance metric)
- Optionally persists to disk

**`add_chunks(chunks, persist=False, source="upload")`**
- Appends new chunks to existing index
- Deduplicates (doesn't add if already exists)
- Encodes new chunks only
- Returns count of added chunks

**`retrieve_clause(query)`**
- Main retrieval function (3-tier fallback logic)
- Priority 1: Legal reference extraction (Section X of Act Y)
- Priority 2: Exact question match (with fuzzy tolerance)
- Priority 3: Semantic search via FAISS
- Returns: (clause_text, confidence_score)

**`retrieve_candidate_clauses(query, top_k=8)`**
- Returns top-k ranked candidates
- Each with: combined_score, retrieval_confidence, lexical_hits, clause, source

#### Query Processing Functions

**`_extract_legal_reference(query) → (section_ref, act_name)`**
- Regex pattern matching for "Section X of Act Y"
- Extracts legal reference from natural language
- Returns structured components for direct lookup

**`_extract_query_terms(query) → (terms, phrases)`**
- Spell correction (typo fixes)
- Tokenization and stopword removal
- Query expansion using legal synonyms
- Returns keywords and expanded phrases for boosting

**`_rank_candidates(query) → list[dict]`**
- Semantic search via FAISS
- For each candidate:
  - Compute embedding similarity (primary: 0.82 weight)
  - Count keyword hits (secondary: 0.15 max)
  - Apply source bonus (tertiary: 0.03)
  - Combined score = 0.82*confidence + keyword_boost + source_bonus
- Sort by combined_score descending

#### Similarity Scoring

```python
combined_score = (confidence * 0.82) + keyword_boost + source_bonus

where:
  confidence = 1 / (1 + L2_distance)           [0-1]
  keyword_boost = min(0.15, 0.04*kw + 0.06*ph) [0-0.15]
  source_bonus = 0.03 if from legal_qa else 0  [0-0.03]
```

Why this weighting?
- **Semantic similarity (82%)** is primary because embeddings naturally handle paraphrasing and synonyms
- **Keywords (15%)** boost exact matches but don't override semantic mismatches
- **Source (3%)** slight preference for curated knowledge base over user uploads

---

### 2. **auth_local.py** - Local Authentication

#### Data Storage
- File: `backend/local_users.json`
- Format: `{username: {salt, password_hash}}`
- No external database needed

#### Key Functions

**`_hash_password(password, salt) → hash`**
- Algorithm: PBKDF2-HMAC-SHA256
- Iterations: 120,000 (slow by design for security)
- Salt: 16 random hex bytes per user
- Returns: Base64-encoded hash

**`register_local_user(username, password) → (bool, str)`**
- Validates username (non-empty) and password (≥6 chars)
- Checks for duplicate usernames
- Generates random salt
- Hashes password with salt
- Saves to local_users.json
- Returns success status and message

**`verify_local_login(username, password) → bool`**
- Loads user from file
- Recomputes hash with stored salt
- Compares using `hmac.compare_digest()` (constant-time)
- Returns True only if exact match

**`create_login_token(username) → token`**
- Payload: `{sub: username, iat: now, exp: now+3600}`
- Encodes payload as Base64 JSON
- Signs with HMAC-SHA256 using TOKEN_SECRET
- Returns: `base64(payload).base64(signature)`

**`verify_login_token(token) → dict | None`**
- Splits token into payload and signature
- Verifies signature matches
- Checks expiration time
- Returns payload dict or None

#### Token Example
```
Payload: {"sub":"admin","iat":1771867353,"exp":1771870953}
Signature: mKD335ouKLfnBICRWPS1IqPYpxQjPuA7YNvsz1OXvC0=
Full Token: eyJzdWIiOiJhZG1pbiIsImlhdCI6MTc3MTg2NzM1MywiZXhwIjoxNzcxODcwOTUzfQ.mKD335ouKLfnBICRWPS1IqPYpxQjPuA7YNvsz1OXvC0=
```

---

### 3. **document_processor.py** - PDF Processing

#### `extract_text(file_path) → str`
- Uses pdfplumber to open PDF
- Iterates through all pages
- Extracts text from each page
- Concatenates with newlines
- Returns full document text

#### `chunk_text(text) → list[str]`
Multi-level chunking strategy:

**Level 1: ARTICLE/SECTION Headers**
- Regex: `(ARTICLE|SECTION)[\s—-]*[IVXivx0-9]+`
- Splits document into article sections
- Each article becomes buffer for level 2

**Level 2: Numbered Clauses**
- Regex: `\d+\.\d+\.?\d*` (e.g., 3.14, 3.14.1)
- Splits each article by clause numbers
- Each clause becomes independent chunk

**Level 3: Sliding Window (Fallback)**
- If structured headers not found
- Creates chunks of ~150 words
- Overlaps by 50% for coherence
- Window size: min 50 words, max 300 words

**Constraints:**
- Min chunk: 50 words (minimum meaningful content)
- Max chunk: 1000 words (prevent too-large vectors)
- Target: 150 words (optimal embedding size)

**Example Output:**
```python
[
  "ARTICLE 1 Section 1.1 This agreement...",
  "ARTICLE 1 Section 1.2 Parties agree...",
  "ARTICLE 2 Section 2.1 Confidentiality obligations...",
]
```

---

### 4. **risk_engine.py** - Risk Detection

#### `detect_risk(clause_text) → {risk_level, risk_reason}`

Simple keyword-based detection (can be enhanced):

```python
if "without notice" or "terminate" in text:
  return High: "Employer can terminate without prior notice"

if "penalty" or "liquidated damages" in text:
  return Medium: "Financial penalty imposed"

if "jurisdiction" or "governing law" in text:
  return Low: "Standard legal clause"

else:
  return Low: "No significant legal risk detected"
```

**Returns:**
```json
{
  "risk_level": "High|Medium|Low|Unknown",
  "risk_reason": "Explanation"
}
```

**Future Enhancement:**
- Use LLM to analyze risk factors
- Track financial impact, termination terms, IP ownership
- Generate remediation suggestions

---

### 5. **llm_router.py** - Intelligent LLM Routing

#### `generate_answer(context, question) → str`

Smart fallback strategy:

```
1. Start local LLM (Ollama)
   └─ Set 4 second timeout
   
2. If returns within 4s:
   └─ Success → Return answer
   
3. If timeout or error:
   └─ "Local LLM slow → switching to Gemini"
   └─ Fall back to Gemini API
   
4. Return Gemini response
```

**Why this approach?**
- Local LLM is fast and privacy-preserving (when it works)
- Gemini is reliable fallback (cloud-based)
- Users get response in ~5 seconds max

**Timeout Configuration:**
- Ollama max wait: 4 seconds
- Fallback threshold ensures responsive UI

---

### 6. **gemini_engine.py** - Cloud LLM Integration

#### `generate_gemini_answer(context, question) → str`
- Uses Google Gemini 2.5 Flash model
- Prompt: Answer ONLY from provided legal clause
- Prevents hallucination with strict instructions
- Returns: Generated answer string

#### `generate_gemini_fallback_answer(question) → str`
- For questions NOT in knowledge base
- Generates general legal information
- Adds disclaimer: "This is general Gemini response"
- Includes jurisdiction warning

#### `generate_document_summary(document_text) → str`
- Analyzes full document
- Extracts: parties, purpose, scope, terms, obligations
- Returns: 2-3 paragraph summary
- Used by `/summarize` endpoint

---

### 7. **relevance_reranker.py** - Fine-Tuned Ranking

#### `rerank_candidates(query, candidates) → dict | None`
- Uses fine-tuned BERT model (if available)
- Re-scores top candidates for relevance
- Falls back gracefully if model not found
- Returns best candidate with reranker_score

**Requirements:**
- Model path: `backend/legal-bert-finetune/output/legal-bert-finetuned/`
- Supports GPU acceleration (uses CUDA if available)

---

## Query Processing Pipeline

### Example: "What is liability in employment contracts?"

```
Step 1: Spell Correction
  Input:  "What is liabl in employment contracts?"
  Output: "What is liable in employment contracts?"

Step 2: Legal Reference Check
  Pattern: (section|clause|article) + (number) + (act name)
  Result:  None (no "Section X" pattern found)

Step 3: Exact Question Match (Fuzzy)
  Search: "what is liability in employment contracts?"
  Database: "What is the employee's liability...?"
  Similarity: 0.87 (≥0.85 threshold)
  Result: Match found! Return answer directly

Step 4: If no exact match, proceed to semantic search
  Embed query: Query embedding (384-dim vector)
  FAISS Search: Find top 50 chunks by distance
  Score blend:
    - Embedding similarity: 0.78 confidence
    - Keyword hits: "liability", "employment", "contracts" (+0.08)
    - Source: "legal_qa" (+0.03)
    - Total: 0.78*0.82 + 0.08 + 0.03 = 0.72

Step 5: Confidence Check
  Threshold: 0.30 (MIN_CONFIDENCE_SCORE)
  Result: 0.72 > 0.30 ✓ Proceed

Step 6: LLM Routing
  Route via llm_router:
    - Try Ollama (4s timeout)
    - If slow/error → Use Gemini API

Step 7: Risk Detection
  Clause: "...employee liability limited to..."
  Keywords found: "liability"
  Risk Level: Medium
  Reason: "Financial penalty imposed"

Step 8: Response
  {
    "answer": "Employee liability is...",
    "clause_reference": "Employment Contract, Section 8",
    "confidence_score": 0.72,
    "risk_level": "Medium"
  }
```

---

## Database & Vector Storage

### FAISS Index

**Location:** `backend/vector_db/`

**Files:**
- `legal_qa.index`: FAISS binary index (vectors)
- `legal_qa_chunks.json`: Chunk texts
- `legal_qa_sources.json`: Source labels
- `legal_qa_metadata.json`: Schema version

**Index Type:** IndexFlatL2
- Distance metric: L2 (Euclidean)
- No approximation (exact search)
- Suitable for ≤1M vectors

**Vector Format:**
- Embedding model: Sentence Transformers (all-MiniLM-L6-v2)
- Vector size: 384 dimensions
- Precision: float32

**Performance:**
- Initial load: ~2 seconds
- Query search: ~50ms for 50 candidates
- Index persistence: Serialized to binary format

### User Database

**File:** `backend/local_users.json`

**Format:**
```json
{
  "admin": {
    "salt": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "password_hash": "base64_encoded_pbkdf2_hash"
  },
  "lawyer1": {
    "salt": "...",
    "password_hash": "..."
  }
}
```

**Security:**
- PBKDF2-HMAC-SHA256 (120,000 iterations)
- Per-user random salt (16 bytes)
- Constant-time comparison (prevent timing attacks)
- No plaintext passwords stored

---

## Authentication System

### Token-Based Flow

```
Registration
  ↓
User submits: {username, password}
  ↓
Validate: username unique, password ≥6 chars
  ↓
Generate salt (16 random hex bytes)
  ↓
Hash password: PBKDF2(password, salt)
  ↓
Store in local_users.json
  ↓
Return: success, username

Login
  ↓
User submits: {username, password}
  ↓
Load user from local_users.json
  ↓
Recompute hash: PBKDF2(password, stored_salt)
  ↓
Compare hashes (constant-time)
  ↓
If match:
  Create token payload: {sub, iat, exp}
  Encode payload: Base64(JSON)
  Sign: HMAC-SHA256(payload, secret)
  Return token: payload.signature
  
Token Verification
  ↓
Extract: payload, signature from token.split(".")
  ↓
Verify signature matches
  ↓
Check expiration: exp > now
  ↓
Return: payload or error
```

### Token Structure

**Custom JWT Format** (not standard RFC 7519)

```python
payload = {
  "sub": "username",           # Subject (user)
  "iat": 1771867353,           # Issued at (unix timestamp)
  "exp": 1771870953            # Expiration (unix timestamp)
}

token = base64(json.dumps(payload)) + "." + base64(hmac_signature)
```

**Advantages:**
- Smaller than standard JWT
- No external library dependency
- Secure: HMAC-signed, expiry-checked

**Limitations:**
- Token revocation not supported (no blacklist)
- Single secret for all tokens (no key rotation)
- Can be enhanced to track logout tokens

---

## Error Handling

### Common Error Scenarios

#### 1. Document Upload
```python
Error: File not found in uploads
Handler: Validate file_path exists

Error: PDF corrupted/unreadable
Handler: pdfplumber exception caught, fallback to binary extraction

Error: Chunk size too small
Handler: Filter chunks < 50 words
```

#### 2. Query Processing
```python
Error: Knowledge base not loaded
Handler: Initialize on startup via ensure_default_local_user()

Error: Query embedding fails
Handler: Return fallback (None confidence, trigger Gemini)

Error: FAISS index corruption
Handler: Rebuild from legal_qa.json
```

#### 3. LLM Generation
```python
Error: Ollama timeout (>4s)
Handler: Switch to Gemini automatically

Error: Gemini API rate limit
Handler: Return "Service temporarily unavailable"

Error: No GEMINI_API_KEY set
Handler: Return message instructing user to configure env var
```

#### 4. Authentication
```python
Error: Invalid credentials
Handler: Return 401 "Invalid username or password"

Error: Token expired
Handler: Return 401 "Invalid or expired token"

Error: Malformed token
Handler: Return 400 "Invalid token format"
```

### Response Status Codes

```
200 OK              - Successful operation
400 Bad Request     - Invalid input (empty username, short password)
401 Unauthorized    - Invalid token or credentials
404 Not Found       - No document uploaded for /analyze
500 Server Error    - Unexpected exception
```

---

## Configuration & Environment Variables

### Required Environment Variables
```bash
GEMINI_API_KEY=<your-gemini-api-key>              # Required for cloud LLM
LOCAL_AUTH_SECRET=<your-secret>                   # Token signing secret
LOCAL_AUTH_DEFAULT_USERNAME=admin                 # (default: "admin")
LOCAL_AUTH_DEFAULT_PASSWORD=admin123              # (default: "admin123")
LOCAL_AUTH_TTL_SECONDS=3600                       # Token lifetime seconds
```

### Optional Configuration
```bash
RERANKER_MIN_SCORE=0.5                            # Fine-tuning threshold
OLLAMA_HOST=http://localhost:11434                # Local LLM endpoint
```

### Installation

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
export GEMINI_API_KEY="your-api-key"

# Start backend
python -m uvicorn rag_engine.main:app --app-dir backend --reload
```

---

## Performance Optimization Tips

### 1. FAISS Index Size
- Current: ~66K Q&A pairs from legal_qa.json
- Query time: ~50ms per search
- To optimize large indexes: Use IndexIVF (approximate search)

### 2. Chunk Size Tuning
- Current: 50-1000 words target 150
- Adjust for your documents:
  - Larger chunks (300+ words): Better context, slower search
  - Smaller chunks (50 words): Faster search, less context

### 3. LLM Response Time
- Ollama: 1-3 seconds (depends on model size)
- Gemini: 2-4 seconds (network latency)
- Timeout threshold: 4 seconds balances speed + reliability

### 4. Caching Opportunities
- Cache frequent queries' embeddings
- Pre-compute summaries for large documents
- Memoize legal reference lookups

---

## Future Enhancements

1. **Multi-turn Conversations**
   - Store conversation history
   - Context-aware follow-up questions

2. **Advanced Risk Analysis**
   - Machine learning-based risk scoring
   - Financial impact estimation
   - Remediation recommendations

3. **Document Comparison**
   - Compare two contracts
   - Highlight differences
   - Suggest standardization

4. **Query Logging & Analytics**
   - Track user queries
   - Identify gaps in knowledge base
   - ML-driven content recommendations

5. **Role-Based Access**
   - Admin: View all queries, manage users
   - Lawyer: Annotate clauses, rate answers
   - Client: View-only dashboard

6. **Multi-Language Support**
   - Support Hindi, Tamil, etc.
   - Language-agnostic embeddings

---

## Glossary

- **FAISS**: Facebook AI Similarity Search (vector database)
- **RAG**: Retrieval-Augmented Generation (retrieve + generate)
- **Embeddings**: Dense vector representations of text
- **PBKDF2**: Password-Based Key Derivation Function 2 (hashing)
- **HMAC**: Hash-Based Message Authentication Code (signing)
- **LLM**: Large Language Model
- **Chunking**: Splitting documents into smaller segments
- **Reranking**: Re-scoring candidates with a finer model

---

**Last Updated:** February 24, 2026  
**Version:** 1.0
