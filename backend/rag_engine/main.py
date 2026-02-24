# ==============================================================================
# IMPORTS: Core dependencies for FastAPI, document processing, and RAG system
# ==============================================================================
from fastapi import FastAPI, UploadFile, File  # Web framework and file upload handling
from pydantic import BaseModel  # Data validation using type hints
import re  # Regular expressions for text pattern matching
import shutil  # File operations (copy, move)
from typing import Any  # Type hints for flexible return types

# Import RAG core functions: vector search, chunking, and indexing
from rag_engine.rag_core import (
    retrieve_clause,  # Semantic search + ranking to find relevant clause
    retrieve_candidate_clauses,  # Get top-K candidates from FAISS
    add_chunks,  # Add new chunks to FAISS index
    extract_clause_reference,  # Extract "Section X" from text
    initialize_vector_db_from_legal_qa,  # Load or build initial FAISS index
)
from rag_engine.document_processor import extract_text, chunk_text  # PDF extraction + chunking
from rag_engine.risk_engine import detect_risk  # Keyword-based risk detection
from rag_engine.llm_router import generate_answer  # Route between Ollama/Gemini LLMs
from rag_engine.gemini_engine import generate_gemini_fallback_answer, generate_document_summary  # Gemini API calls
from rag_engine.relevance_reranker import rerank_candidates  # Optional fine-tuned ranking
from rag_engine.auth_local import (  # Local authentication system (no database)
    ensure_default_local_user,  # Create default admin user on first run
    verify_local_login,  # Check username/password against hashed store
    create_login_token,  # Generate signed JWT token
    verify_login_token,  # Validate token signature and expiration
    register_local_user,  # Add new user to local store
)


# ==============================================================================
# FASTAPI APPLICATION INITIALIZATION
# ==============================================================================
# Create FastAPI app instance as the main ASGI application
app = FastAPI(title="Legal AI Chatbot API")

# Global variable to track the most recently uploaded PDF file path
# Used by `/analyze` and `/summarize` endpoints to know which file to process
LATEST_UPLOADED_PATH: str | None = None

# ==============================================================================
# CONSTANTS: Message markers indicating LLM couldn't answer from context
# ==============================================================================
# When LLM returns any of these phrases, it means it couldn't answer from doc
# This triggers fallback to Gemini for general knowledge answer
INSUFFICIENT_ANSWER_MARKERS = [
    "does not contain information",
    "cannot answer this from the provided document",
    "not enough information",
    "insufficient information",
    "not provided in the clause",
    "there is no information",
    "no information",
]


# ==============================================================================
# UTILITY FUNCTION: Check if LLM answer is insufficient
# ==============================================================================
def is_insufficient_answer(answer: str) -> bool:
    """
    Check if LLM answer indicates it couldn't find information in document.
    
    Args:
        answer: The LLM's generated answer text
        
    Returns:
        True if answer contains any "insufficient" marker phrase, False otherwise
        
    Purpose:
        Detect when local LLM/Ollama says "I can't answer from your document"
        so we can fall back to Gemini for general knowledge answer
    """
    # Normalize: convert to lowercase, strip whitespace
    normalized = (answer or "").strip().lower()
    # Return True if ANY marker phrase is found in the answer
    return any(marker in normalized for marker in INSUFFICIENT_ANSWER_MARKERS)



