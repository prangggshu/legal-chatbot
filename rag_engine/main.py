from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import shutil
from rag_engine.rag_core import retrieve_clause, build_index, extract_clause_reference
from rag_engine.document_processor import extract_text, chunk_text
from rag_engine.risk_engine import detect_risk
from rag_engine.llm_router import generate_answer


app = FastAPI(title="Legal AI Chatbot API")

class Question(BaseModel):
    query: str

@app.get("/")
def home():
    return {"status": "Legal AI Backend Running"}

@app.post("/ask")
def ask_question(q: Question):
    clause, confidence = retrieve_clause(q.query)

# ✅ Handle no retrieval case
    if clause is None:
        return {
            "question": q.query,
            "answer": "I cannot answer this from the provided document.",
            "clause_reference": "Not Available",
            "confidence_score": 0.0,
            "risk_level": "Unknown",
            "risk_reason": "No relevant clause found"
        }

    answer = generate_answer(clause, q.query)
    risk = detect_risk(clause)
    clause_ref = extract_clause_reference(clause)

    return {
        "question": q.query,
        "answer": answer,
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

    build_index(chunks)

    return {
        "status": "Document uploaded and processed",
        "chunks_created": len(chunks)
    }
