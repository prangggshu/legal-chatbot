from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()


def generate_gemini_fallback_answer(question: str) -> str:
    prompt = f"""
You are a legal assistant.

The user asked a legal question that was not found in the local legal knowledge base.
Answer the question with general legal information in clear language.
Do not claim to quote the local documents.
If jurisdiction is unclear, mention that laws vary by jurisdiction.

Question:
{question}
"""
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return (
        "Note: This question was not found in the project knowledge base. "
        "The following is a general Gemini response.\n\n"
        f"{response.text.strip()}"
    )
