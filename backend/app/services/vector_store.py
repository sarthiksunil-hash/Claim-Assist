"""
Vector Store Service — FAISS-based vector store for document indexing and semantic search.

FAISS stores vectors only, so we manage metadata separately via a JSON sidecar file.

Two logical collections:
1. user_documents — uploaded policy docs, medical reports, denial letters (per-user)
2. knowledge_base — IRDAI regulations, treatment protocols, denial categories (shared)

Storage layout:
  faiss_store/
    user_documents.index     — FAISS index file
    user_documents_meta.json — metadata for each vector
    knowledge_base.index
    knowledge_base_meta.json
"""

import os
import json
import numpy as np
from typing import List, Dict, Optional

# Lazy-load FAISS and embedding model
_faiss = None
_embed_model = None
_embed_model_load_attempted = False

FAISS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "faiss_store")

# In-memory stores (loaded from disk on first access)
_stores: Dict[str, dict] = {}  # { collection_name: { "index": faiss_index, "meta": [...], "texts": [...] } }


def _load_faiss():
    """Lazy-load FAISS."""
    global _faiss
    if _faiss is not None:
        return _faiss
    try:
        import faiss
        _faiss = faiss
        print("[VectorStore] FAISS loaded successfully")
        return _faiss
    except ImportError:
        print("[VectorStore] FAISS not installed — pip install faiss-cpu")
        return None


def _get_embedding_model():
    """Lazy-load the sentence-transformers embedding model."""
    global _embed_model, _embed_model_load_attempted
    if _embed_model_load_attempted:
        return _embed_model
    _embed_model_load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[VectorStore] Loaded embedding model: all-MiniLM-L6-v2 (384-dim)")
        return _embed_model
    except Exception as e:
        print(f"[VectorStore] Could not load embedding model: {e}")
        return None


def _encode_texts(texts: List[str]) -> Optional[np.ndarray]:
    """Encode texts into embedding vectors."""
    model = _get_embedding_model()
    if model is None:
        return None
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.array(embeddings, dtype=np.float32)


def _get_store(collection_name: str) -> Optional[dict]:
    """Get or create an in-memory store for a collection."""
    if collection_name in _stores:
        return _stores[collection_name]

    faiss = _load_faiss()
    if faiss is None:
        return None

    os.makedirs(FAISS_DIR, exist_ok=True)

    index_path = os.path.join(FAISS_DIR, f"{collection_name}.index")
    meta_path = os.path.join(FAISS_DIR, f"{collection_name}_meta.json")

    # Try to load existing index from disk
    if os.path.exists(index_path) and os.path.exists(meta_path):
        try:
            index = faiss.read_index(index_path)
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            store = {
                "index": index,
                "meta": data.get("meta", []),
                "texts": data.get("texts", []),
            }
            _stores[collection_name] = store
            print(f"[VectorStore] Loaded '{collection_name}' from disk ({index.ntotal} vectors)")
            return store
        except Exception as e:
            print(f"[VectorStore] Error loading {collection_name}: {e}")

    # Create a new empty index (384-dim for all-MiniLM-L6-v2)
    dim = 384
    index = faiss.IndexFlatIP(dim)  # Inner product (cosine sim with normalized vectors)
    store = {"index": index, "meta": [], "texts": []}
    _stores[collection_name] = store
    print(f"[VectorStore] Created new '{collection_name}' collection (dim={dim})")
    return store


def _save_store(collection_name: str):
    """Persist a store to disk."""
    faiss = _load_faiss()
    if faiss is None or collection_name not in _stores:
        return

    store = _stores[collection_name]
    os.makedirs(FAISS_DIR, exist_ok=True)

    index_path = os.path.join(FAISS_DIR, f"{collection_name}.index")
    meta_path = os.path.join(FAISS_DIR, f"{collection_name}_meta.json")

    try:
        faiss.write_index(store["index"], index_path)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "meta": store["meta"],
                "texts": store["texts"],
            }, f, ensure_ascii=False)
        print(f"[VectorStore] Saved '{collection_name}' ({store['index'].ntotal} vectors)")
    except Exception as e:
        print(f"[VectorStore] Error saving {collection_name}: {e}")


# ══════════════════════════════════════════════════════════════
#  DOCUMENT INDEXING
# ══════════════════════════════════════════════════════════════

