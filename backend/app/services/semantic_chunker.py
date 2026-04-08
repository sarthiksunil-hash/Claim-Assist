"""
Semantic Chunker — Splits text into semantically coherent chunks.

Strategy:
1. Split text into sentences
2. Generate embeddings per sentence (using sentence-transformers)
3. Compare cosine similarity between consecutive sentences
4. Where similarity drops below threshold → chunk boundary
5. Return list of chunks with metadata

Fallback: If sentence-transformers is not available, use paragraph-based splitting.
"""

import re
import numpy as np
from typing import List, Dict, Optional

# Lazy-load sentence-transformers (heavy import)
_model = None
_model_load_attempted = False


def _get_embedding_model():
    """Lazy-load the sentence-transformers model."""
    global _model, _model_load_attempted
    if _model_load_attempted:
        return _model
    _model_load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[SemanticChunker] Loaded all-MiniLM-L6-v2 embedding model")
    except Exception as e:
        print(f"[SemanticChunker] Could not load sentence-transformers: {e}")
        print("[SemanticChunker] Falling back to paragraph-based chunking")
        _model = None
    return _model


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using regex."""
    # Handle common abbreviations to avoid false splits
    text = re.sub(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s', '\n<<SPLIT>>\n', text)
    sentences = [s.strip() for s in text.split('<<SPLIT>>') if s.strip()]
    
    # If regex produced too few splits, try simpler approach
    if len(sentences) <= 2 and len(text) > 200:
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    return sentences


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _paragraph_chunking(text: str, max_chunk_size: int = 500) -> List[Dict]:
    """Fallback: chunk by paragraphs (when sentence-transformers unavailable)."""
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "token_count": len(current_chunk.split()),
                "chunk_index": len(chunks),
                "method": "paragraph",
            })
            current_chunk = para
        else:
            current_chunk += "\n\n" + para if current_chunk else para
    
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "token_count": len(current_chunk.split()),
            "chunk_index": len(chunks),
            "method": "paragraph",
        })
    
    return chunks


def semantic_chunk(
    text: str,
    similarity_threshold: float = 0.4,
    min_chunk_size: int = 50,
    max_chunk_size: int = 800,
) -> List[Dict]:
    """
    Split text into semantically coherent chunks.
    
    Args:
        text: The input text to chunk
        similarity_threshold: Below this cosine similarity, create a new chunk (lower = fewer chunks)
        min_chunk_size: Minimum characters per chunk
        max_chunk_size: Maximum characters per chunk
    
    Returns:
        List of chunk dicts with: text, token_count, chunk_index, method
    """
    if not text or len(text.strip()) < min_chunk_size:
        return [{
            "text": text.strip(),
            "token_count": len(text.split()),
            "chunk_index": 0,
            "method": "single",
        }] if text and text.strip() else []

    model = _get_embedding_model()
    
    # Fallback to paragraph chunking if model not available
    if model is None:
        return _paragraph_chunking(text, max_chunk_size)
    
    # Step 1: Split into sentences
    sentences = _split_into_sentences(text)
    
    if len(sentences) <= 1:
        return _paragraph_chunking(text, max_chunk_size)
    
    # Step 2: Generate embeddings for all sentences
    try:
        embeddings = model.encode(sentences, show_progress_bar=False)
    except Exception as e:
        print(f"[SemanticChunker] Embedding error: {e}")
        return _paragraph_chunking(text, max_chunk_size)
    
    # Step 3: Find breakpoints based on cosine similarity drops
    breakpoints = []
    for i in range(1, len(sentences)):
        sim = _cosine_similarity(embeddings[i - 1], embeddings[i])
        if sim < similarity_threshold:
            breakpoints.append(i)
    
    # Step 4: Build chunks from breakpoints
    chunks = []
    start_idx = 0
    
    for bp in breakpoints:
        chunk_text = " ".join(sentences[start_idx:bp]).strip()
        if len(chunk_text) >= min_chunk_size:
            chunks.append({
                "text": chunk_text,
                "token_count": len(chunk_text.split()),
                "chunk_index": len(chunks),
                "method": "semantic",
            })
            start_idx = bp
        # If chunk is too small, merge with next
    
    # Add remaining sentences as final chunk
    remaining = " ".join(sentences[start_idx:]).strip()
    if remaining:
        if chunks and len(remaining) < min_chunk_size:
            # Merge small trailing chunk with previous
            chunks[-1]["text"] += " " + remaining
            chunks[-1]["token_count"] = len(chunks[-1]["text"].split())
        else:
            chunks.append({
                "text": remaining,
                "token_count": len(remaining.split()),
                "chunk_index": len(chunks),
                "method": "semantic",
            })
    
    # Step 5: Split any chunks that are too large
    final_chunks = []
    for chunk in chunks:
        if len(chunk["text"]) > max_chunk_size:
            sub_chunks = _paragraph_chunking(chunk["text"], max_chunk_size)
            for sc in sub_chunks:
                sc["chunk_index"] = len(final_chunks)
                sc["method"] = "semantic+split"
                final_chunks.append(sc)
        else:
            chunk["chunk_index"] = len(final_chunks)
            final_chunks.append(chunk)
    
    print(f"[SemanticChunker] Split {len(text)} chars → {len(final_chunks)} chunks "
          f"(avg {sum(c['token_count'] for c in final_chunks) // max(len(final_chunks), 1)} tokens/chunk)")
    
    return final_chunks
