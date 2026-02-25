# ==============================================================================
# GEMINI ENGINE MODULE
# ==============================================================================
# Purpose: Interface with Google's Gemini API for LLM generation
# Model: gemini-2.5-flash (fast, cost-effective)
# Use Cases: Answer generation, fallback knowledge, document summarization
# ==============================================================================

from google import genai  # Google Generative AI Python SDK
import os  # Environment variables
from dotenv import load_dotenv  # Load .env files

# Load environment variables from .env file (if exists)
# Allows setting GEMINI_API_KEY without hardcoding it
load_dotenv()

# Initialize Gemini client with API key from environment
# Get your key at: https://makersuite.google.com/
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Model selection: gemini-2.5-flash
# - Fast: 1-3 second responses
# - Cost-effective: $0.0001 per prompt
# - Quality: Excellent for Q&A and summarization
MODEL_NAME = "gemini-2.5-flash"


# ==============================================================================
# FUNCTION: Generate answer from context using Gemini
# ==============================================================================
def generate_gemini_answer(context: str, question: str) -> str:
    """
    Generate answer to question using only provided context.
    
    Args:
        context: Legal clause text (from vector search)
        question: User's question
        
    Returns:
        Generated answer text (2-3 sentences typically)
        
    Prompt Strategy:
        - Explicitly instruct: "Answer using ONLY the legal clause below"
        - Prevents hallucination (making up information)
        - If context insufficient, LLM says "not enough information"
        - Clear, professional legal assistant tone
        
    Example:
        context = "Section 5: Employee must provide 30 days notice"
        question = "What is the notice period?"
        answer = "30 days"
        
    Security:
        - Context is from user's document (already uploaded)
        - No sensitive data leaked (only sent what user uploaded)
        - API key required (don't commit to git)
    """
    # Construct prompt with clear instructions
    # Triple quotes allow multi-line string
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
    # Call Gemini API
    # model= specifies which model to use
    # contents= is the prompt text
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    # Extract and return generated text
    # .text attribute contains the answer
    # .strip() removes leading/trailing whitespace
    return response.text.strip()


# ==============================================================================
# FUNCTION: Generate fallback answer (general knowledge)
# ==============================================================================
def generate_gemini_fallback_answer(question: str) -> str:
    """
    Generate answer using general legal knowledge (not from local docs).
    
    Args:
        question: User's legal question
        
    Returns:
        General legal answer with disclaimer that it's not from user's docs
        
    When Used:
        - User asks question not found in uploaded documents
        - No semantic match in knowledge base (confidence < 0.30)
        - System needs to provide SOME answer rather than "I don't know"
        
    Prompt Strategy:
        - Clearly state question not found in local KB
        - Provide general legal information
        - Mention that laws vary by jurisdiction
        - Don't claim to quote local documents
        
    Example:
        question = "What is quantum mechanics?"
        (clearly not in legal docs)
        answer = "Note: This question was not found in the project knowledge base..."
        
    Difference vs generate_gemini_answer():
        - generate_gemini_answer(): Answer from specific retrieved clause
        - generate_gemini_fallback_answer(): Answer from general knowledge
    """
    # Construct prompt for general knowledge query
    prompt = f"""
You are a legal assistant.

The user asked a legal question that was not found in the local legal knowledge base.
Answer the question with general legal information in clear language.
Do not claim to quote the local documents.
If jurisdiction is unclear, mention that laws vary by jurisdiction.

Question:
{question}
"""
    # Call Gemini API with general knowledge prompt
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    # Return answer with clear disclaimer prefix
    # User needs to know this is NOT from their uploaded document
    return (
        "Note: This question was not found in the project knowledge base. "
        "The following is a general Gemini response.\n\n"
        f"{response.text.strip()}"
    )


# ==============================================================================
# FUNCTION: Generate document summary
# ==============================================================================
def generate_document_summary(document_text: str) -> str:
    """
    Generate concise summary of full legal document.
    
    Args:
        document_text: Full text of document (all pages)
        
    Returns:
        2-3 paragraph summary covering key points
        
    Summary Includes:
        1. Key parties involved (Company A, Employee, etc.)
        2. Document type (Employment Agreement, Service Contract, etc.)
        3. Main objectives and scope
        4. Important terms and conditions
        5. Critical clauses and obligations
        
    Use Case:
        - User uploads 20-page contract
        - Clicks "Summarize" button
        - Gets high-level overview in 30 seconds
        - Can then ask specific questions about clauses
        
    Example:
        Input: 5000-word employment agreement
        Output: "This is an Employment Agreement between XYZ Corporation and [Employee]..."
        
    Note:
        - Full document text sent to Gemini (can be large)
        - Gemini has 128K token context window (handles most docs)
        - For very large docs (> 50 pages), may need chunking
    """
    # Construct prompt for document summarization
    prompt = f"""
You are a legal document specialist.

Read the following legal document carefully and provide a concise summary (2-3 paragraphs).

The summary should:
1. Identify the key parties and document type
2. Describe the main objectives and scope
3. Highlight the most important terms and conditions
4. Note any critical clauses or obligations

Document:
{document_text}

Provide the summary in clear, professional language.
"""
    # Call Gemini API with full document text
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    # Return generated summary text
    return response.text.strip()
