import os
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_DIR = PROJECT_ROOT / "legal-bert-finetune" / "output" / "legal-bert-finetuned"
RELEVANCE_THRESHOLD = float(os.getenv("RERANKER_MIN_SCORE", "0.5"))

_tokenizer = None
_model = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_load_attempted = False


def _load_model(model_dir: Path | None = None) -> bool:
    global _tokenizer, _model, _load_attempted

    if _tokenizer is not None and _model is not None:
        return True
    if _load_attempted:
        return False

    _load_attempted = True
    target_dir = model_dir or DEFAULT_MODEL_DIR
    if not target_dir.exists():
        return False

    try:
        _tokenizer = AutoTokenizer.from_pretrained(str(target_dir))
        _model = AutoModelForSequenceClassification.from_pretrained(str(target_dir)).to(_device)
        _model.eval()
        return True
    except Exception:
        _tokenizer = None
        _model = None
        return False


def rerank_candidates(query: str, candidates: list[dict], min_score: float | None = None) -> dict | None:
    if not candidates:
        return None

    if not _load_model():
        return None

    assert _tokenizer is not None
    assert _model is not None

    threshold = RELEVANCE_THRESHOLD if min_score is None else min_score
    best = None

    with torch.no_grad():
        for candidate in candidates:
            clause = candidate.get("clause", "")
            if not clause:
                continue

            encoded = _tokenizer(
                query,
                clause,
                truncation=True,
                padding="max_length",
                max_length=256,
                return_tensors="pt",
            )
            encoded = {key: value.to(_device) for key, value in encoded.items()}
            logits = _model(**encoded).logits
            probabilities = torch.softmax(logits, dim=1)
            relevance_score = float(probabilities[0][1].item())

            row = {
                "clause": clause,
                "source": candidate.get("source", "unknown"),
                "retrieval_confidence": float(candidate.get("retrieval_confidence", 0.0)),
                "reranker_score": relevance_score,
            }

            if best is None or row["reranker_score"] > best["reranker_score"]:
                best = row

    if best is None:
        return None
    if best["reranker_score"] < threshold:
        return None
    return best
