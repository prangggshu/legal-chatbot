import time
from llm_engine import generate_local_answer
from gemini_engine import generate_gemini_answer

MAX_LOCAL_TIME = 4  # seconds

def generate_answer(context: str, question: str) -> str:
    start = time.time()

    try:
        answer = generate_local_answer(context, question)
        if time.time() - start <= MAX_LOCAL_TIME:
            return answer
        else:
            print("Local LLM slow → switching to Gemini")
    except Exception as e:
        print("Local LLM failed → switching to Gemini:", e)

    return generate_gemini_answer(context, question)