def index_document(
    doc_id: str,
    chunks: List[Dict],
    metadata: Dict,
    user_email: str = "default",
) -> bool:
    """
    Index document chunks into the user_documents FAISS index.

    Args:
        doc_id: Unique document identifier
        chunks: List of chunk dicts from semantic_chunker (must have "text" key)
        metadata: Document metadata (file_type, filename, etc.)
        user_email: Owner of the document

    Returns:
        True if indexed successfully
    """
    store = _get_store("user_documents")
    if store is None:
        print("[VectorStore] No store available, skipping indexing")
        return False

    if not chunks:
        return False

    # Remove old chunks for this doc
    delete_document(doc_id)

    texts = [c["text"] for c in chunks]
    embeddings = _encode_texts(texts)
    if embeddings is None:
        return False

    try:
        store["index"].add(embeddings)

        for i, chunk in enumerate(chunks):
            store["meta"].append({
                "doc_id": doc_id,
                "user_email": user_email,
                "chunk_index": i,
                "chunk_method": chunk.get("method", "unknown"),
                "token_count": chunk.get("token_count", 0),
                "file_type": metadata.get("file_type", ""),
                "filename": metadata.get("filename", ""),
            })
            store["texts"].append(chunk["text"])

        _save_store("user_documents")
        print(f"[VectorStore] Indexed {len(chunks)} chunks for doc {doc_id} (user: {user_email})")
        return True

    except Exception as e:
        print(f"[VectorStore] Indexing error: {e}")
        return False


def delete_document(doc_id: str) -> bool:
    """
    Remove all chunks for a document.
    Since FAISS doesn't support deletion natively, we rebuild the index without the doc.
    """
    store = _get_store("user_documents")
    if store is None or not store["meta"]:
        return False

    faiss = _load_faiss()
    if faiss is None:
        return False

    # Find indices to keep
    keep_indices = [i for i, m in enumerate(store["meta"]) if m.get("doc_id") != doc_id]
    removed = len(store["meta"]) - len(keep_indices)

    if removed == 0:
        return True  # Nothing to remove

    if not keep_indices:
        # All entries belong to this doc — reset
        dim = 384
        store["index"] = faiss.IndexFlatIP(dim)
        store["meta"] = []
        store["texts"] = []
    else:
        # Rebuild index with remaining vectors
        # Re-encode remaining texts (FAISS doesn't let us extract vectors from IndexFlatIP easily)
        remaining_texts = [store["texts"][i] for i in keep_indices]
        remaining_meta = [store["meta"][i] for i in keep_indices]

        embeddings = _encode_texts(remaining_texts)
        if embeddings is not None:
            dim = 384
            new_index = faiss.IndexFlatIP(dim)
            new_index.add(embeddings)
            store["index"] = new_index
            store["meta"] = remaining_meta
            store["texts"] = remaining_texts

    _save_store("user_documents")
    print(f"[VectorStore] Deleted {removed} chunks for doc {doc_id}")
    return True


# ══════════════════════════════════════════════════════════════
#  SEARCH / RETRIEVAL
# ══════════════════════════════════════════════════════════════

def search_user_docs(
    query: str,
    user_email: str = "default",
    top_k: int = 5,
) -> List[Dict]:
    """
    Search user's uploaded documents for relevant chunks.

    Returns list of dicts with: text, score, metadata
    """
    store = _get_store("user_documents")
    if store is None or store["index"].ntotal == 0:
        return []

    query_embedding = _encode_texts([query])
    if query_embedding is None:
        return []

    try:
        # Search more than top_k since we filter by user
        n_search = min(store["index"].ntotal, top_k * 5)
        scores, indices = store["index"].search(query_embedding, n_search)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(store["meta"]):
                continue
            meta = store["meta"][idx]
            if meta.get("user_email") != user_email:
                continue
            results.append({
                "text": store["texts"][idx],
                "score": float(score),
                "metadata": meta,
            })
            if len(results) >= top_k:
                break

        return results

    except Exception as e:
        print(f"[VectorStore] User docs search error: {e}")
        return []


