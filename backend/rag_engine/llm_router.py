# ==============================================================================
# LLM ROUTER MODULE
# ==============================================================================
# Purpose: Intelligently route between local (Ollama) and cloud (Gemini) LLMs
# Strategy: Try local first (fast, private), fall back to cloud (reliable)
# ==============================================================================

import time  # Track elapsed time for timeout
from rag_engine.llm_engine import generate_local_answer  # Ollama llama3
from rag_engine.gemini_engine import generate_gemini_answer  # Google Gemini API

# Maximum time to wait for local LLM (Ollama) before fallback
# 4 seconds chosen as balance:
# - < 2s: Ollama often responds naturally
# - 4s: Gives slow machines a chance
# - > 4s: User perceives as hanging
MAX_LOCAL_TIME = 4  # seconds


# ==============================================================================
# FUNCTION: Generate answer with intelligent routing
# ==============================================================================
def generate_answer(context: str, question: str) -> str:
    """
    Generate answer using local LLM with cloud fallback.
    
    Args:
        context: Retrieved clause text (from vector search)
        question: User's question
        
    Returns:
        Generated answer text
        
    Routing Logic:
        1. Try Ollama llama3 on localhost:11434
        2. If response received within 4 seconds → use it
        3. If timeout (> 4s) or error → fall back to Gemini
        
    Why This Strategy?
        - Privacy: Local LLM keeps data on-device (no cloud API)
        - Speed: Ollama typically faster (1-2s vs 3-5s)
        - Cost: Ollama is free, Gemini costs per token
        - Reliability: Gemini fallback ensures answer even if Ollama down
        
    Example Flow (Ollama Success):
        User asks question → Ollama responds in 1.5s → Return Ollama answer
        
    Example Flow (Ollama Timeout):
        User asks question → Ollama silent for 4s → Switch to Gemini → Return Gemini answer
        
    Example Flow (Ollama Error):
        User asks question → Ollama not running → Catch exception → Return Gemini answer
    """
    # Record start time for timeout tracking
    start = time.time()

    try:
        # Try local LLM first (Ollama llama3)
        answer = generate_local_answer(context, question)
        
        # Check if response received within acceptable time
        if time.time() - start <= MAX_LOCAL_TIME:
            # Fast enough! Return Ollama answer
            return answer
        else:
            # Ollama was slow (> 4 seconds)
            # Print debug message and fall through to Gemini
            print(\"Local LLM slow → switching to Gemini\")
    except Exception as e:
        # Local LLM failed (not running, network error, etc.)
        # Print debug message and fall through to Gemini
        print(\"Local LLM failed → switching to Gemini:\", e)

    # If we reach here, Ollama timed out or failed
    # Fall back to Gemini API (cloud)
    return generate_gemini_answer(context, question)
