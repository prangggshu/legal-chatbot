from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import re
import json
from pathlib import Path

embedder = SentenceTransformer("all-MiniLM-L6-v2")

index = None
chunks_store = []
chunk_sources = []
MIN_CONFIDENCE_SCORE = 0.35
MAX_RETRIEVAL_CANDIDATES = 50
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTOR_DB_DIR = PROJECT_ROOT / "vector_db"
FAISS_INDEX_PATH = VECTOR_DB_DIR / "legal_qa.index"
CHUNKS_PATH = VECTOR_DB_DIR / "legal_qa_chunks.json"
SOURCES_PATH = VECTOR_DB_DIR / "legal_qa_sources.json"
METADATA_PATH = VECTOR_DB_DIR / "legal_qa_metadata.json"
INDEX_SCHEMA_VERSION = 2
LEGAL_QA_PATH = PROJECT_ROOT / "legal-bert-finetune" / "data" / "legal_qa.json"
STOP_WORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "by", "with", "is", "are", "was", "were",
    "what", "which", "who", "whom", "when", "where", "why", "how", "does", "do", "did", "about", "under", "law"
}
QUERY_PHRASE_EXPANSIONS = {
    "it law": [
        "information technology",
        "information technology act",
        "cyber",
        "electronic record",
        "digital signature",
        "computer"
    ]
}

def build_index(chunks, persist: bool = False, source: str = "legal_qa"):
    global index, chunks_store, chunk_sources
    cleaned_chunks = [chunk.strip() for chunk in chunks if chunk and chunk.strip()]

    if not cleaned_chunks:
        chunks_store = []
        chunk_sources = []
        index = None
        return

    chunks_store = cleaned_chunks
    chunk_sources = [source] * len(cleaned_chunks)
    embeddings = embedder.encode(cleaned_chunks, convert_to_numpy=True)
    embeddings = np.array(embeddings, dtype=np.float32)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    if persist:
        save_index()

def add_chunks(chunks, persist: bool = False, source: str = "upload"):
    global index, chunks_store, chunk_sources

    cleaned_chunks = [chunk.strip() for chunk in chunks if chunk and chunk.strip()]
    if not cleaned_chunks:
        return 0

    if index is None or index.ntotal == 0 or not chunks_store:
        build_index(cleaned_chunks, persist=persist, source=source)
        return len(cleaned_chunks)

    existing_chunks = set(chunks_store)
    new_chunks = [chunk for chunk in cleaned_chunks if chunk not in existing_chunks]
    if not new_chunks:
        return 0

    embeddings = embedder.encode(new_chunks, convert_to_numpy=True)
    embeddings = np.array(embeddings, dtype=np.float32)
    index.add(embeddings)
    chunks_store.extend(new_chunks)
    chunk_sources.extend([source] * len(new_chunks))

    if persist:
        save_index()

    return len(new_chunks)

def save_index():
    if index is None or index.ntotal == 0 or not chunks_store or len(chunk_sources) != len(chunks_store):
        return False

    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_INDEX_PATH))

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks_store, f, ensure_ascii=False)

    with open(SOURCES_PATH, "w", encoding="utf-8") as f:
        json.dump(chunk_sources, f, ensure_ascii=False)

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump({"schema_version": INDEX_SCHEMA_VERSION}, f)

    return True

def load_index():
    global index, chunks_store, chunk_sources

    if not FAISS_INDEX_PATH.exists() or not CHUNKS_PATH.exists():
        return False

    if METADATA_PATH.exists():
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        if metadata.get("schema_version") != INDEX_SCHEMA_VERSION:
            return False
    else:
        return False

    loaded_index = faiss.read_index(str(FAISS_INDEX_PATH))

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        loaded_chunks = json.load(f)

    if SOURCES_PATH.exists():
        with open(SOURCES_PATH, "r", encoding="utf-8") as f:
            loaded_sources = json.load(f)
    else:
        loaded_sources = ["unknown"] * len(loaded_chunks)

    if (
        loaded_index.ntotal == 0
        or not loaded_chunks
        or loaded_index.ntotal != len(loaded_chunks)
        or len(loaded_sources) != len(loaded_chunks)
    ):
        return False

    index = loaded_index
    chunks_store = loaded_chunks
    chunk_sources = loaded_sources
    return True