# ==============================================================================
# UTILITY FUNCTION: Extract clause text from wrapped format
# ==============================================================================
def unwrap_retrieved_clause(retrieved_text: str) -> str:
    """
    Extract clause text from 'Question: ... Clause: ...' wrapped format.
    
    Args:
        retrieved_text: Raw text that may be wrapped in Question/Clause format
        
    Returns:
        Just the clause portion if wrapped, full text if not wrapped
        
    Example:
        Input: "Question: What is section 3?\nClause: Section 3 states..."
        Output: "Section 3 states..."
    """
    # Return empty string if input is None or empty
    if not retrieved_text:
        return ""

    # Try to extract using regex pattern: "Clause: <content>" at end of string
    # flags: IGNORECASE (match Clause:, CLAUSE:, etc), DOTALL (. matches newlines)
    match = re.search(r"(?:^|\n)Clause:\s*(.*)$", retrieved_text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        # If pattern found, return just the clause content (group 1)
        return match.group(1).strip()

    # If no Clause: wrapper found, return the full text as-is (already unwrapped)
    return retrieved_text.strip()


# ==============================================================================
# UTILITY FUNCTION: Detect if question is a direct section lookup
# ==============================================================================
def is_direct_section_lookup(question: str) -> bool:
    """
    Check if question is asking for a specific section/clause directly.
    
    Examples:
        "What does section 5 say?" -> True
        "What is clause 3.2?" -> True
        "Are there penalties?" -> False
        
    Purpose:
        For direct lookups, return raw clause text without LLM generation
        This is more accurate than having LLM re-explain the same clause
    """
    # Normalize: convert to lowercase and strip whitespace
    normalized = (question or "").strip().lower()
    # Regex pattern: \b=word boundary, \d+=digits, [a-z]*=optional letters
    # Matches: "what does section 5", "what is clause 3.2", etc.
    return bool(re.search(r"\bwhat\s+does\s+(section|clause)\s+\d+[a-z]*\b", normalized))




# ==============================================================================
# PYDANTIC DATA MODELS: Request/Response validation schemas
# ==============================================================================

class Question(BaseModel):
    """Request body for POST /ask endpoint - user's legal question"""
    query: str  # The question user is asking about the document


class RiskAnalysisSummary(BaseModel):
    """Summary statistics for risk analysis results"""
    total_chunks: int  # Total number of document chunks processed
    risk_sections: int  # Count of chunks with any risk detected
    high_risk: int  # Count of HIGH risk chunks
    medium_risk: int  # Count of MEDIUM risk chunks


class LoginRequest(BaseModel):
    """Request body for POST /auth/login - user credentials"""
    username: str  # Username for authentication
    password: str  # Password (will be hashed server-side)


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register - new user account creation"""
    username: str  # Desired username (must be unique)
    password: str  # Desired password (minimum 6 characters)


class LogoutRequest(BaseModel):
    """Request body for POST /auth/logout - user logout"""
    token: str  # Current bearer token to invalidate




# ==============================================================================
# STARTUP EVENT: Initialize system on application startup
# ==============================================================================
@app.on_event("startup")
async def startup_event():
    """
    FastAPI startup event: runs once when application initializes.
    
    Purpose:
        - Create default admin user if no users exist
        - Load or build FAISS vector index from legal_qa.json
        - Prepare system for first request
    """
    # If no users in store, create default admin/admin123 user
    ensure_default_local_user()
    # Load FAISS index from disk, or build from legal_qa.json if first run
    initialize_vector_db_from_legal_qa()

# ==============================================================================
# ENDPOINT: Health Check
# ==============================================================================
@app.get("/")
def home():
    """
    Simple health check endpoint.
    
    Returns:
        JSON with status message confirming backend is running
        
    Usage:
        curl http://localhost:8000/
    """
    return {"status": "Legal AI Backend Running"}


# ==============================================================================
# ENDPOINT: Login (POST /auth/login)
# ==============================================================================
@app.post("/auth/login")
def login_user(payload: LoginRequest):
    """
    Authenticate user with username/password and return JWT bearer token.
    
    Args:
        payload: LoginRequest with username and password
        
    Returns:
        {status, access_token, token_type, username} on success
        {status, detail} on error
        
    Process:
        1. Strip and validate username/password provided
        2. Check credentials against PBKDF2 hashed store
        3. If valid, generate HMAC-signed token with 1-hour TTL
        4. Return token for use in Authorization header
        
    Example:
        POST /auth/login
        {"username": "admin", "password": "admin123"}
        
        Response:
        {"status": "success", "access_token": "...", "token_type": "bearer"}
    """
    # Normalize username: strip leading/trailing whitespace
    username = payload.username.strip()
    # Get password directly (no strip - whitespace may be intentional)
    password = payload.password

    # Validate: both username and password must be provided
    if not username or not password:
        return {"status": "error", "detail": "Username and password are required."}

    # Verify credentials: hash provided password and compare with stored hash
    # Uses constant-time comparison to prevent timing attacks
    is_valid = verify_local_login(username, password)
    if not is_valid:
        return {"status": "error", "detail": "Invalid username or password."}

    # Credentials valid: generate signed JWT token
    # Token format: base64(payload).base64(hmac_signature)
    # Payload: {sub: username, iat: issue_time, exp: expiration_time}
    token = create_login_token(username)
    return {
        "status": "success",
        "access_token": token,  # Return token for Bearer auth
        "token_type": "bearer",  # Indicates standard Bearer token format
        "username": username,  # Echo back username for confirmation
    }




# ==============================================================================
# ENDPOINT: Register (POST /auth/register)
# ==============================================================================
@app.post("/auth/register")
def register_user(payload: RegisterRequest):
    """
    Register a new user account with username/password.
    
    Args:
        payload: RegisterRequest with desired username and password
        
    Returns:
        {status, detail, username} on success
        {status, detail} on error
        
    Validation:
        - Username must not be empty
        - Password must be at least 6 characters
        - Username must not already exist
        
    Security:
        - Password hashed with PBKDF2-HMAC-SHA256
        - 120,000 iterations with unique 16-byte salt
        - Stored in local_users.json as {username: {salt, password_hash}}
        
    Example:
        POST /auth/register
        {"username": "john", "password": "secure123"}
        
        Response:
        {"status": "success", "detail": "User registered successfully.", "username": "john"}
    """
    # Call registration function with validation and hashing
    success, detail = register_local_user(payload.username, payload.password)
    if not success:
        # Return error if validation failed (empty user, short password, duplicate)
        return {"status": "error", "detail": detail}

    # Registration successful
    return {
        "status": "success",
        "detail": detail,  # Success message from registration function
        "username": payload.username.strip(),  # Echo back normalized username
    }


# ==============================================================================
# ENDPOINT: Verify Token (GET /auth/verify)
# ==============================================================================
@app.get("/auth/verify")
def verify_user_token(token: str):
    """
    Verify if a bearer token is valid and not expired.
    
    Args:
        token: JWT token from query parameter (GET /auth/verify?token=...)
        
    Returns:
        {status, username, expires_at} if valid
        {status, detail} if invalid/expired
        
    Validation:
        - Verify HMAC signature matches (prevents tampering)
        - Check expiration timestamp hasn't passed
        - Extract username from token payload
        
    Purpose:
        Frontend uses this to check if stored token is still valid
        before making requests, avoiding 401 errors
        
    Example:
        GET /auth/verify?token=eyJzdWIiOiJhZG1pbiIsImlhdCI...
        
        Response (valid):
        {"status": "success", "username": "admin", "expires_at": 1711870953}
        
        Response (expired):
        {"status": "error", "detail": "Invalid or expired token."}
    """
    # Verify token: check signature and expiration
    payload = verify_login_token(token)
    if payload is None:
        # Token invalid (tampered, expired, or malformed)
        return {"status": "error", "detail": "Invalid or expired token."}

    # Token valid: return payload information
    return {
        "status": "success",
        "username": payload.get("sub", ""),  # "sub" = subject (username)
        "expires_at": payload.get("exp"),  # "exp" = expiration Unix timestamp
    }


# ==============================================================================
# ENDPOINT: Logout (POST /auth/logout)
# ==============================================================================
@app.post("/auth/logout")
def logout_user(payload: LogoutRequest):
    """
    Logout user by verifying and invalidating token.
    
    Args:
        payload: LogoutRequest with token to invalidate
        
    Returns:
        {status, detail, username} on success
        {status, detail} on error
        
    Note:
        Current implementation doesn't maintain token blacklist
        Token remains technically valid until expiration (1 hour)
        Frontend should delete token from localStorage
        
    Future Enhancement:
        Add Redis/DB-based token blacklist for immediate revocation
        
    Example:
        POST /auth/logout
        {"token": "eyJzdWIiOiJhZG1pbiIsImlhdCI..."}
        
        Response:
        {"status": "success", "detail": "Logged out successfully.", "username": "admin"}
    """
    # Normalize token: strip whitespace
    token = (payload.token or "").strip()
    if not token:
        return {"status": "error", "detail": "Token is required."}

    # Verify token is valid before "logging out"
    verified = verify_login_token(token)
    if verified is None:
        return {"status": "error", "detail": "Invalid or expired token."}

    # Token valid: acknowledge logout
    # Frontend should now delete token from localStorage
    return {
        "status": "success",
        "detail": "Logged out successfully.",
        "username": verified.get("sub", ""),  # Return username for confirmation
    }

# ==============================================================================
# ENDPOINT: Ask Question (POST /ask)
# ==============================================================================
@app.post("/ask")
def ask_question(q: Question):
    """
    Main Q&A endpoint: answer legal questions using RAG pipeline.
    
    Args:
        q: Question object with query string
        
    Returns:
        JSON with:
        - answer: Generated answer text
        - confidence_score: 0.0-1.0 reliability metric
        - clause_reference: Section/clause name or "Not Available"
        - risk_level: High/Medium/Low/Unknown
        - answer_source: retrieval/reranker/gemini_fallback
        
    Processing Pipeline:
        1. Check if direct section lookup ("what is section 5?")
        2. If not direct, try optional fine-tuned reranker
        3. Run main retrieval (legal ref -> exact match -> semantic)
        4. If no match, fall back to Gemini general knowledge
        5. Generate answer via LLM router (Ollama -> Gemini)
        6. Detect risk in retrieved clause
        7. Return comprehensive response
        
    Example:
        POST /ask
        {"query": "What is the employment termination period?"}
        
        Response:
        {"answer": "30 days notice required...", "confidence_score": 0.92, ...}
    """
    # Initialize variables for clause content and metadata
    clause = None  # Will hold retrieved clause text
    confidence = None  # Confidence score from retrieval (0.0-1.0)
    answer_source = "retrieval"  # Track where answer came from
    
    # Check if this is a direct lookup like "What does section 5 say?"
    direct_lookup = is_direct_section_lookup(q.query)

    # If NOT a direct lookup, try optional fine-tuned reranker
    if not direct_lookup:
        # Get top-8 candidates from FAISS semantic search
        candidates = retrieve_candidate_clauses(q.query, top_k=8)
        # Try to rerank using fine-tuned BERT model (if available)
        reranked = rerank_candidates(q.query, candidates)
        if reranked is not None:
            # Reranker succeeded: use reranked clause
            clause = reranked["clause"]
            confidence = reranked["retrieval_confidence"]
            answer_source = "reranker"  # Mark that reranker was used

    # If reranker didn't find anything, run main retrieval
    if clause is None:
        # Main retrieval: 3-tier fallback (legal ref -> exact -> semantic)
        clause, confidence = retrieve_clause(q.query)

    # If no clause found after all retrieval attempts
    if clause is None:
        # No match in knowledge base: fall back to Gemini general knowledge
        try:
            # Generate general legal answer using Gemini API
            fallback_answer = generate_gemini_fallback_answer(q.query)
        except Exception:
            # Even Gemini failed (API key missing, network error, etc.)
            fallback_answer = "I cannot answer this from the provided document, and fallback generation is currently unavailable."

        # Return fallback response with 0.0 confidence
        return {
            "question": q.query,
            "answer": fallback_answer,
            "answer_source": "gemini_fallback",  # Mark as general knowledge
            "clause_reference": "Not Available",  # No clause was found
            "confidence_score": 0.0,  # Zero confidence = not from user's doc
            "risk_level": "Unknown",  # Can't assess risk without clause
            "risk_reason": "No relevant clause found in knowledge base",
        }

    # Clause found! Extract it from "Question: ... Clause: ..." wrapper
    normalized_clause = unwrap_retrieved_clause(clause)

    # Decide how to generate answer
    if direct_lookup and normalized_clause:
        # Direct lookup: return raw clause text (more accurate than LLM paraphrase)
        answer = normalized_clause
        answer_source = "retrieval_direct_clause"
    else:
        # Normal Q&A: generate answer using LLM router
        # Router tries Ollama first (4s timeout), falls back to Gemini
        answer = generate_answer(normalized_clause, q.query)

    # Check if LLM said "I can't answer from the provided context"
    if is_insufficient_answer(answer):
        # LLM couldn't answer from clause - handle based on query type
        if direct_lookup and normalized_clause:
            # Direct lookup: just return the raw clause (user asked for it)
            answer = normalized_clause
            answer_source = "retrieval_direct_clause"
        else:
            # Normal Q&A with insufficient answer: fall back to Gemini
            try:
                fallback_answer = generate_gemini_fallback_answer(q.query)
            except Exception:
                fallback_answer = "I cannot answer this from the provided document, and fallback generation is currently unavailable."

            # Return Gemini fallback response
            return {
                "question": q.query,
                "answer": fallback_answer,
                "answer_source": "gemini_fallback",
                "clause_reference": "Not Available",
                "confidence_score": round(float(confidence or 0.0), 2),
                "risk_level": "Unknown",
                "risk_reason": "Retrieved context was insufficient; switched to Gemini fallback",
            }

    # Answer is good! Now detect risk in the clause
    # Keyword-based risk detection: High/Medium/Low
    risk = detect_risk(normalized_clause)
    
    # Extract section/clause reference for display ("Section 5", etc.)
    clause_ref = extract_clause_reference(clause)

    # Return complete response with answer, confidence, risk, etc.
    return {
        "question": q.query,  # Echo back question
        "answer": answer,  # Generated or raw answer
        "answer_source": answer_source,  # How answer was generated
        "clause_reference": clause_ref,  # Section/clause name
        "confidence_score": round(float(confidence or 0.0), 2),  # 0.0-1.0
        "risk_level": risk["risk_level"],  # High/Medium/Low
        "risk_reason": risk["risk_reason"],  # Why this risk level
    }



# ==============================================================================
# ENDPOINT: Upload Document (POST /upload)
# ==============================================================================
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a PDF document into the vector database.
    
    Args:
        file: PDF file uploaded via multipart/form-data
        
    Returns:
        JSON with:
        - status: Success message
        - chunks_created: Number of chunks generated from PDF
        - chunks_added: Number of NEW chunks added to index (deduped)
        
    Processing Pipeline:
        1. Save uploaded PDF to uploads/ folder
        2. Extract text from all pages using pdfplumber
        3. Chunk text using multi-level strategy (articles -> clauses -> sliding window)
        4. Initialize/load FAISS index
        5. Embed chunks and add to FAISS index (deduplicated)
        6. Persist index to disk
        7. Store file path globally for /analyze and /summarize
        
    Example:
        curl -X POST http://localhost:8000/upload -F "file=@contract.pdf"
        
        Response:
        {"status": "Document uploaded and processed", "chunks_created": 45, "chunks_added": 42}
    """
    # Create file path in uploads/ directory using original filename
    file_path = f"uploads/{file.filename}"

    # Save uploaded file to disk
    # open() creates destination file, shutil.copyfileobj() streams content
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract full text from PDF (all pages combined)
    text = extract_text(file_path)
    
    # Chunk text into semantic segments (50-1000 words each)
    # Uses multi-level strategy: articles -> clauses -> sliding window
    chunks = chunk_text(text)

    # Ensure FAISS index is loaded or initialized
    initialize_vector_db_from_legal_qa()
    
    # Add chunks to FAISS index
    # persist=True: save to disk after adding
    # source="upload": mark these chunks as from uploaded document
    # Returns count of NEW chunks added (duplicates skipped)
    added_count = add_chunks(chunks, persist=True, source="upload")

    # Store file path globally so /analyze and /summarize know which file to use
    global LATEST_UPLOADED_PATH
    LATEST_UPLOADED_PATH = file_path

    # Return success with statistics
    return {
        "status": "Document uploaded and processed",
        "chunks_created": len(chunks),  # Total chunks generated
        "chunks_added": added_count,  # New chunks added (after deduplication)
    }



# ==============================================================================
# ENDPOINT: Analyze Document Risks (GET /analyze)
# ==============================================================================
@app.get("/analyze")
async def analyze_document_risks():
    """
    Analyze the most recently uploaded PDF for legal risks.
    
    Returns:
        JSON with:
        - summary: Statistics (total_chunks, risk_sections, high/medium counts)
        - risk_sections: Array of risky chunks with details
        
    Process:
        1. Check if a document has been uploaded
        2. Extract text from stored PDF path
        3. Chunk text same way as upload
        4. For each chunk, detect risk using keyword matching
        5. Aggregate statistics and return risky sections
        
    Risk Detection:
        - HIGH: "terminate without notice", "unlimited liability"
        - MEDIUM: "penalty", "liquidated damages"
        - LOW: "jurisdiction", "governing law"
        
    Example:
        GET /analyze
        
        Response:
        {
          "status": "Risk analysis completed",
          "summary": {"total_chunks": 45, "risk_sections": 8, "high_risk": 2, "medium_risk": 6},
          "risk_sections": [
            {"section_index": 3, "risk_level": "High", "risk_reason": "...", "section_text": "..."}
          ]
        }
    """
    # Validate that a document has been uploaded
    if not LATEST_UPLOADED_PATH:
        return {
            "status": "No document uploaded",
            "detail": "Upload a PDF using /upload before running /analyze.",
        }

    # Extract text from most recent upload
    text = extract_text(LATEST_UPLOADED_PATH)
    # Chunk the text (same chunking as during upload)
    chunks = chunk_text(text)

    # Initialize risk tracking
    risk_sections: list[dict[str, Any]] = []  # Will hold risky chunks
    high_risk = 0  # Count of HIGH risk chunks
    medium_risk = 0  # Count of MEDIUM risk chunks

    # Scan each chunk for risks
    for idx, chunk in enumerate(chunks, start=1):  # start=1 for human-readable numbering
        # Detect risk using keyword-based detection
        risk = detect_risk(chunk)
        level = risk.get("risk_level", "Unknown")

        # Increment counters for high/medium
        if level == "High":
            high_risk += 1
        elif level == "Medium":
            medium_risk += 1

        # If chunk has any risk, add to results
        if level in {"High", "Medium"}:
            risk_sections.append(
                {
                    "section_index": idx,  # Chunk number
                    "risk_level": level,  # High/Medium/Low
                    "risk_reason": risk.get("risk_reason", ""),  # Why risky
                    "section_text": chunk,  # Full chunk text
                }
            )

    # Create summary statistics using Pydantic model
    summary = RiskAnalysisSummary(
        total_chunks=len(chunks),  # All chunks processed
        risk_sections=len(risk_sections),  # Chunks with risk
        high_risk=high_risk,  # HIGH risk count
        medium_risk=medium_risk,  # MEDIUM risk count
    )

    # Debug: print risks to console
    for item in risk_sections:
        print(f"Risk section {item['section_index']} ({item['risk_level']}): {item['risk_reason']}")

    # Return analysis results
    return {
        "status": "Risk analysis completed",
        "summary": summary.dict(),  # Convert Pydantic to dict
        "risk_sections": risk_sections,  # Full list of risky sections
    }



# ==============================================================================
# ENDPOINT: Summarize Document (GET /summarize)
# ==============================================================================
@app.get("/summarize")
async def summarize_document():
    """
    Generate a brief summary of the most recently uploaded document.
    
    Returns:
        JSON with:
        - status: "success" or "error"
        - summary: 2-3 paragraph summary (if success)
        - detail: Error message (if error)
        
    Process:
        1. Check if document uploaded
        2. Extract full text from PDF
        3. Send to Gemini API for summarization
        4. Return generated summary
        
    Summary Includes:
        - Key parties involved
        - Document type (employment, service agreement, etc.)
        - Main objectives and scope
        - Important terms and conditions
        - Critical obligations
        
    Example:
        GET /summarize
        
        Response:
        {
          "status": "success",
          "summary": "This is an Employment Agreement between XYZ Corp and Employee..."
        }
    """
    # Validate that a document has been uploaded
    if not LATEST_UPLOADED_PATH:
        return {
            "status": "error",
            "detail": "No document uploaded. Upload a PDF using /upload before running /summarize.",
        }

    try:
        # Extract full text from most recently uploaded PDF
        text = extract_text(LATEST_UPLOADED_PATH)
        
        # Validate text was extracted successfully
        if not text or len(text.strip()) == 0:
            return {
                "status": "error",
                "detail": "Document could not be read or is empty.",
            }

        # Generate summary using Gemini API
        # Sends full text, gets back 2-3 paragraph summary
        summary = generate_document_summary(text)
        
        # Return successful summary
        return {
            "status": "success",
            "summary": summary,
        }
    except Exception as e:
        # Handle errors (API key missing, network error, etc.)
        return {
            "status": "error",
            "detail": f"Failed to generate summary: {str(e)}",
        }
