"""
RAG Service — Retrieval-Augmented Generation orchestrator.

Pipeline:
1. Receive user query + user_email
2. Search user's documents (ChromaDB) for relevant chunks
3. Search shared knowledge base for relevant IRDAI/medical info
4. Build context-enriched prompt
5. Send to Ollama/LLM for generation
6. Return response with source citations
"""

import os
import httpx
from typing import List, Dict, Optional, Tuple

from app.services.vector_store import search_user_docs, search_knowledge_base

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

RAG_SYSTEM_PROMPT = """You are ClaimAssist AI, an expert assistant for Indian health insurance claims and IRDAI regulations.

You have been provided with CONTEXT retrieved from the user's uploaded documents and the IRDAI/medical knowledge base. Use this context to give accurate, specific answers.

RULES:
1. ALWAYS prioritize information from the provided CONTEXT over your general knowledge.
2. If the context contains relevant policy clauses, quote them with section numbers.
3. If the context references IRDAI regulations, cite the regulation ID.
4. If the context comes from the user's uploaded documents, mention which document type it came from.
5. If the context does NOT contain relevant information for the question, say so honestly and provide your best general knowledge with a disclaimer.
6. Keep responses concise but thorough (2-4 paragraphs).
7. Use simple language a policyholder can understand.
8. Always remind users this is informational, not legal advice."""


def _format_context(user_chunks: List[Dict], kb_chunks: List[Dict]) -> str:
    """Format retrieved chunks into a context string for the LLM."""
    context_parts = []
    
    if user_chunks:
        context_parts.append("=== FROM YOUR UPLOADED DOCUMENTS ===")
        for i, chunk in enumerate(user_chunks, 1):
            source = chunk.get("metadata", {}).get("file_type", "document")
            filename = chunk.get("metadata", {}).get("filename", "")
            score = chunk.get("score", 0)
            context_parts.append(
                f"\n[Document {i}] (Source: {source}"
                f"{', File: ' + filename if filename else ''}"
                f", Relevance: {score:.0%})\n{chunk['text']}"
            )
    
    if kb_chunks:
        context_parts.append("\n\n=== FROM IRDAI / MEDICAL KNOWLEDGE BASE ===")
        for i, chunk in enumerate(kb_chunks, 1):
            source_type = chunk.get("metadata", {}).get("type", "knowledge")
            title = chunk.get("metadata", {}).get("title", "")
            score = chunk.get("score", 0)
            context_parts.append(
                f"\n[Knowledge {i}] (Type: {source_type}"
                f"{', ' + title if title else ''}"
                f", Relevance: {score:.0%})\n{chunk['text']}"
            )
    
    return "\n".join(context_parts) if context_parts else ""


def retrieve_context(
    query: str,
    user_email: str = "default",
    top_k: int = 5,
) -> Tuple[List[Dict], List[Dict], str]:
    """
    Retrieve relevant context from both user docs and knowledge base.
    
    Returns: (user_chunks, kb_chunks, formatted_context_string)
    """
    user_chunks = search_user_docs(query, user_email=user_email, top_k=top_k)
    kb_chunks = search_knowledge_base(query, top_k=top_k)
    
    # Filter low-relevance results
    user_chunks = [c for c in user_chunks if c.get("score", 0) > 0.25]
    kb_chunks = [c for c in kb_chunks if c.get("score", 0) > 0.25]
    
    context_str = _format_context(user_chunks, kb_chunks)
    
    return user_chunks, kb_chunks, context_str