def initialize_vector_db_from_legal_qa():
    if load_index():
        return True

    if not LEGAL_QA_PATH.exists():
        return False

    try:
        with open(LEGAL_QA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        contexts = []
        for item in data:
            context = item.get("context", "").strip()
            if not context:
                continue

            question = item.get("question", "").strip()
            searchable_text = f"Question: {question}\nClause: {context}" if question else context
            contexts.append(searchable_text)

        if not contexts:
            return False

        build_index(contexts, persist=True, source="legal_qa")
        return True
    except Exception:
        return False

def _extract_query_terms(query: str):
    normalized_query = query.lower().strip()
    tokens = re.findall(r"[a-z0-9]+", normalized_query)
    query_terms = [token for token in tokens if len(token) > 2 and token not in STOP_WORDS]

    expanded_phrases = []
    for phrase, expansions in QUERY_PHRASE_EXPANSIONS.items():
        if phrase in normalized_query:
            expanded_phrases.extend(expansions)

    if "it" in tokens and "information technology" not in expanded_phrases:
        expanded_phrases.extend(QUERY_PHRASE_EXPANSIONS["it law"])

    return query_terms, expanded_phrases


def _normalize_lookup_text(value: str) -> str:
    lowered = (value or "").lower().strip()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered


def _extract_wrapped_question_and_clause(text: str):
    match = re.match(r"\s*Question:\s*(.*?)\s*\nClause:\s*(.*)\Z", text or "", flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None, None
    question_text = match.group(1).strip()
    clause_text = match.group(2).strip()
    return question_text, clause_text


def _find_exact_question_match(query: str):
    normalized_query = _normalize_lookup_text(query)
    if not normalized_query:
        return None

    for chunk in chunks_store:
        question_text, _ = _extract_wrapped_question_and_clause(chunk)
        if not question_text:
            continue
        if _normalize_lookup_text(question_text) == normalized_query:
            return chunk
    return None


def _rank_candidates(query: str):
    if index is None or index.ntotal == 0 or not chunks_store:
        return []

    q_embedding = embedder.encode([query], convert_to_numpy=True)
    q_embedding = np.array(q_embedding, dtype=np.float32)
    candidate_count = min(MAX_RETRIEVAL_CANDIDATES, index.ntotal)
    distances, indices = index.search(q_embedding, k=candidate_count)

    if indices.size == 0:
        return []

    query_terms, expanded_phrases = _extract_query_terms(query)
    ranked = []

    for distance, chunk_idx in zip(distances[0], indices[0]):
        if chunk_idx < 0 or chunk_idx >= len(chunks_store):
            continue

        clause_text = chunks_store[chunk_idx]
        source = chunk_sources[chunk_idx] if chunk_idx < len(chunk_sources) else "unknown"
        lowered_clause = clause_text.lower()

        confidence = 1 / (1 + float(distance))
        keyword_hits = sum(1 for term in query_terms if term in lowered_clause)
        phrase_hits = sum(1 for phrase in expanded_phrases if phrase in lowered_clause)
        source_bonus = 0.03 if source == "legal_qa" else 0.0
        combined_score = confidence + (0.08 * keyword_hits) + (0.15 * phrase_hits) + source_bonus

        ranked.append(
            {
                "combined_score": float(combined_score),
                "retrieval_confidence": float(confidence),
                "lexical_hits": int(keyword_hits + phrase_hits),
                "clause": clause_text,
                "source": source,
            }
        )

    ranked.sort(key=lambda row: row["combined_score"], reverse=True)
    return ranked


def retrieve_candidate_clauses(query: str, top_k: int = 8):
    ranked = _rank_candidates(query)
    if not ranked:
        return []
    return ranked[: max(1, top_k)]

def retrieve_clause(query):
    exact_match = _find_exact_question_match(query)
    if exact_match is not None:
        return exact_match, 0.99

    ranked = _rank_candidates(query)
    if not ranked:
        return None, None

    best_candidate = ranked[0]
    best_confidence = best_candidate["retrieval_confidence"]
    best_lexical_hits = best_candidate["lexical_hits"]
    best_clause = best_candidate["clause"]
    best_source = best_candidate["source"]
    rounded_confidence = float(round(best_confidence, 2))

    if best_confidence < MIN_CONFIDENCE_SCORE and best_lexical_hits == 0:
        return None, rounded_confidence

    best_knowledge_base_candidate = next((candidate for candidate in ranked if candidate["source"] == "legal_qa"), None)

    if best_knowledge_base_candidate is not None:
        kb_confidence = best_knowledge_base_candidate["retrieval_confidence"]
        kb_lexical_hits = best_knowledge_base_candidate["lexical_hits"]
        kb_clause = best_knowledge_base_candidate["clause"]

        if kb_clause != best_clause:
            merged_context = (
                f"Knowledge Base Context:\n{kb_clause}\n\n"
                f"Additional Retrieved Context ({'Uploaded Document' if best_source == 'upload' else 'Knowledge Base'}):\n{best_clause}"
            )
            merged_confidence = float(round(max(best_confidence, kb_confidence), 2))

            if kb_confidence >= MIN_CONFIDENCE_SCORE or kb_lexical_hits > 0:
                return merged_context, merged_confidence

    return best_clause, rounded_confidence


def extract_clause_reference(text: str) -> str:
    if not text:
        return "Not Available"

    question_match = re.search(r"Question:\s*(.+?)(?:\n|$)", text, flags=re.IGNORECASE)
    if question_match:
        question_text = question_match.group(1)
        section_or_clause_match = re.search(
            r"\b(Section|Clause)\s+\d+[A-Za-z]*\b",
            question_text,
            flags=re.IGNORECASE,
        )
        if section_or_clause_match:
            return section_or_clause_match.group(0).title()

    section_or_clause_match = re.search(r"\b(Section|Clause)\s+\d+[A-Za-z]*\b", text, flags=re.IGNORECASE)
    if section_or_clause_match:
        return section_or_clause_match.group(0).title()

    chapter_match = re.search(r"\bChapter\s+[IVXLC0-9]+\b", text, flags=re.IGNORECASE)
    if chapter_match:
        return chapter_match.group(0).title()

    return "Not Available"
