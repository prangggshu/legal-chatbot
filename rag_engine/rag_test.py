from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Load embedding model (once)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Sample legal clauses (later this comes from uploaded documents)
clauses = [
    "The employer may terminate the employee without notice.",
    "A penalty of fifty thousand rupees applies if the employee resigns early.",
    "The agreement is governed by Indian law."
]

# Create embeddings
embeddings = embedder.encode(clauses)

# Store in FAISS
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings))

def retrieve_clause(question: str) -> str:
    """
    Takes a user question and returns the most relevant clause.
    """
    q_embedding = embedder.encode([question])
    D, I = index.search(q_embedding, k=1)
    return clauses[I[0][0]]
