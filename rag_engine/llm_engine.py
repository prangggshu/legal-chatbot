from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    model="llama3",
    temperature=0,
    num_predict=120
)

def generate_local_answer(context: str, question: str) -> str:
    prompt = f"""
You are a legal assistant.

Answer the user's question using ONLY the legal clause below.
You MAY explain conditions or limitations mentioned in the clause.
Do NOT add information not present in the clause.
Do NOT give general legal advice.

If the clause does not contain any information relevant to the question, say:
"I cannot answer this from the provided document."

Legal Clause:
{context}

Question:
{question}

Answer in clear, simple language.
"""
    return llm.invoke(prompt).strip()
