# ==============================================================================
# LLM ENGINE MODULE (Local Ollama)
# ==============================================================================
# Purpose: Interface with local Ollama LLM for privacy-preserving answer generation
# Model: llama3 (Meta's open-source LLM)
# Runs on: localhost:11434 (Ollama server)
# ==============================================================================

from langchain_ollama import OllamaLLM  # LangChain wrapper for Ollama

# Initialize Ollama LLM with configuration
# model=\"llama3\": Use Meta's Llama 3 model (excellent for Q&A)
# temperature=0: Deterministic output (no randomness, same input = same output)
# num_predict=120: Max tokens to generate (~120 words)
llm = OllamaLLM(
    model=\"llama3\",  # Model name (must be installed via `ollama pull llama3`)
    temperature=0,  # 0 = deterministic, 1 = creative
    num_predict=120  # Max output length in tokens
)


# ==============================================================================
# FUNCTION: Generate answer using local Ollama LLM
# ==============================================================================
def generate_local_answer(context: str, question: str) -> str:
    \"\"\"
    Generate answer using local Ollama llama3 model.
    
    Args:
        context: Retrieved legal clause text
        question: User's question
        
    Returns:
        Generated answer text
        
    Advantages vs Cloud LLMs:
        - Privacy: Data never leaves local machine
        - Speed: Typically 1-2 seconds (no network latency)
        - Cost: Free (no API charges)
        - Offline: Works without internet
        
    Disadvantages:
        - Requires Ollama installed and running
        - Needs good hardware (8GB+ RAM recommended)
        - Smaller model than GPT-4/Gemini
        
    Prompt Strategy:
        - Explicitly say \"Answer using ONLY the legal clause\"
        - Allow explaining conditions/limitations (not just copy-paste)
        - If insufficient info, say \"I cannot answer\"
        - Avoids general legal advice (only from provided context)
        
    Example:
        context = \"Section 3: Payment due within 30 days\"
        question = \"When is payment due?\"
        answer = \"Payment is due within 30 days\"
    \"\"\"
    # Construct prompt with clear instructions
    prompt = f\"\"\"
You are a legal assistant.

Answer the user's question using ONLY the legal clause below.
You MAY explain conditions or limitations mentioned in the clause.
Do NOT add information not present in the clause.
Do NOT give general legal advice.

If the clause does not contain any information relevant to the question, say:
\"I cannot answer this from the provided document.\"

Legal Clause:
{context}

Question:
{question}

Answer in clear, simple language.
\"\"\"
    # Invoke Ollama LLM with prompt
    # .invoke() sends prompt to Ollama server on localhost:11434
    # Returns generated text response
    # .strip() removes leading/trailing whitespace
    return llm.invoke(prompt).strip()
