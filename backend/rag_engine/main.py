from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import shutil
from rag_engine.rag_core import retrieve_clause, retrieve_candidate_clauses, add_chunks, extract_clause_reference, initialize_vector_db_from_legal_qa
from rag_engine.document_processor import extract_text, chunk_text
from rag_engine.risk_engine import detect_risk
from rag_engine.llm_router import generate_answer
from rag_engine.gemini_engine import generate_gemini_fallback_answer
from rag_engine.relevance_reranker import rerank_candidates


app = FastAPI(title="Legal AI Chatbot API")

INSUFFICIENT_ANSWER_MARKERS = [
    "does not contain information",
    "cannot answer this from the provided document",
    "not enough information",
    "insufficient information",
    "not provided in the clause",
]


def is_insufficient_answer(answer: str) -> bool:
    normalized = (answer or "").strip().lower()
    return any(marker in normalized for marker in INSUFFICIENT_ANSWER_MARKERS)

class Question(BaseModel):
    query: str

@app.on_event("startup")
async def startup_event():
    """Load persistent FAISS index or build from legal_qa.json on first run."""
    initialize_vector_db_from_legal_qa()

@app.get("/")
def home():
    return {"status": "Legal AI Backend Running"}

@app.post("/ask")
def ask_question(q: Question):
    clause = None
    confidence = None
    answer_source = "retrieval"

    candidates = retrieve_candidate_clauses(q.query, top_k=8)
    reranked = rerank_candidates(q.query, candidates)
    if reranked is not None:
        clause = reranked["clause"]
        confidence = reranked["retrieval_confidence"]
        answer_source = "reranker"

    if clause is None:
        clause, confidence = retrieve_clause(q.query)

# ✅ Handle no retrieval case
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
            "risk_reason": "No relevant clause found in knowledge base"
        }

    answer = generate_answer(clause, q.query)

    if is_insufficient_answer(answer):
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
            "risk_reason": "Retrieved context was insufficient; switched to Gemini fallback"
        }

    risk = detect_risk(clause)
    clause_ref = extract_clause_reference(clause)

    return {
        "question": q.query,
        "answer": answer,
        "answer_source": answer_source,
        "clause_reference": clause_ref,
        "confidence_score": round(float(confidence), 2),
        "risk_level": risk["risk_level"],
        "risk_reason": risk["risk_reason"]
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

    return {
        "status": "Document uploaded and processed",
        "chunks_created": len(chunks),
        "chunks_added": added_count
    }
