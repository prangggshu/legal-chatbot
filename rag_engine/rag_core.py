from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import re

embedder = SentenceTransformer("all-MiniLM-L6-v2")

index = None
chunks_store = []

def build_index(chunks):
    global index, chunks_store
    chunks_store = chunks
    embeddings = embedder.encode(chunks)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

def retrieve_clause(query):
    if index is None:
        return None, None

    q_embedding = embedder.encode([query])
    distances, indices = index.search(q_embedding, k=1)

    clause_text = chunks_store[indices[0][0]]
    distance = distances[0][0]

    # Convert distance to confidence score (simple normalization)
    confidence = float(round(1 / (1 + distance), 2))


    return clause_text, confidence


def extract_clause_reference(text: str) -> str:
    match = re.search(r'Clause\s+\d+', text)
    if match:
        return match.group()
    return "Not Available"
