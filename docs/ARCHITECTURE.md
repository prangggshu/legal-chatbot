# Architecture & Design Decisions

Deep dive into the architectural choices, design patterns, and rationale behind the Legal AI Chatbot.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Key Design Decisions](#key-design-decisions)
3. [Data Flow Architecture](#data-flow-architecture)
4. [Technology Stack Justification](#technology-stack-justification)
5. [Scalability & Performance](#scalability--performance)
6. [Security Architecture](#security-architecture)
7. [Error Handling Strategy](#error-handling-strategy)
8. [Future Evolution](#future-evolution)

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React + Vite)                    │
│  - Authentication UI (Login/Register)                           │
│  - Chat Interface (Ask/Answer)                                  │
│  - Document Management (Upload/Analyze/Summarize)              │
│  - Session Management (localStorage tokens)                     │
└──────────────────────────────────┬──────────────────────────────┘
                                   │ HTTP/REST (CORS enabled)
                                   ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                     │
│  ┌───────────────────────────────────────────────────────┐      │
│  │               Authentication Layer                     │      │
│  │  - PBKDF2 password hashing                            │      │
│  │  - HMAC token signing                                 │      │
│  │  - Local user JSON store                              │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │               Document Processing                      │      │
│  │  - PDF text extraction (pdfplumber)                   │      │
│  │  - Multi-level intelligent chunking                   │      │
│  │  - Embedding generation                               │      │
│  │  - Vector index management                            │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │             Query Processing Pipeline                  │      │
│  │  - Spell correction & synonym expansion               │      │
│  │  - Legal reference extraction                         │      │
│  │  - FAISS semantic search                              │      │
│  │  - Multi-tier ranking and scoring                     │      │
│  │  - Risk detection                                      │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │              LLM Routing & Generation                  │      │
│  │  - Ollama (4s timeout) → Gemini fallback              │      │
│  │  - Context-aware prompt engineering                   │      │
│  │  - Hallucination prevention                           │      │
│  └───────────────────────────────────────────────────────┘      │
└──────────────┬──────────────────────────────┬──────────────────┘
               │                              │
        ┌──────↓──────┐              ┌────────↓─────────┐
        │  FAISS Index│              │  Gemini API      │
        │  (Local)    │              │  (Google Cloud)  │
        └─────────────┘              └──────────────────┘
               ↓                              ↓
        ┌──────────────┐              ┌────────────────┐
        │  Embeddings  │              │  LLM Generation│
        │  384-dims    │              │  gemini-2.5    │
        └──────────────┘              └────────────────┘
               ↑
        ┌──────────────┐
        │ Sentence     │
        │ Transformers │
        │ (all-MiniLM  │
        │  -L6-v2)     │
        └──────────────┘
```

### Component Interactions

```
User Request
    ↓
API Endpoint (FastAPI)
    ├─ Auth validation (HMAC token check)
    ├─ Document upload/processing
    ├─ Query routing through pipeline
    │   ├─ Spell correction
    │   ├─ Synonym expansion
    │   ├─ Legal reference extraction
    │   ├─ FAISS search for semantic matches
    │   └─ Risk scoring
    ├─ LLM routing (Ollama or Gemini)
    ├─ Response generation
    ├─ Risk detection on returned clause
    └─ JSON response to frontend
```

---

## Key Design Decisions

### 1. Vector Search (FAISS) Over Database Query

**Decision**: Use FAISS + Sentence Transformers instead of SQL database with full-text search.

**Rationale**:
- **Semantic Understanding**: Captures meaning, not just keywords
  - Query "What are the penalties?" matches "Liquidated damages clause"
  - Query "secrecy" matches "confidentiality"
- **Performance**: ~100ms search vs 500ms+ SQL query
- **No Schema Migration**: Handles unstructured legal text naturally
- **Local Storage**: Works offline, no network dependency
- **Cost**: Free (local model) vs expensive cloud AI services
- **Interpretability**: Clear similarity scores (0.0-1.0)

**Trade-offs**:
- ❌ Can't do complex SQL joins (documents one-at-a-time)
- ❌ Large index takes disk space (~500MB per 100K chunks)
- ✅ But: Semantic search superior for legal domain

---

### 2. Local Authentication (No External Database)

**Decision**: PBKDF2 + HMAC tokens stored in local JSON, not requiring external DB or OAuth.

**Rationale**:
- **Simplicity**: No infrastructure dependency (no PostgreSQL, MongoDB)
- **Privacy**: Passwords never leave local environment
- **Development Speed**: Implement auth in <200 lines
- **Offline Capability**: Works without internet
- **PBKDF2 Strength**: 120K iterations + per-user salt prevents rainbow tables

**Security Trade-offs**:
- ✅ Passwords hashed with strong algorithms
- ✅ Tokens signed with HMAC-SHA256
- ❌ No token revocation (can't logout users from backend)
- ❌ No role-based access yet
- ↔️ Single-user-per-session model

**When to Upgrade**:
- Multi-tenant system needed → Add PostgreSQL
- Enterprise SSO required → Add OAuth2/OIDC
- User revocation critical → Add token blacklist

---

### 3. Multi-Level Document Chunking

**Decision**: Articles → Clauses → Sliding Window (vs simple paragraph splitting)

**Rationale**:
- **Articles as Context**: "Article 2 - Compensation" preserves legal structure
- **Clauses as Units**: "3.14" splits at semantic boundaries (not arbitrary lines)
- **Sliding Window Fallback**: Captures content when no structural markers
- **Word Constraints**: 50-word minimum prevents fragments, 1000-word max prevents overload
- **150-word Target**: Balances specificity (not too general) with coverage (not duplicative)

**Example Chunking**:
```
Raw Document (5000 words)
    ↓ (Split by ARTICLE headers)
Article 1 (1200w) | Article 2 (1300w) | Article 3 (2500w)
    ↓ (Split by numbered clauses within each)
1.1 (400w) | 1.2 (350w) | 1.3 (450w) | 2.1 (600w) | ...
    ↓ (Sliding window if no clauses found)
[Sent 0-50] | [Sent 25-75] | [Sent 50-100] | ... (50% overlap)
    ↓ (Enforce word constraints)
50-1000 words per chunk (target 150)
    ↓ (Embed and index)
45 semantic chunks ready for search
```

**Benefits**:
- Preserves legal structure (articles/clauses matter in law)
- Semantic coherence (related terms together)
- No orphan fragments
- Efficient FAISS indexing (45 chunks vs 1000+ paragraphs)

---

### 4. Query Processing Pipeline (3-Tier Fallback)

**Decision**: Legal Ref → Exact Match → Semantic Search → LLM Fallback

**Rationale**:
- **Tier 1 (Legal Reference)**: Direct pattern match for "Section X of Act Y"
  - Fastest (regex lookup, <10ms)
  - Most accurate (user knows exact reference)
- **Tier 2 (Exact Question)**: Fuzzy match (85% similarity) with cached questions
  - Medium speed (~100ms)
  - Handles typos, paraphrasing
- **Tier 3 (Semantic)**: FAISS cosine search if Tiers 1-2 fail
  - Slower (~1s)
  - Most flexible (understanding, not keywords)
- **Tier 4 (LLM)**: Gemini generation if no KB match
  - Slowest (~5s)
  - Fallback to general knowledge

**Pipeline Example**:
```
Query: "What is section 1 of aadhaar act?"
    ↓
Tier 1: Legal Reference Match
  - Extract: section="1", act="aadhaar"
  - Search KB for chunks containing "Section 1" AND "Aadhaar"
  - ✅ Found! → Return immediately (skip Tiers 2-4)
    
Query: "What about termination?" (vs stored "What is termination clause?")
    ↓
Tier 1: Legal Reference Match
  - No pattern match → Continue
    ↓
Tier 2: Exact Question Match
  - Fuzzy match: "termination" vs "termination clause" = 88% similar
  - ✅ Match found! → Return (skip Tiers 3-4)

Query: "penalties if I break" (novel phrasing)
    ↓
Tiers 1-2: No matches
    ↓
Tier 3: Semantic Search
  - Embed query, find nearest neighbors in FAISS
  - ✅ Found "liquidated damages" as semantic neighbor
  - Confidence 0.78

Query: "How do quantum computers work?"
    ↓
Tiers 1-4: No relevant legal content
    ↓
Tier 4: LLM Fallback
  - Gemini generates general knowledge answer
  - Mark response as "gemini_fallback", confidence 0.0
```

---

### 5. Scoring Formula: 82% Semantic + 15% Keyword + 3% Source

**Decision**: Weighted combination of three signals.

**Formula**:
```
combined_score = (0.82 × embedding_similarity) 
               + (0.15 × keyword_boost)     # 0.0-0.15 max
               + (0.03 × source_bonus)      # 0.0-0.03 if "upload"
```

**Rationale**:
- **Semantic Dominance (82%)**: Paraphrasing should match
  - "What are penalties?" ≈ "Liquidated damages" (both about money)
- **Keyword Boost (15% max)**: Exact word matches matter
  - Query "termination" + text "termination" gets boost
  - Prevents low-semantic-score but keyword-perfect matches
- **Source Bonus (3%)**: Prefer uploaded documents over training data
  - User's contract supersedes general legal knowledge
  - Small bonus only (0.03) to not distort semantic scores

**Example Scoring**:
```
Document A:
  - Embedding similarity: 0.88
  - Keyword match: Yes (boost +0.12)
  - Source: "upload" (boost +0.03)
  - Final: (0.82 × 0.88) + 0.12 + 0.03 = 0.8616 ✅ Ranked #1

Document B:
  - Embedding similarity: 0.95
  - Keyword match: No (boost +0.00)
  - Source: "training_data" (no boost)
  - Final: (0.82 × 0.95) + 0.00 + 0.00 = 0.779 ✅ Ranked #2
```

**Why not 50/50 semantic/keyword?**
- Legal language is specific (synonyms are rare)
- Paraphrasing is common in user questions
- Over-weighting keywords misses "liability" vs "responsible"

---

### 6. Ollama (Local) → Gemini (Cloud) Fallback

**Decision**: Try Ollama first with 4-second timeout, fall back to Gemini if needed.

**Rationale**:
- **Privacy + Speed**: Ollama llama3 runs locally
  - ~1-2 second responses
  - No personal data sent to cloud
- **Robustness**: If Ollama slow/unavailable, cloud fallback ensures availability
  - 4-second timeout chosen:
    - < 2s: Ollama loads next-tokens naturally
    - 4s: Ollama on slow machine has chance
    - > 4s: User perceived as hanging
- **Cost**: Gemini API cheap for usage-based ($0.0001/prompt)
- **Fallback Quality**: Gemini 2.5 Flash is excellent if needed

**Decision Tree**:
```
Ask question
    ↓
Try Ollama on localhost:11434
    ├─ Success in < 4s? → Use Ollama answer
    ├─ Timeout (> 4s)? → Mark as fallback to Gemini
    ├─ Connection refused? → Fallback to Gemini
    └─ Gemini generates answer
```

---

### 7. Embedding Model: Sentence Transformers (all-MiniLM-L6-v2)

**Decision**: Use all-MiniLM-L6-v2 (384-dim) vs larger models.

**Rationale**:
- **Speed**: ~50ms per chunk vs 200ms for larger models
- **Quality**: 384-dims captures legal semantics well
  - Legal documents highly structured (not ambiguous)
  - Smaller dims sufficient
- **Memory**: ~500MB RAM vs 2GB for larger models
- **Local Loading**: No API key, instant availability
- **Proven Legal Domain**: Used successfully in legal-BERT literature

**vs Alternatives**:
- ❌ BM25 (keyword): Misses paraphrasing ("penalties" vs "damages")
- ❌ OpenAI embeddings: Privacy, cost, API availability
- ✅ all-MiniLM: Local, fast, accurate, proven

---

### 8. Risk Detection: Keyword-Based (Future: ML)

**Current (v1)**:
- Simple keyword matching: "terminate without notice" → High Risk
- Hardcoded patterns, ~80% accuracy

**Future (v2)**:
- ML classifier trained on legal risk annotations
- Expected: ~95% accuracy
- Would replace keyword detection

**Why Simple Pattern First**:
- Interpretability: User sees exactly why something is risky
- Speed: No model loading
- Accuracy: 80% acceptable for MVP
- Easy to update rules

---

## Data Flow Architecture

### Document Upload Flow

```
User selects PDF
    ↓
POST /upload
    ↓
FastAPI receives file
    ├─ Validate: Is it a PDF?
    ├─ Store: Save to uploads/
    ├─ Extract: pdfplumber reads all pages
    │   └─ Combine into single text (remove page breaks)
    ├─ Chunk: Multi-level splitting
    │   ├─ Step 1: Split by ARTICLE headers
    │   ├─ Step 2: Split by numbered clauses
    │   └─ Step 3: Sliding window for remaining
    ├─ Embed: Sentence Transformers
    │   └─ 384-dim vectors for each chunk
    ├─ Index: Add to FAISS index
    │   ├─ Update index.pickle
    │   ├─ Update metadata
    │   └─ Persist to /vector_db/
    └─ Respond: {chunks_created: 45, chunks_added: 42}

FAISS Index State:
  - /vector_db/legal_qa.index (FAISS binary)
  - /vector_db/legal_qa_chunks.json (chunk texts)
  - /vector_db/legal_qa_metadata.json (source labels)
  - /vector_db/legal_qa_sources.json (file sources)
```

### Question Processing Flow

```
User types: "What is clause 3.2?"
    ↓
POST /ask {query}
    ↓
Query Processing Pipeline:
    ├─ Spell Correction
    │   └─ Check for typos (liabl→liable)
    ├─ Synonym Expansion
    │   └─ "penalties" → ["penalties", "damages", "fines"]
    ├─ Legal Reference Extraction
    │   ├─ Pattern: "clause|section|article" + number + "of" + act
    │   └─ Extract: clause=3.2, act=None
    ├─ Tier 1: Direct Legal Reference Match
    │   ├─ Search KB: contains "3.2" AND context
    │   └─ If found: Return with high confidence
    ├─ Tier 2: Exact Question Match
    │   ├─ Fuzzy search: historical questions
    │   └─ If 85%+ similar: Return cached answer
    ├─ Tier 3: Semantic Search (FAISS)
    │   ├─ Embed query (384-dim vector)
    │   ├─ Search: Find top-K nearest neighbors
    │   ├─ Rank: Apply scoring formula
    │   └─ Threshold: confidence > 0.30?
    │       ├─ Yes → Use top result
    │       └─ No → Continue to Tier 4
    └─ Tier 4: LLM Generation
        ├─ Try Ollama (4s timeout)
        │   └─ Success → Use answer
        ├─ If timeout/error → Try Gemini
        │   └─ Generate general knowledge
        └─ Mark as "gemini_fallback"

Retrieved Clause Processing:
    ├─ Extract text from winning chunk
    ├─ Risk detection: Scan for keywords
    │   ├─ High: "terminate", "without notice"
    │   ├─ Medium: "penalty", "liquidated"
    │   └─ Low: "jurisdiction", "governing"
    ├─ Generate answer via LLM
    │   └─ Prompt: "Answer ONLY from provided context"
    └─ Compose response JSON

Response to Frontend:
{
  "question": "What is clause 3.2?",
  "answer": "Clause 3.2 states...",
  "confidence_score": 0.92,
  "clause_reference": "Section 3.2",
  "risk_level": "High",
  "answer_source": "retrieval"
}
```

### Risk Analysis Flow

```
User clicks "Analyze"
    ↓
GET /analyze
    ↓
Load FAISS Index
    ├─ Read saved index from /vector_db/
    ├─ Load embeddings into memory
    └─ Load chunk texts
    
Scan All Chunks:
    ├─ For each chunk:
    │   ├─ Check for risk keywords
    │   │   ├─ High: "terminate", "without notice", "liable"
    │   │   ├─ Medium: "penalty", "damages", "breach"
    │   │   └─ Low: "jurisdiction", "law"
    │   └─ If risk found: Add to results
    ├─ Aggregate:
    │   ├─ Total chunks: 45
    │   ├─ Risk chunks: 8
    │   ├─ High risk: 2
    │   ├─ Medium risk: 6
    │   └─ Low risk: 0
    └─ Sort by risk level
    
Response:
{
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
      "risk_reason": "Termination without notice",
      "section_text": "..."
    },
    ...
  ]
}
```

---

## Technology Stack Justification

### Backend: FastAPI

**Why FastAPI over Django/Flask**:
- ✅ Async/await (fast, concurrent requests)
- ✅ Automatic OpenAPI docs
- ✅ Type hints (editor autocomplete, validation)
- ✅ Lightweight (no ORM overhead)
- ❌ Smaller ecosystem vs Django
- ✅ Perfect for microservice/RAG patterns

### Vector DB: FAISS

**Why FAISS over Pinecone/Weaviate**:
- ✅ Local (no API, privacy)
- ✅ Free (no subscription)
- ✅ Fast (~100ms searches)
- ✅ Works offline
- ❌ No automatic backups
- ✅ Good enough for <1M documents

**When to upgrade**:
- > 10M documents → Elasticsearch
- Managed hosting needed → Pinecone/Weaviate
- Distributed search → Milvus

### Frontend: React + Vite

**Why React**:
- ✅ Large ecosystem (components, libraries)
- ✅ TypeScript integration
- ✅ Responsive UI for chat
- ✅ State management (Redux-lite patterns)

**Why Vite over Create React App**:
- ✅ Fast dev server (instant HMR)
- ✅ Smaller production build
- ✅ Modern build system
- ✅ Integrated TypeScript support

### LLM: Ollama + Gemini

**Why Ollama locally**:
- ✅ Privacy (no API calls for basic answers)
- ✅ Speed (~1-2 seconds)
- ✅ Free (llama3 is open)
- ✅ Works offline

**Why Gemini as fallback**:
- ✅ Expensive queries infrequent (only when KB fails)
- ✅ Excellent quality (best in class)
- ✅ API stability
- ✅ Cheap per-token pricing

---

## Scalability & Performance

### Horizontal Scaling Plan

```
Current (v1):
  Single backend instance (localhost)
  Single frontend instance (localhost)
  Suitable for: 1-10 users local testing

v1.5 (Multiple Users - Local Network):
  Backend → Gunicorn workers (4-8)
  FAISS index shared via /vector_db/
  Suitable for: 2-20 concurrent users

v2 (Cloud):
  Kubernetes deployment
  Multiple backend pods
  Distributed FAISS (Mlivus)
  Database: PostgreSQL for auth/history
  Cache: Redis for sessions
  Suitable for: 100+ concurrent users

v3 (Enterprise):
  Multi-tenant architecture
  Separate FAISS per user/org
  Advanced ACLs
  Audit logging
  Suitable for: 1000+ users, SaaS
```

### Performance Metrics (Current)

| Operation | Latency | Bottleneck |
|-----------|---------|-----------|
| Login | 50ms | Password hashing (PBKDF2) |
| Upload (10MB PDF) | 10s | PDF extraction + embedding |
| Ask (cached) | 100ms | FAISS search |
| Ask (semantic) | 1.5s | FAISS + LLM prompt |
| Ask (LLM) | 5s | Gemini generation |
| Analyze | 5s | Keyword scan all chunks |
| Summarize | 7s | Gemini generation |

### Optimization Opportunities

1. **Caching**
   - Cache embeddings (avoid re-compute)
   - Cache similar questions
   - Cache LLM responses

2. **Batching**
   - Batch embedding generation
   - Batch LLM calls

3. **Async Processing**
   - Long-running tasks (upload) as background jobs
   - Webhook notifications when complete

4. **Indexing**
   - Hash-based quick lookup for legal references
   - Inverted index for keyword search

---

## Security Architecture

### Authentication & Authorization

```
Credentials Stored:
  /backend/local_users.json (plaintext NOT PASSWORD!)
  {
    "alice": {
      "salt": "base64_encoded_salt",
      "password_hash": "base64_encoded_pbkdf2_hash"
    }
  }

Login Flow:
  1. User submits username + password
  2. Backend loads salt from local_users.json
  3. Hash submitted password with salt: PBKDF2(password, salt, 120K)
  4. Compare hash with stored hash (constant-time)
  5. If match: Generate token

Token Format:
  payload = {sub: username, iat: timestamp, exp: timestamp}
  signature = HMAC-SHA256(payload, SECRET_KEY)
  token = base64(payload) + "." + base64(signature)

Token Validation:
  1. Parse token (split on ".")
  2. Verify signature with stored SECRET_KEY
  3. Check expiration (iat + 1hour > now)
  4. Return username if valid
```

### Data Privacy

**At Rest**:
- ✅ User credentials: Hashed with PBKDF2
- ✅ Documents: Stored locally, only processed in memory
- ⚠️ Tokens: Stored in browser localStorage (XSS vulnerable)

**In Transit**:
- ⚠️ HTTP only (should be HTTPS in production)
- ⚠️ CORS allows any origin (should restrict)

**In Process**:
- ✅ Documents: Loaded, processed, released
- ✅ No long-term storage of document contents
- ✅ Embeddings: Only vectors stored (not original text unless indexed)

### Production Security Recommendations

```
1. HTTPS/TLS
   - All API calls encrypted
   - Prevent token interception

2. CORS
   - Restrict to known frontend origins
   - Prevent POST from arbitrary domains

3. Rate Limiting
   - Prevent brute force attacks
   - 10 requests/min per IP on /auth/login

4. HTTPS + HSTS
   - Force HTTPS-only connections
   - Prevent MITM attacks

5. Input Validation
   - Validate PDF uploads
   - Sanitize query strings

6. Secrets Management
   - Environment variables for API keys
   - Never commit secrets to git
   - Rotate SECRET_KEY regularly

7. Logging & Monitoring
   - Audit log authentication attempts
   - Alert on suspicious patterns
   - No password logging

8. Database
   - If scaling: Use PostgreSQL
   - Enable SSL connections
   - Regular backups
```

---

## Error Handling Strategy

### Error Categories

```
1. User Input Errors (400)
   - Invalid JSON: {"status": "error", "detail": "JSON decode error"}
   - Missing fields: {"status": "error", "detail": "missing: 'query'"}
   - Type mismatch: {"status": "error", "detail": "username must be string"}

2. Authentication Errors (401)
   - Wrong password: {"status": "error", "detail": "Invalid username or password"}
   - Expired token: {"status": "error", "detail": "Invalid or expired token"}
   - Missing credentials: {"status": "error", "detail": "No token provided"}

3. Resource Errors (404)
   - No document: {"status": "No document uploaded", "detail": "Upload before asking"}
   - Missing file: {"status": "error", "detail": "File not found"}

4. Server Errors (500)
   - Exception in code: {"status": "error", "detail": "Internal server error"}
   - API key missing: {"status": "error", "detail": "GEMINI_API_KEY not configured"}
   - OOM: {"status": "error", "detail": "Out of memory"}
```

### Error Recovery Strategies

```
LLM Timeout:
  Try Ollama (4s)
    → No response → Use Gemini
    → Still no response → Return cached answer or user-friendly message

FAISS Index Corrupted:
  → Rebuild from chunks
  → Fallback to keyword search if rebuilding fails

Missing API Key:
  → Display friendly error
  → Log with timestamp
  → Suggest configuration

Upload Extraction Fails (corrupted PDF):
  → Return 400 with specific error
  → Suggest user re-upload
  → Log error type
```

---

## Future Evolution

### Short Term (3 months)

1. **Token Revocation**
   - Add token blacklist
   - Implement logout on backend

2. **Advanced Risk Scoring**
   - Train ML model on annotated clauses
   - Replace keyword detection

3. **Multi-Document Search**
   - Allow uploading 2+ documents
   - Search across all simultaneously

4. **Export Features**
   - Export to PDF (Q&As + risk analysis)
   - Export to CSV (risk summary)

### Medium Term (6 months)

1. **Role-Based Access**
   - Admin vs Lawyer vs Client roles
   - Different permissions per role

2. **Batch Processing**
   - Upload 100 documents at once
   - Generate reports en masse

3. **Conversation History**
   - Persist Q&As to database
   - Search past conversations

4. **Custom Risk Rules**
   - Allow users to define risk keywords
   - Personalized risk detection

### Long Term (1 year)

1. **Collaborative Annotations**
   - Multiple lawyers annotate clauses
   - Collective knowledge base

2. **Fine-Tuned LLM**
   - Train private legal LLM
   - Better domain accuracy

3. **SaaS Multi-Tenant**
   - Cloud deployment
   - Subscription model

4. **Mobile App**
   - iOS/Android client
   - On-device embedding

---

**Architecture V1 Completed**: March 2024  
**Next Review**: June 2024  
**Maintainers**: Development Team
