# ==============================================================================
# DOCUMENT PROCESSOR MODULE
# ==============================================================================
# Purpose: Extract text from PDFs and chunk into semantic segments
# Strategy: Multi-level intelligent chunking for Indian legal documents
# ==============================================================================

import pdfplumber  # PDF text extraction library
import re  # Regular expressions for pattern matching


# ==============================================================================
# FUNCTION: Extract full text from PDF
# ==============================================================================
def extract_text(file_path: str) -> str:
    """
    Extract all text from a PDF file, combining all pages.
    
    Args:
        file_path: Path to PDF file on disk
        
    Returns:
        Full text from all pages concatenated with newlines
        
    Process:
        - Open PDF with pdfplumber
        - Iterate through all pages
        - Extract text from each page
        - Combine with newlines between pages
        
    Handles:
        - Multi-page PDFs
        - Text-based PDFs (not scanned images)
        - UTF-8 encoding
        
    Note:
        Does NOT work with scanned PDFs (image-based)
        Those need OCR preprocessing first
    """
    # Initialize empty text accumulator
    text = ""
    
    # Open PDF file using context manager (auto-closes on exit)
    with pdfplumber.open(file_path) as pdf:
        # Iterate through each page in the PDF
        for page in pdf.pages:
            # Extract text from current page
            page_text = page.extract_text()
            
            # If page has text (not blank or image-only)
            if page_text:
                # Append to accumulator with newline separator
                text += page_text + "\n"
    
    # Return full document text
    return text


# ==============================================================================
# FUNCTION: Intelligent multi-level chunking
# ==============================================================================
def chunk_text(text: str):
    """
    Chunk text using multi-level strategy optimized for legal documents.
    
    Strategy:
        Level 1: Split by ARTICLE/SECTION headers
        Level 2: Split by numbered clauses (e.g., 3.14, 6.2)
        Level 3: Sliding window fallback if no structure found
        
    Args:
        text: Full document text (all pages combined)
        
    Returns:
        List of chunk strings, each 50-1000 words (target 150)
        
    Why Multi-Level?
        Legal documents have hierarchical structure:
        - ARTICLE II -> defines major section
        - 3.14 -> specific clause within article
        - Preserving structure improves semantic relevance
        
    Word Constraints:
        - MIN: 50 words (avoid fragments)
        - MAX: 1000 words (avoid overload)
        - TARGET: 150 words (optimal for embeddings)
        
    Example Document Structure:
        ARTICLE I - Definitions
          1.1 \"Employee\" means...
          1.2 \"Employer\" means...
        ARTICLE II - Employment Terms
          2.1 The employee shall...
          2.2 Compensation is...
    """

    # Normalize whitespace: collapse multiple spaces/newlines to single space
    # This makes regex patterns more reliable
    text = re.sub(r'\s+', ' ', text)

    # Define word count constraints
    MIN_CHUNK_WORDS = 50  # Minimum words to avoid fragments
    MAX_CHUNK_WORDS = 300  # Maximum words to fit in context window
    TARGET_CHUNK_WORDS = 150  # Target size for semantic coherence

    # ==============================================================================
    # LEVEL 1: Split by ARTICLE/SECTION headers
    # ==============================================================================
    # Pattern matches: ARTICLE V, SECTION 3, Article II, etc.
    # [\s—-]* allows optional spaces, em-dashes, or hyphens
    # [IVXivx0-9]+ matches Roman numerals or Arabic numbers
    article_pattern = r'((?:ARTICLE|SECTION)[\s—-]*[IVXivx0-9]+)'
    
    # Split text, keeping delimiters (ARTICLE/SECTION headers)
    # Returns: [before_first_match, match1, after_match1, match2, after_match2, ...]
    article_splits = re.split(article_pattern, text, flags=re.IGNORECASE)

    # Initialize list to collect chunks
    chunks = []

    # Iterate through splits in pairs (header + content)
    # range(1, ..., 2) gives: 1, 3, 5, ... (odd indices = headers)
    for i in range(1, len(article_splits), 2):
        # Skip if we've reached end of list
        if i < len(article_splits):
            # Extract article header (ARTICLE II, etc.)
            article_header = article_splits[i]
            
            # Extract article content (text following header)
            article_content = article_splits[i + 1] if i + 1 < len(article_splits) else ""
            
            # Skip if content is empty or too short
            if not article_content or len(article_content.split()) < MIN_CHUNK_WORDS:
                continue

            # ==============================================================================
            # LEVEL 2: Split article content by numbered clauses
            # ==============================================================================
            # Pattern matches: 3.14, 6.2, 1.2.3, etc.
            # \d+ = one or more digits
            # \.\d+ = period followed by digits (can repeat)
            clause_pattern = r'(\d+\.\d+\.?\d*)'
            
            # Split article content by clause numbers, keeping delimiters
            clause_splits = re.split(clause_pattern, article_content, flags=re.IGNORECASE)

            # Buffer to accumulate clause text
            clause_buffer = ""
            
            # Iterate through clause splits
            for j in range(len(clause_splits)):
                part = clause_splits[j]
                
                # Check if this part is a clause number (e.g., \"3.14\")
                if re.match(r'^\d+\.\d+', part):
                    # This is a clause header
                    # If buffer has content and meets min size, save as chunk
                    if clause_buffer and len(clause_buffer.split()) >= MIN_CHUNK_WORDS:
                        chunks.append(f\"{article_header} {clause_buffer.strip()}\")
                    
                    # Start new buffer with this clause number
                    clause_buffer = part
                else:
                    # This is clause content text, add to buffer
                    clause_buffer += \" \" + part

            # Save final clause buffer if it meets minimum size
            if clause_buffer and len(clause_buffer.split()) >= MIN_CHUNK_WORDS:
                chunks.append(f\"{article_header} {clause_buffer.strip()}\")


    # ==============================================================================
    # LEVEL 3: Sliding window fallback (if no structured chunks found)
    # ==============================================================================
    # If no ARTICLE/SECTION structure discovered, use sliding window approach
    if not chunks:
        # Split text into individual words
        words = text.split()
        
        # If whole document is tiny, return it as single chunk
        if len(words) < MIN_CHUNK_WORDS:
            return [text] if text.strip() else []

        # Initialize list for window-based chunks
        chunk_list = []
        i = 0  # Start index for sliding window
        
        # Slide window across document
        while i < len(words):
            # End index: current + target size, capped at document length
            chunk_end = min(i + TARGET_CHUNK_WORDS, len(words))
            
            # Extract words for this chunk
            chunk_words = words[i:chunk_end]
            
            # Join words back into string
            chunk_text_str = " ".join(chunk_words)

            # Only add if meets minimum size requirement
            if len(chunk_words) >= MIN_CHUNK_WORDS:
                chunk_list.append(chunk_text_str)

            # Advance window by half target size (50% overlap)
            # Overlap ensures no information lost at boundaries
            i += TARGET_CHUNK_WORDS // 2

        # Return sliding window chunks
        return chunk_list

    # ==============================================================================
    # FINAL CLEANUP: Filter chunks by word count constraints
    # ==============================================================================
    final_chunks = []
    for chunk in chunks:
        # Strip whitespace from chunk
        cleaned = chunk.strip()
        
        # Count words in chunk
        word_count = len(cleaned.split())
        
        # Only include if within acceptable range
        if MIN_CHUNK_WORDS <= word_count <= 1000:  # Note: max 1000 (not 300) for flexibility
            final_chunks.append(cleaned)

    # Return final chunks if any, otherwise full text as fallback
    return final_chunks if final_chunks else [text.strip()] if text.strip() else []
