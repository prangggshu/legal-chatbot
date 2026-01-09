from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={"api_version": "v1"}
)

MODEL_NAME = "models/gemini-2.5-flash"

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
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()