def search_knowledge_base(
    query: str,
    top_k: int = 5,
) -> List[Dict]:
    """
    Search the shared IRDAI/medical knowledge base.

    Returns list of dicts with: text, score, metadata
    """
    store = _get_store("knowledge_base")
    if store is None or store["index"].ntotal == 0:
        return []

    query_embedding = _encode_texts([query])
    if query_embedding is None:
        return []

    try:
        n_search = min(store["index"].ntotal, top_k)
        scores, indices = store["index"].search(query_embedding, n_search)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(store["meta"]):
                continue
            results.append({
                "text": store["texts"][idx],
                "score": float(score),
                "metadata": store["meta"][idx],
            })

        return results

    except Exception as e:
        print(f"[VectorStore] KB search error: {e}")
        return []


# ══════════════════════════════════════════════════════════════
#  KNOWLEDGE BASE INDEXING (run on startup)
# ══════════════════════════════════════════════════════════════

_kb_indexed = False


def index_knowledge_bases() -> bool:
    """
    Index the static IRDAI and medical knowledge bases into FAISS.
    Called once on startup. Skips if already indexed.
    """
    global _kb_indexed
    if _kb_indexed:
        return True

    store = _get_store("knowledge_base")
    if store is None:
        return False

    # Skip if already has data on disk
    if store["index"].ntotal > 0:
        print(f"[VectorStore] Knowledge base already indexed ({store['index'].ntotal} vectors)")
        _kb_indexed = True
        return True

    try:
        from app.services.insurance_kb import IRDAI_REGULATIONS, STANDARD_POLICY_CLAUSES, DENIAL_CATEGORIES
        from app.services.medical_kb import ICD10_CODES

        texts = []
        metas = []

        # ── IRDAI Regulations ──
        for reg in IRDAI_REGULATIONS:
            provisions = "; ".join(reg.get("key_provisions", []))
            doc_text = (
                f"IRDAI Regulation: {reg['title']} ({reg['id']})\n"
                f"Circular: {reg.get('circular_no', '')}\n"
                f"Key Provisions: {provisions}"
            )
            texts.append(doc_text)
            metas.append({
                "source": "insurance_kb",
                "type": "regulation",
                "regulation_id": reg["id"],
                "title": reg["title"],
            })

        # ── Standard Policy Clauses ──
        for key, clause in STANDARD_POLICY_CLAUSES.items():
            doc_text = (
                f"Policy Clause: {clause['title']} (Section {clause['section']})\n"
                f"{clause['standard_text']}\n"
                f"Appeal Strategy: {clause['appeal_strategy']}"
            )
            texts.append(doc_text)
            metas.append({
                "source": "insurance_kb",
                "type": "policy_clause",
                "section": clause["section"],
                "title": clause["title"],
            })

        # ── Denial Categories ──
        for key, cat in DENIAL_CATEGORIES.items():
            counter_args = "; ".join(cat.get("counter_arguments", []))
            doc_text = (
                f"Denial Category: {cat['label']}\n"
                f"Description: {cat['description']}\n"
                f"Counter Arguments: {counter_args}"
            )
            texts.append(doc_text)
            metas.append({
                "source": "insurance_kb",
                "type": "denial_category",
                "category_key": key,
                "title": cat["label"],
            })

        # ── Medical KB (ICD-10 + Treatment Protocols) ──
        for code, entry in ICD10_CODES.items():
            treatments = ", ".join(entry.get("standard_treatments", []))
            doc_text = (
                f"Medical: {entry.get('common_name', '')} ({code})\n"
                f"Description: {entry['description']}\n"
                f"Category: {entry.get('category', '')}\n"
                f"Standard Treatments: {treatments}\n"
                f"Severity: {entry.get('severity', '')}"
            )
            texts.append(doc_text)
            metas.append({
                "source": "medical_kb",
                "type": "icd10_code",
                "code": code,
                "title": entry.get("common_name", entry["description"]),
            })

        if not texts:
            print("[VectorStore] No KB entries to index")
            return False

        # Encode and add to FAISS
        embeddings = _encode_texts(texts)
        if embeddings is None:
            return False

        store["index"].add(embeddings)
        store["meta"] = metas
        store["texts"] = texts

        _save_store("knowledge_base")
        print(f"[VectorStore] Indexed {len(texts)} knowledge base entries into FAISS")
        _kb_indexed = True
        return True

    except Exception as e:
        print(f"[VectorStore] KB indexing error: {e}")
        import traceback
        traceback.print_exc()
        return False
