-- ══════════════════════════════════════════════════════════════
--  ClaimAssist AI — Complete Supabase Schema
--  Paste in: Supabase Dashboard → SQL Editor → New Query → Run
--  Run ONLY the sections you don't already have.
-- ══════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────
-- SECTION A: Auth tables (SKIP if already created)
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(255) NOT NULL,
    is_verified   BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    last_login    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.otp_records (
    id         SERIAL PRIMARY KEY,
    email      VARCHAR(255) NOT NULL,
    otp_code   VARCHAR(6) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS public.password_reset_tokens (
    id         SERIAL PRIMARY KEY,
    email      VARCHAR(255) NOT NULL,
    token      VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    used       BOOLEAN DEFAULT FALSE
);

-- ──────────────────────────────────────────────────────────────
-- SECTION B: Documents table
-- Stores uploaded insurance documents per user
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.documents (
    id             SERIAL PRIMARY KEY,
    file_id        VARCHAR(50) NOT NULL,          -- short UUID used in file path
    user_email     VARCHAR(255) NOT NULL,
    filename       VARCHAR(500) NOT NULL,
    file_type      VARCHAR(50) NOT NULL,          -- policy, medical_report, denial_letter, medical_bill
    file_path      TEXT NOT NULL,                 -- relative server path
    file_size      INTEGER DEFAULT 0,             -- bytes
    status         VARCHAR(30) DEFAULT 'uploaded',-- uploaded, processed, error
    ocr_source     VARCHAR(30) DEFAULT 'none',    -- groq_vision, local_ocr, none
    extracted_text TEXT DEFAULT '',               -- full OCR output
    metadata       JSONB DEFAULT '{}',            -- key-value pairs from OCR
    rag_indexed    BOOLEAN DEFAULT FALSE,         -- whether indexed in FAISS
    rag_chunks     INTEGER DEFAULT 0,
    upload_date    TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- SECTION C: Claim analyses / pipeline results
-- One record per pipeline run
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.claim_analyses (
    id                    SERIAL PRIMARY KEY,
    claim_id              VARCHAR(20) UNIQUE NOT NULL,   -- CLM-XXXXXX
    user_email            VARCHAR(255) NOT NULL,
    patient_name          VARCHAR(255),
    insurer_name          VARCHAR(255),
    claim_amount          NUMERIC(12, 2),
    denial_reason         TEXT,
    status                VARCHAR(30) DEFAULT 'completed',
    policy_alignment_score NUMERIC(5, 2) DEFAULT 0,
    medical_necessity_score NUMERIC(5, 2) DEFAULT 0,
    appeal_strength       JSONB DEFAULT '{}',            -- {label, overall_score, factors}
    discrepancies         JSONB DEFAULT '[]',
    pipeline_results      JSONB DEFAULT '{}',            -- full agent outputs
    recommendation        TEXT,
    analyzed_at           TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- SECTION D: Appeal letters
-- Generated appeal letters linked to claim analyses
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.appeal_letters (
    id                SERIAL PRIMARY KEY,
    claim_id          VARCHAR(20) NOT NULL REFERENCES public.claim_analyses(claim_id) ON DELETE CASCADE,
    user_email        VARCHAR(255) NOT NULL,
    appeal_text       TEXT NOT NULL,
    tone              VARCHAR(30) DEFAULT 'formal',     -- formal, assertive, empathetic
    citations         JSONB DEFAULT '[]',
    regulations_cited JSONB DEFAULT '[]',
    confidence_score  NUMERIC(5, 2) DEFAULT 0,
    status            VARCHAR(30) DEFAULT 'generated',  -- generated, sent, accepted, rejected
    generated_at      TIMESTAMPTZ DEFAULT NOW(),
    sent_at           TIMESTAMPTZ
);

-- ──────────────────────────────────────────────────────────────
-- SECTION E: Chat history
-- Per-user conversation history with the AI chatbot
-- ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id         SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    role       VARCHAR(10) NOT NULL,              -- user, assistant
    content    TEXT NOT NULL,
    model      VARCHAR(60),                       -- groq, ollama, rag-context-only
    has_context BOOLEAN DEFAULT FALSE,            -- whether RAG retrieved any context
    sources    JSONB DEFAULT '[]',                -- RAG source citations
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────────
-- SECTION F: Indexes for all tables
-- ──────────────────────────────────────────────────────────────
-- Auth
CREATE INDEX IF NOT EXISTS idx_users_email        ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_otp_email          ON public.otp_records(email);
CREATE INDEX IF NOT EXISTS idx_reset_email        ON public.password_reset_tokens(email);
CREATE INDEX IF NOT EXISTS idx_reset_token        ON public.password_reset_tokens(token);

-- Documents
CREATE INDEX IF NOT EXISTS idx_docs_user_email    ON public.documents(user_email);
CREATE INDEX IF NOT EXISTS idx_docs_file_id       ON public.documents(file_id);
CREATE INDEX IF NOT EXISTS idx_docs_file_type     ON public.documents(file_type);

-- Claims
CREATE INDEX IF NOT EXISTS idx_claims_user_email  ON public.claim_analyses(user_email);
CREATE INDEX IF NOT EXISTS idx_claims_claim_id    ON public.claim_analyses(claim_id);

-- Appeals
CREATE INDEX IF NOT EXISTS idx_appeals_claim_id   ON public.appeal_letters(claim_id);
CREATE INDEX IF NOT EXISTS idx_appeals_user_email ON public.appeal_letters(user_email);

-- Chat
CREATE INDEX IF NOT EXISTS idx_chat_user_email    ON public.chat_messages(user_email);
CREATE INDEX IF NOT EXISTS idx_chat_created_at    ON public.chat_messages(created_at);

-- ──────────────────────────────────────────────────────────────
-- SECTION G: Row Level Security (RLS)
-- ──────────────────────────────────────────────────────────────
ALTER TABLE public.users                   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.otp_records             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.password_reset_tokens   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.claim_analyses          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.appeal_letters          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages           ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to avoid errors on re-run
DO $$
BEGIN
    DROP POLICY IF EXISTS "Allow all for users"             ON public.users;
    DROP POLICY IF EXISTS "Allow all for otp"              ON public.otp_records;
    DROP POLICY IF EXISTS "Allow all for tokens"           ON public.password_reset_tokens;
    DROP POLICY IF EXISTS "Allow all for documents"        ON public.documents;
    DROP POLICY IF EXISTS "Allow all for claim_analyses"   ON public.claim_analyses;
    DROP POLICY IF EXISTS "Allow all for appeal_letters"   ON public.appeal_letters;
    DROP POLICY IF EXISTS "Allow all for chat_messages"    ON public.chat_messages;
END $$;

-- Allow service key (backend) full access to all tables
CREATE POLICY "Allow all for users"           ON public.users           FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for otp"             ON public.otp_records     FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for tokens"          ON public.password_reset_tokens FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for documents"       ON public.documents       FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for claim_analyses"  ON public.claim_analyses  FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for appeal_letters"  ON public.appeal_letters  FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for chat_messages"   ON public.chat_messages   FOR ALL USING (true) WITH CHECK (true);

-- ──────────────────────────────────────────────────────────────
-- SECTION H: Auto-cleanup for expired OTPs (optional)
-- ──────────────────────────────────────────────────────────────
-- Removes OTP records older than 24h automatically via cron
-- Requires pg_cron extension. Enable in Supabase → Extensions first.
-- SELECT cron.schedule('cleanup-otps', '0 * * * *',
--   $$DELETE FROM public.otp_records WHERE expires_at < NOW()$$);

-- ──────────────────────────────────────────────────────────────
-- VERIFY: list all tables created
-- ──────────────────────────────────────────────────────────────
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
