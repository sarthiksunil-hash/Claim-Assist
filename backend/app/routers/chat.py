"""
Chat Router - AI chatbot for insurance guidance.
Pipeline: RAG (retrieve from user docs + KB) → Ollama/LLM → keyword fallback.
Covers IRDAI regulations, insurance terminology, claim processes, and appeal strategies.
"""

from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional, List
import httpx
import json as _json
import os
import pathlib as _pathlib
import re

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

SYSTEM_PROMPT = """You are ClaimAssist AI, a knowledgeable and friendly assistant specializing in Indian health insurance claims, IRDAI (Insurance Regulatory and Development Authority of India) regulations, and medical insurance terminology.

Your expertise includes:
1. **IRDAI Regulations**: Circulars, guidelines, Master Circulars on health insurance, TPA regulations, claim processing timelines, grievance redressal mechanisms
2. **Health Insurance Terms**: Sum insured, deductibles, co-pay, sub-limits, waiting periods, PED (Pre-Existing Disease) exclusions, cashless vs reimbursement claims, network hospitals, TPA (Third Party Administrator)
3. **Claim Process**: How to file a claim, required documents, timelines, what to do when a claim is denied, how appeals work, Insurance Ombudsman process
4. **Medical Insurance Policies**: Coverage types (individual, family floater, group), riders, exclusions, inclusions, renewal terms, portability
5. **Appeal Strategies**: How to challenge claim denials, what evidence to gather, IRDAI complaint process, Consumer Forum approach
6. **Indian Healthcare Context**: Common treatments, ICD-10 codes, hospital billing practices, cashless authorization

Guidelines:
- Always be accurate and cite IRDAI regulation numbers when relevant
- If you don't know something, say so honestly rather than guessing
- Keep responses concise but thorough (2-4 paragraphs maximum)
- Use simple language that a policyholder can understand
- When explaining legal or regulatory concepts, give practical examples
- Always remind users that your advice is informational, not legal advice
- If asked about specific claim situations, ask for relevant details before advising"""


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    type: str
    model: str
    sources: Optional[List[dict]] = None
    has_context: bool = False


async def query_ollama(message: str) -> tuple[str, str]:
    """Send a message to Ollama and get a response."""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                health = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                if health.status_code != 200:
                    return _smart_response(message), "claimassist-ai"
            except Exception:
                return _smart_response(message), "claimassist-ai"

            # Try the model
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": message},
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 500,
                    },
                },
            )

            if response.status_code == 200:
                data = response.json()
                reply = data.get("message", {}).get("content", "")
                if reply:
                    return reply, OLLAMA_MODEL

            if response.status_code == 404:
                return (
                    f"The {OLLAMA_MODEL} model is not downloaded. Run `ollama pull {OLLAMA_MODEL}` in your terminal to download it. "
                    "In the meantime, I'll use my built-in knowledge to help you.\n\n"
                    + _smart_response(message),
                    "claimassist-ai",
                )

            return _smart_response(message), "claimassist-ai"

    except httpx.TimeoutException:
        return (
            "The AI model is taking too long to respond. This can happen on the first query. "
            "Let me help you with my built-in knowledge:\n\n" + _smart_response(message),
            "claimassist-ai",
        )
    except Exception as e:
        print(f"[Chat] Ollama error: {e}")
        return _smart_response(message), "claimassist-ai"


# ═══════════════════════════════════════════════════════════
#  KNOWLEDGE BASE — loaded from external JSON file
# ═══════════════════════════════════════════════════════════

_KB_PATH = _pathlib.Path(__file__).resolve().parent.parent / "data" / "insurance_kb.json"