async def generate_rag_response(
    query: str,
    user_email: str = "default",
) -> Dict:
    """
    Full RAG pipeline: retrieve context -> build prompt -> generate response.
    Priority: Groq API -> Ollama -> context-only fallback.
    
    Returns dict with: response, model, sources, has_context
    """
    # Step 1: Retrieve relevant context
    user_chunks, kb_chunks, context_str = retrieve_context(query, user_email)
    
    has_context = bool(context_str.strip())
    
    # Step 2: Build the prompt
    if has_context:
        user_message = (
            f"CONTEXT:\n{context_str}\n\n"
            f"---\n\n"
            f"USER QUESTION: {query}\n\n"
            f"Please answer the question using the context provided above. "
            f"Cite specific documents or regulations when relevant."
        )
    else:
        user_message = query
    
    messages = [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    # Step 3A: Try Groq API first (fast, cloud-based)
    try:
        from app.services.groq_service import groq_chat
        groq_reply = await groq_chat(messages, max_tokens=1024, temperature=0.7)
        if groq_reply:
            return {
                "response": groq_reply,
                "model": "groq",
                "has_context": has_context,
                "sources": _build_source_citations(user_chunks, kb_chunks),
                "user_docs_used": len(user_chunks),
                "kb_docs_used": len(kb_chunks),
            }
    except Exception as e:
        print(f"[RAG] Groq failed (trying Ollama): {e}")
    
    # Step 3B: Try Ollama/local LLM
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                health = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                if health.status_code != 200:
                    raise ConnectionError("Ollama not available")
            except Exception:
                raise ConnectionError("Ollama not available")
            
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 800,
                    },
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("message", {}).get("content", "")
                if reply:
                    return {
                        "response": reply,
                        "model": OLLAMA_MODEL,
                        "has_context": has_context,
                        "sources": _build_source_citations(user_chunks, kb_chunks),
                        "user_docs_used": len(user_chunks),
                        "kb_docs_used": len(kb_chunks),
                    }
                
    except ConnectionError as e:
        print(f"[RAG] Ollama not available: {e}")
    except httpx.TimeoutException:
        print("[RAG] Ollama timeout")
    except Exception as e:
        print(f"[RAG] LLM error: {e}")
    
    # Step 4: Fallback — return context directly without LLM
    if has_context:
        fallback_response = _build_fallback_response(query, user_chunks, kb_chunks)
        return {
            "response": fallback_response,
            "model": "rag-context-only",
            "has_context": True,
            "sources": _build_source_citations(user_chunks, kb_chunks),
            "user_docs_used": len(user_chunks),
            "kb_docs_used": len(kb_chunks),
        }
    
    # No context and no LLM — return None to signal fallback to keyword system
    return None


def _build_source_citations(
    user_chunks: List[Dict],
    kb_chunks: List[Dict],
) -> List[Dict]:
    """Build a list of source citations for the response."""
    sources = []
    
    for chunk in user_chunks:
        meta = chunk.get("metadata", {})
        sources.append({
            "type": "uploaded_document",
            "file_type": meta.get("file_type", ""),
            "filename": meta.get("filename", ""),
            "relevance": round(chunk.get("score", 0) * 100),
        })
    
    for chunk in kb_chunks:
        meta = chunk.get("metadata", {})
        sources.append({
            "type": meta.get("type", "knowledge_base"),
            "title": meta.get("title", ""),
            "source": meta.get("source", ""),
            "relevance": round(chunk.get("score", 0) * 100),
        })
    
    # Deduplicate by title/filename
    seen = set()
    unique_sources = []
    for s in sources:
        key = s.get("filename") or s.get("title") or str(s)
        if key not in seen:
            seen.add(key)
            unique_sources.append(s)
    
    return unique_sources


def _build_fallback_response(
    query: str,
    user_chunks: List[Dict],
    kb_chunks: List[Dict],
) -> str:
    """Build a response from retrieved context when LLM is not available."""
    parts = []
    
    parts.append(
        "🔍 **I found relevant information in my knowledge base** "
        "(Ollama/LLM is not running, so I'm showing retrieved context directly):\n"
    )
    
    if user_chunks:
        parts.append("\n**From your uploaded documents:**")
        for i, chunk in enumerate(user_chunks[:3], 1):
            filename = chunk.get("metadata", {}).get("filename", "")
            source = f" ({filename})" if filename else ""
            parts.append(f"\n{i}. {source}\n> {chunk['text'][:300]}{'...' if len(chunk['text']) > 300 else ''}")
    
    if kb_chunks:
        parts.append("\n\n**From IRDAI/Medical knowledge base:**")
        for i, chunk in enumerate(kb_chunks[:3], 1):
            title = chunk.get("metadata", {}).get("title", "")
            source = f" — {title}" if title else ""
            parts.append(f"\n{i}.{source}\n> {chunk['text'][:300]}{'...' if len(chunk['text']) > 300 else ''}")
    
    parts.append(
        "\n\n💡 *To get AI-generated answers, install Ollama and run "
        "`ollama pull mistral` (or `llama3.2`) in your terminal.*"
    )
    
    return "\n".join(parts)
