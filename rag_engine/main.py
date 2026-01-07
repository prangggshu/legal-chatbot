from fastapi import FastAPI
from pydantic import BaseModel
from rag_core import retrieve_clause

app = FastAPI(title="Legal AI Chatbot API")

class Question(BaseModel):
    query: str

@app.get("/")
def home():
    return {"status": "Legal AI Backend Running"}

@app.post("/ask")
def ask_question(q: Question):
    clause = retrieve_clause(q.query)
    return {
        "question": q.query,
        "answer": clause
    }
