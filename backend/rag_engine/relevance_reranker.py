# ==============================================================================
# RELEVANCE RERANKER MODULE (Optional BERT)
# ==============================================================================
# Purpose: Fine-tuned BERT model for reranking retrieved clauses by relevance
# Model: Legal-BERT fine-tuned on legal Q&A pairs
# Architecture: BERT sequence classification (2 classes: relevant/irrelevant)
# Usage: Optional enhancement to FAISS retrieval (graceful degradation if model missing)
# 
# Why BERT Reranking:
#   1. FAISS uses semantic embeddings (fast, ~80% accurate)
#   2. BERT uses cross-attention (slower, ~95% accurate)
#   3. Pipeline: FAISS gets top-5 → BERT reranks → return best
#   4. Combines speed of FAISS with accuracy of BERT
# 
# Graceful Degradation:
#   - If model not found in legal-bert-finetune/output/ → return None
#   - Main API continues with FAISS-only results
#   - No user-facing errors
# ==============================================================================

import os  # For environment variables
from pathlib import Path  # For file path handling

import torch  # PyTorch for model inference
from transformers import AutoModelForSequenceClassification, AutoTokenizer  # HuggingFace Transformers

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Get project root (go up from rag_engine/ to legal-chatbot/backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default path to fine-tuned BERT model
# Expected structure: backend/legal-bert-finetune/output/legal-bert-finetuned/
# Contains: config.json, pytorch_model.bin, tokenizer_config.json, vocab.txt
DEFAULT_MODEL_DIR = PROJECT_ROOT / "legal-bert-finetune" / "output" / "legal-bert-finetuned"

# Minimum relevance score to accept a clause (0.0-1.0)
# Default: 0.5 means model must be ≥50% confident clause is relevant
# Can override via RERANKER_MIN_SCORE env variable (e.g., 0.7 for stricter filtering)
RELEVANCE_THRESHOLD = float(os.getenv("RERANKER_MIN_SCORE", "0.5"))

# ==============================================================================
# GLOBAL STATE (Lazy Loading)
# ==============================================================================

# Tokenizer for converting text to BERT input tokens
# None until first rerank_candidates() call
_tokenizer = None

# BERT model for relevance classification
# None until first rerank_candidates() call
_model = None

# Device for model inference (CUDA GPU if available, else CPU)
# GPU speeds up inference ~10x (50ms vs 500ms per clause)
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Flag to avoid repeated load attempts if model not found
# Once we try and fail, don't retry every rerank call
_load_attempted = False


# ==============================================================================
# INTERNAL HELPER: Load BERT model (lazy initialization)
# ==============================================================================
def _load_model(model_dir: Path | None = None) -> bool:
    """
    Lazy load the fine-tuned BERT model and tokenizer.
    
    Args:
        model_dir: Optional custom model directory (default: legal-bert-finetuned/)
        
    Returns:
        True if model loaded successfully, False otherwise
        
    Side Effects:
        Sets global _tokenizer, _model, _load_attempted
        
    Lazy Loading Strategy:
        - Model loaded on first rerank_candidates() call (not at import time)
        - Saves memory if reranker never used
        - Faster startup time (model loading takes ~2-3 seconds)
        
    Graceful Degradation:
        - If model directory not found → return False
        - If loading fails (corrupted files, etc.) → return False
        - Caller checks return value and skips reranking
        
    Model Requirements:
        Directory must contain:
        - config.json (BERT architecture config)
        - pytorch_model.bin (trained weights)
        - tokenizer_config.json (tokenizer settings)
        - vocab.txt (BERT vocabulary)
    """
    global _tokenizer, _model, _load_attempted

    # Check if already loaded successfully
    if _tokenizer is not None and _model is not None:
        return True  # Already loaded, no work needed
    
    # Check if we already tried and failed
    if _load_attempted:
        return False  # Don't retry on every call (performance optimization)

    # Mark that we attempted loading (prevents retry loops)
    _load_attempted = True
    
    # Determine target directory (use provided or default)
    target_dir = model_dir or DEFAULT_MODEL_DIR
    
    # Check if directory exists
    if not target_dir.exists():
        # Model not trained yet or wrong path
        # This is normal if user hasn't run fine-tuning
        return False

    try:
        # Load tokenizer from saved directory
        # Tokenizer converts text → token IDs (e.g., "notice" → [2053, 2025])
        _tokenizer = AutoTokenizer.from_pretrained(str(target_dir))
        
        # Load model from saved directory
        # AutoModelForSequenceClassification = BERT with classification head
        # .to(_device) moves model to GPU (if available) or CPU
        _model = AutoModelForSequenceClassification.from_pretrained(str(target_dir)).to(_device)
        
        # Set model to evaluation mode (disables dropout, batch norm training)
        # Critical for inference (affects behavior of some layers)
        _model.eval()
        
        return True  # Success
        
    except Exception:
        # Loading failed (corrupted files, wrong format, missing dependencies, etc.)
        # Reset globals to None (clean state)
        _tokenizer = None
        _model = None
        return False  # Signal failure to caller



# ==============================================================================
# FUNCTION: Rerank candidates using fine-tuned BERT
# ==============================================================================
def rerank_candidates(query: str, candidates: list[dict], min_score: float | None = None) -> dict | None:
    """
    Rerank retrieved candidates using fine-tuned BERT and return the best match.
    
    Args:
        query: User's question (e.g., "When is payment due?")
        candidates: List of dicts from FAISS retrieval, each with:
            - "clause": legal text
            - "source": document/section name
            - "retrieval_confidence": FAISS similarity score (0.0-1.0)
        min_score: Optional override for relevance threshold (default: RELEVANCE_THRESHOLD)
        
    Returns:
        Best candidate dict with added "reranker_score", or None if:
        - No candidates provided
        - Model not loaded
        - All scores below threshold
        
    Algorithm:
        1. Try to load BERT model (lazy loading)
        2. For each candidate:
           a. Tokenize query+clause pair (cross-attention input)
           b. Run through BERT model
           c. Softmax logits → probability distribution [irrelevant, relevant]
           d. Extract P(relevant) as relevance score
        3. Track best (highest scoring) candidate
        4. Return best if score ≥ threshold, else None
        
    BERT Cross-Attention:
        - Input: [CLS] query [SEP] clause [SEP]
        - BERT attends between query tokens and clause tokens
        - Captures semantic overlap better than cosine similarity
        - Example: "payment deadline" matches "due within 30 days"
        
    Performance:
        - ~50-500ms per candidate (CPU vs GPU)
        - Typically rerank 3-5 candidates (total: 150-2500ms)
        - FAISS retrieval: ~10ms (20-250x faster but less accurate)
        
    Token Limit:
        - Max 256 tokens (query + clause combined)
        - If exceeded, truncates from end (keeps beginning of clause)
        - Most clauses <256 tokens (~200 words)
    """
    # Early exit if no candidates
    if not candidates:
        return None

    # Try to load model (returns False if model not available)
    if not _load_model():
        # Model not found or failed to load
        # Gracefully degrade: return None (caller uses FAISS results)
        return None

    # Assert model loaded (for type checker)
    # These should be set by _load_model() if it returned True
    assert _tokenizer is not None
    assert _model is not None

    # Determine threshold to use (parameter override or global default)
    threshold = RELEVANCE_THRESHOLD if min_score is None else min_score
    
    # Track best candidate so far
    best = None

    # Disable gradient computation (inference only, no training)
    # Saves memory and speeds up inference (~30% faster)
    with torch.no_grad():
        # Loop through each candidate from FAISS retrieval
        for candidate in candidates:
            # Extract clause text
            clause = candidate.get("clause", "")
            
            # Skip empty clauses
            if not clause:
                continue

            # Tokenize query+clause pair for BERT input
            # truncation=True: If >256 tokens, truncate from end
            # padding="max_length": Pad to 256 tokens (BERT requires fixed length)
            # return_tensors="pt": Return PyTorch tensors (not lists)
            encoded = _tokenizer(
                query,  # First sequence (query)
                clause,  # Second sequence (clause)
                truncation=True,  # Truncate if too long
                padding="max_length",  # Pad to max_length
                max_length=256,  # Max tokens for BERT input
                return_tensors="pt",  # Return PyTorch tensors
            )
            
            # Move tensors to same device as model (GPU or CPU)
            # Model on GPU but input on CPU = error
            encoded = {key: value.to(_device) for key, value in encoded.items()}
            
            # Run BERT model on encoded input
            # **encoded unpacks dict (input_ids, attention_mask, token_type_ids)
            # .logits extracts raw prediction scores [batch_size, num_classes]
            logits = _model(**encoded).logits
            
            # Convert logits to probabilities using softmax
            # logits = [logit_irrelevant, logit_relevant] (e.g., [-2.3, 1.8])
            # softmax → [P(irrelevant), P(relevant)] (e.g., [0.02, 0.98])
            probabilities = torch.softmax(logits, dim=1)
            
            # Extract P(relevant) = second class probability
            # probabilities[0][1] = first batch item, second class (relevant)
            # .item() converts tensor to Python float
            relevance_score = float(probabilities[0][1].item())

            # Build result dict with all scores
            row = {
                "clause": clause,  # Keep original clause text
                "source": candidate.get("source", "unknown"),  # Document source
                "retrieval_confidence": float(candidate.get("retrieval_confidence", 0.0)),  # FAISS score
                "reranker_score": relevance_score,  # BERT score (0.0-1.0)
            }

            # Update best if this is the highest scoring candidate so far
            if best is None or row["reranker_score"] > best["reranker_score"]:
                best = row

    # Check if we found any candidate
    if best is None:
        return None  # All candidates were empty clauses
    
    # Check if best candidate meets threshold
    if best["reranker_score"] < threshold:
        # Best candidate too low confidence (e.g., 0.35 < 0.5)
        # Better to return nothing than wrong answer
        return None
    
    # Return best candidate (above threshold)
    return best
