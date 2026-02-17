import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
client = genai

MODEL_NAME = "gemini-2.5-flash"

def generate_gemini_answer(context: str, question: str) -> str:
    prompt = f"""
You are a legal assistant.

Answer the user's question using ONLY the legal clause below.
Do NOT add information not present in the clause.

Legal Clause:
{context}

Question:
{question}

Answer clearly.
"""
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)

    return response.text.strip()
