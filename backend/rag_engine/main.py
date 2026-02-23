from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import re
import shutil
from typing import Any
from rag_engine.rag_core import (
    retrieve_clause,
    retrieve_candidate_clauses,
    add_chunks,
    extract_clause_reference,
    initialize_vector_db_from_legal_qa,
)
from rag_engine.document_processor import extract_text, chunk_text
from rag_engine.risk_engine import detect_risk
from rag_engine.llm_router import generate_answer
from rag_engine.gemini_engine import generate_gemini_fallback_answer
from rag_engine.relevance_reranker import rerank_candidates
from rag_engine.auth_local import (
    ensure_default_local_user,
    verify_local_login,
    create_login_token,
    verify_login_token,
    register_local_user,
)


app = FastAPI(title="Legal AI Chatbot API")
LATEST_UPLOADED_PATH: str | None = None

INSUFFICIENT_ANSWER_MARKERS = [
    "does not contain information",
    "cannot answer this from the provided document",
    "not enough information",
    "insufficient information",
    "not provided in the clause",
    "there is no information",
    "no information",
]


def is_insufficient_answer(answer: str) -> bool:
    normalized = (answer or "").strip().lower()
    return any(marker in normalized for marker in INSUFFICIENT_ANSWER_MARKERS)


def unwrap_retrieved_clause(retrieved_text: str) -> str:
    if not retrieved_text:
        return ""

    match = re.search(r"(?:^|\n)Clause:\s*(.*)$", retrieved_text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    return retrieved_text.strip()


def is_direct_section_lookup(question: str) -> bool:
    normalized = (question or "").strip().lower()
    return bool(re.search(r"\bwhat\s+does\s+(section|clause)\s+\d+[a-z]*\b", normalized))


class Question(BaseModel):
    query: str


class RiskAnalysisSummary(BaseModel):
    total_chunks: int
    risk_sections: int
    high_risk: int
    medium_risk: int


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class LogoutRequest(BaseModel):
    token: str


@app.on_event("startup")
async def startup_event():
    """Load persistent FAISS index or build from legal_qa.json on first run."""
    ensure_default_local_user()
    initialize_vector_db_from_legal_qa()

@app.get("/")
def home():
    return {"status": "Legal AI Backend Running"}


@app.post("/auth/login")
def login_user(payload: LoginRequest):
    username = payload.username.strip()
    password = payload.password

    if not username or not password:
        return {"status": "error", "detail": "Username and password are required."}

    is_valid = verify_local_login(username, password)
    if not is_valid:
        return {"status": "error", "detail": "Invalid username or password."}

    token = create_login_token(username)
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "username": username,
    }


@app.post("/auth/register")
def register_user(payload: RegisterRequest):
    success, detail = register_local_user(payload.username, payload.password)
    if not success:
        return {"status": "error", "detail": detail}

    return {
        "status": "success",
        "detail": detail,
        "username": payload.username.strip(),
    }


@app.get("/auth/verify")
def verify_user_token(token: str):
    payload = verify_login_token(token)
    if payload is None:
        return {"status": "error", "detail": "Invalid or expired token."}

    return {
        "status": "success",
        "username": payload.get("sub", ""),
        "expires_at": payload.get("exp"),
    }


@app.post("/auth/logout")
def logout_user(payload: LogoutRequest):
    token = (payload.token or "").strip()
    if not token:
        return {"status": "error", "detail": "Token is required."}

    verified = verify_login_token(token)
    if verified is None:
        return {"status": "error", "detail": "Invalid or expired token."}

    return {
        "status": "success",
        "detail": "Logged out successfully.",
        "username": verified.get("sub", ""),
    }

