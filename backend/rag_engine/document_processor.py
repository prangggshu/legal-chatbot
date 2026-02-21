import pdfplumber
import re

def extract_text(file_path: str) -> str:
    """
    Extract full text from PDF (Indian contracts friendly).
    """
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def chunk_text(text: str):
    """
    Chunk Indian legal contracts by ARTICLE and numbered clauses.
    """

    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)

    # Split on ARTICLE—X or ARTICLE - X
    article_splits = re.split(
        r'(ARTICLE[\s—-]*\d+)',
        text,
        flags=re.IGNORECASE
    )

    chunks = []
    buffer = ""

    for part in article_splits:
        if re.match(r'ARTICLE[\s—-]*\d+', part, re.IGNORECASE):
            if buffer:
                chunks.append(buffer.strip())
            buffer = part
        else:
            buffer += " " + part

    if buffer:
        chunks.append(buffer.strip())

    # Further split large articles into numbered clauses (e.g. 3.14, 6.2)
    final_chunks = []
    MIN_CHUNK_WORDS = 5

    for chunk in chunks:
        sub_chunks = re.split(
            r'(?=\d+\.\d+)',
            chunk
        )

        for sc in sub_chunks:
            cleaned = sc.strip()
            if len(cleaned.split()) >= MIN_CHUNK_WORDS:
                final_chunks.append(cleaned)

    if not final_chunks:
        final_chunks = [c.strip() for c in chunks if len(c.strip().split()) >= MIN_CHUNK_WORDS]

    return final_chunks
