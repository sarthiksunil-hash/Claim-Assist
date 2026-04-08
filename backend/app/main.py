"""
ClaimAssist AI - FastAPI Backend
Agentic LLM Framework for Automated Health Insurance Claim Appeals
"""

from fastapi import FastAPI, Header
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

from app.routers import documents, claims, appeals, knowledge, auth, pipeline, chat
from app.database.db import engine, Base
from app.middleware.jwt_middleware import JWTMiddleware

load_dotenv()

app = FastAPI(
    title="ClaimAssist AI API",
    description="Agentic LLM Framework for Automated Health Insurance Claim Appeals using Policy-Medical Evidence Alignment and Insurance Knowledge Graphs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Authentication middleware
app.add_middleware(JWTMiddleware)

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[DB] Table creation warning: {e}")

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

# Mount static files for uploaded documents
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(claims.router, prefix="/api/claims", tags=["Claims"])
app.include_router(appeals.router, prefix="/api/appeals", tags=["Appeals"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Graph"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Agent Pipeline"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "ClaimAssist AI API",
        "version": "1.0.0"
    }


# ── Startup event: index knowledge bases into ChromaDB ──
@app.on_event("startup")
async def startup_index_knowledge_bases():
    """Index IRDAI and medical knowledge bases into ChromaDB on startup."""
    try:
        from app.services.vector_store import index_knowledge_bases
        indexed = index_knowledge_bases()
        if indexed:
            print("[Startup] Knowledge bases indexed into ChromaDB")
        else:
            print("[Startup] Knowledge base indexing skipped or failed (non-fatal)")
    except Exception as e:
        print(f"[Startup] KB indexing error (non-fatal): {e}")


@app.get("/api/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats(x_user_email: Optional[str] = Header(None)):
    """Get dashboard statistics from Supabase — real counts per user."""
    user_email = x_user_email or "default"
    from app.database.supabase_repo import get_dashboard_stats as repo_stats
    return repo_stats(user_email)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