@app.post("/ask")
def ask_question(q: Question):
    clause = None
    confidence = None
    answer_source = "retrieval"
    direct_lookup = is_direct_section_lookup(q.query)

    if not direct_lookup:
        candidates = retrieve_candidate_clauses(q.query, top_k=8)
        reranked = rerank_candidates(q.query, candidates)
        if reranked is not None:
            clause = reranked["clause"]
            confidence = reranked["retrieval_confidence"]
            answer_source = "reranker"

    if clause is None:
        clause, confidence = retrieve_clause(q.query)

    if clause is None:
        try:
            fallback_answer = generate_gemini_fallback_answer(q.query)
        except Exception:
            fallback_answer = "I cannot answer this from the provided document, and fallback generation is currently unavailable."

        return {
            "question": q.query,
            "answer": fallback_answer,
            "answer_source": "gemini_fallback",
            "clause_reference": "Not Available",
            "confidence_score": 0.0,
            "risk_level": "Unknown",
            "risk_reason": "No relevant clause found in knowledge base",
        }

    normalized_clause = unwrap_retrieved_clause(clause)

    if direct_lookup and normalized_clause:
        answer = normalized_clause
        answer_source = "retrieval_direct_clause"
    else:
        answer = generate_answer(normalized_clause, q.query)

    if is_insufficient_answer(answer):
        if direct_lookup and normalized_clause:
            answer = normalized_clause
            answer_source = "retrieval_direct_clause"
        else:
            try:
                fallback_answer = generate_gemini_fallback_answer(q.query)
            except Exception:
                fallback_answer = "I cannot answer this from the provided document, and fallback generation is currently unavailable."

            return {
                "question": q.query,
                "answer": fallback_answer,
                "answer_source": "gemini_fallback",
                "clause_reference": "Not Available",
                "confidence_score": round(float(confidence or 0.0), 2),
                "risk_level": "Unknown",
                "risk_reason": "Retrieved context was insufficient; switched to Gemini fallback",
            }

    risk = detect_risk(normalized_clause)
    clause_ref = extract_clause_reference(clause)

    return {
        "question": q.query,
        "answer": answer,
        "answer_source": answer_source,
        "clause_reference": clause_ref,
        "confidence_score": round(float(confidence or 0.0), 2),
        "risk_level": risk["risk_level"],
        "risk_reason": risk["risk_reason"],
    }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text(file_path)
    chunks = chunk_text(text)

    initialize_vector_db_from_legal_qa()
    added_count = add_chunks(chunks, persist=True, source="upload")

    global LATEST_UPLOADED_PATH
    LATEST_UPLOADED_PATH = file_path

    return {
        "status": "Document uploaded and processed",
        "chunks_created": len(chunks),
        "chunks_added": added_count,
    }


@app.get("/analyze")
async def analyze_document_risks():
    """Analyze risks for the most recently uploaded PDF; no request body expected."""
    if not LATEST_UPLOADED_PATH:
        return {
            "status": "No document uploaded",
            "detail": "Upload a PDF using /upload before running /analyze.",
        }

    text = extract_text(LATEST_UPLOADED_PATH)
    chunks = chunk_text(text)

    risk_sections: list[dict[str, Any]] = []
    high_risk = 0
    medium_risk = 0

    for idx, chunk in enumerate(chunks, start=1):
        risk = detect_risk(chunk)
        level = risk.get("risk_level", "Unknown")

        if level == "High":
            high_risk += 1
        elif level == "Medium":
            medium_risk += 1

        if level in {"High", "Medium"}:
            risk_sections.append(
                {
                    "section_index": idx,
                    "risk_level": level,
                    "risk_reason": risk.get("risk_reason", ""),
                    "section_text": chunk,
                }
            )

    summary = RiskAnalysisSummary(
        total_chunks=len(chunks),
        risk_sections=len(risk_sections),
        high_risk=high_risk,
        medium_risk=medium_risk,
    )

    for item in risk_sections:
        print(f"Risk section {item['section_index']} ({item['risk_level']}): {item['risk_reason']}")

    return {
        "status": "Risk analysis completed",
        "summary": summary.dict(),
        "risk_sections": risk_sections,
    }