def _load_kb() -> dict:
    """Load knowledge base from JSON file (cached at module level)."""
    try:
        with open(_KB_PATH, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception as e:
        print(f"[Chat] Failed to load KB from {_KB_PATH}: {e}")
        return {"categories": {}, "quick_responses": {}, "default_response_template": ""}


_KB_DATA = _load_kb()
KNOWLEDGE_BASE = _KB_DATA.get("categories", {})
_QUICK_RESPONSES = _KB_DATA.get("quick_responses", {})
_DEFAULT_TEMPLATE = _KB_DATA.get("default_response_template", "")


def _smart_response(message: str) -> str:
    """Provide intelligent responses using the knowledge base."""
    msg = message.lower().strip()

    # Check each knowledge base category (scored keyword match)
    best_match = None
    best_score = 0

    for category, data in KNOWLEDGE_BASE.items():
        score = 0
        for keyword in data.get("keywords", []):
            if keyword in msg:
                score += len(keyword.split())
        if score > best_score:
            best_score = score
            best_match = category

    if best_match and best_score > 0:
        return KNOWLEDGE_BASE[best_match]["response"]

    # Check quick responses (greeting, thanks, help, etc.)
    for _qr_key, qr_data in _QUICK_RESPONSES.items():
        if any(w in msg for w in qr_data.get("keywords", [])):
            return qr_data["response"]

    # Default fallback
    if _DEFAULT_TEMPLATE:
        return _DEFAULT_TEMPLATE.replace("{message}", message)

    return (
        f"I understand you're asking about: **\"{message}\"**. "
        "Try asking about PED, IRDAI regulations, claim process, or appeals!"
    )


# ═══════════════════════════════════════════════════════════
#  CHAT ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("/")
async def chat(request: ChatRequest, x_user_email: Optional[str] = Header(None)):
    """Chat with the AI assistant. Uses RAG pipeline → Ollama → keyword fallback."""
    user_email = x_user_email or "default"
    if not request.message.strip():
        return ChatResponse(
            response="Please send a message and I'll help you with insurance-related queries!",
            type="greeting",
            model="system",
        )

    # ── Persist the user message to Supabase ──
    try:
        from app.database.supabase_repo import save_chat_message
        save_chat_message(user_email, "user", request.message)
    except Exception as e:
        print(f"[Chat] Failed to save user message: {e}")

    # ── Step 1: Try RAG pipeline (retrieve + generate) ──
    try:
        from app.services.rag_service import generate_rag_response
        rag_result = await generate_rag_response(
            query=request.message,
            user_email=user_email,
        )
        if rag_result:
            msg_lower = request.message.lower()
            if any(w in msg_lower for w in ["irdai", "regulation", "rule", "law"]):
                resp_type = "regulation"
            elif any(w in msg_lower for w in ["denial", "denied", "reject", "appeal"]):
                resp_type = "info"
            elif any(w in msg_lower for w in ["hello", "hi", "hey", "help"]):
                resp_type = "greeting"
            else:
                resp_type = "info"

            ai_response = rag_result["response"]
            ai_model = rag_result.get("model", "rag")

            # Persist AI response
            try:
                save_chat_message(
                    user_email, "assistant", ai_response,
                    model=ai_model,
                    has_context=rag_result.get("has_context", False),
                    sources=rag_result.get("sources"),
                )
            except Exception:
                pass

            return ChatResponse(
                response=ai_response,
                type=resp_type,
                model=ai_model,
                sources=rag_result.get("sources"),
                has_context=rag_result.get("has_context", False),
            )
    except Exception as e:
        print(f"[Chat] RAG error (falling back): {e}")

    # ── Step 2: Fallback to direct Ollama (no retrieval) ──
    response_text, model = await query_ollama(request.message)

    # Persist AI response
    try:
        from app.database.supabase_repo import save_chat_message
        save_chat_message(user_email, "assistant", response_text, model=model)
    except Exception:
        pass

    # Determine response type
    msg_lower = request.message.lower()
    if any(w in msg_lower for w in ["irdai", "regulation", "rule", "law"]):
        resp_type = "regulation"
    elif any(w in msg_lower for w in ["denial", "denied", "reject", "appeal"]):
        resp_type = "info"
    elif any(w in msg_lower for w in ["hello", "hi", "hey", "help"]):
        resp_type = "greeting"
    else:
        resp_type = "info"

    return ChatResponse(
        response=response_text,
        type=resp_type,
        model=model,
    )


@router.get("/")
async def chat_get(message: str = "", x_user_email: Optional[str] = Header(None)):
    """Chat with AI assistant (GET endpoint)."""
    request = ChatRequest(message=message)
    return await chat(request, x_user_email=x_user_email)


@router.get("/history")
async def get_chat_history_endpoint(x_user_email: Optional[str] = Header(None)):
    """Return past chat messages for the current user from Supabase."""
    user_email = x_user_email or "default"
    try:
        from app.database.supabase_repo import get_chat_history
        messages = get_chat_history(user_email, limit=50)
        return {"messages": messages, "total": len(messages)}
    except Exception as e:
        print(f"[Chat] History error: {e}")
        return {"messages": [], "total": 0}
