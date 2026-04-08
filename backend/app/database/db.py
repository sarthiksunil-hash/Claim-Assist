"""
Database configuration:
- Supabase REST API for user authentication (users, OTP, password reset)
- Local SQLite for documents, claims, appeals (session-specific data)
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

# ═══════════════════════════════════════════════════════════════
#  SUPABASE CLIENT (for user auth via REST API)
# ═══════════════════════════════════════════════════════════════

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Client | None = None

if SUPABASE_URL and SUPABASE_KEY and "your-project" not in SUPABASE_URL:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[DB] Supabase REST API client initialized successfully!")
        # Verify tables exist
        try:
            supabase.table("users").select("count", count="exact").limit(0).execute()
            print("[DB] ✅ Supabase 'users' table found — auth will use Supabase")
        except Exception as table_err:
            err_msg = str(table_err)
            if "42P01" in err_msg or "does not exist" in err_msg.lower() or "not found" in err_msg.lower():
                print("[DB] ⚠️  Supabase tables NOT FOUND!")
                print("[DB]    → Run the SQL in 'backend/supabase_setup.sql' in your Supabase Dashboard SQL Editor")
                print("[DB]    → Until then, auth will use local SQLite as fallback")
                supabase = None
            else:
                print(f"[DB] ⚠️  Supabase table check warning: {err_msg[:100]}")
                print("[DB]    → Auth will use local SQLite as fallback")
                supabase = None
    except Exception as e:
        print(f"[DB] Supabase client init failed: {e}")
        supabase = None
else:
    print("[DB] Supabase URL/Key not configured — using local SQLite for auth")


def get_supabase() -> Client | None:
    """Get Supabase client instance."""
    return supabase


# ═══════════════════════════════════════════════════════════════
#  LOCAL SQLITE (for documents, claims, appeals)
# ═══════════════════════════════════════════════════════════════

DATABASE_URL = "sqlite:///./claimassist.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
print("[DB] Using local SQLite for documents/claims storage")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ──── SQLite Models (documents, claims, appeals, chat) ─────────

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    file_id = Column(String(50), index=True)
    user_email = Column(String(255), nullable=False, index=True, default="default")
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="uploaded")
    ocr_source = Column(String(50), default="none")
    extracted_text = Column(Text, default="")
    metadata_json = Column(JSON, default={})
    rag_indexed = Column(Boolean, default=False)
    rag_chunks = Column(Integer, default=0)


class ClaimAnalysis(Base):
    __tablename__ = "claim_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    claim_id = Column(String(50), index=True)
    user_email = Column(String(255), nullable=False, index=True, default="default")
    patient_name = Column(String(255))
    insurer_name = Column(String(255))
    claim_amount = Column(Float)
    denial_reason = Column(Text)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")
    discrepancies = Column(JSON, default=[])
    policy_alignment_score = Column(Float, default=0.0)
    medical_necessity_score = Column(Float, default=0.0)
    appeal_strength = Column(JSON, default={})
    pipeline_results = Column(JSON, default={})
    recommendation = Column(Text, default="")


class AppealLetter(Base):
    __tablename__ = "appeal_letters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    claim_id = Column(String(50))
    user_email = Column(String(255), nullable=False, index=True, default="default")
    appeal_text = Column(Text)
    tone = Column(String(50), default="formal")
    citations = Column(JSON, default=[])
    regulations_cited = Column(JSON, default=[])
    generated_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="draft")
    confidence_score = Column(Float, default=0.0)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_email = Column(String(255), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    model = Column(String(100), default="")
    has_context = Column(Boolean, default=False)
    sources = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)


# ──── KEEP SQLite models for backward compat (auth fallback) ──

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class OTPRecord(Base):
    __tablename__ = "otp_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)


# Create all SQLite tables
try:
    Base.metadata.create_all(bind=engine)
    print("[DB] All local tables created/verified successfully")
except Exception as e:
    print(f"[DB] Table creation error: {e}")


# Dependency to get database session (for SQLite)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
