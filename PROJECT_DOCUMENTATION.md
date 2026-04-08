# ClaimAssist AI

### Agentic LLM Framework for Automated Health Insurance Claim Appeals
**Using Policy-Medical Evidence Alignment and Insurance Knowledge Graphs**

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Tech Stack](#-tech-stack)
3. [Architecture](#-architecture)
4. [Project Structure](#-project-structure)
5. [Features](#-features)
6. [Multi-Agent Pipeline](#-multi-agent-pipeline)
7. [Database Design](#-database-design)
8. [API Endpoints](#-api-endpoints)
9. [Frontend Pages](#-frontend-pages)
10. [Setup & Installation](#-setup--installation)
11. [Environment Variables](#-environment-variables)
12. [Running the Application](#-running-the-application)
13. [Supabase Setup](#-supabase-setup)
14. [Chatbot (AI Assistant)](#-chatbot-ai-assistant)
15. [Authentication Flow](#-authentication-flow)
16. [Screenshots & Workflow](#-screenshots--workflow)
17. [Team Contributions](#-team-contributions)

---

## 🎯 Project Overview

**ClaimAssist AI** is an intelligent, full-stack platform that helps policyholders fight unfair health insurance claim denials. It uses a **multi-agent AI pipeline** to analyze insurance documents, identify IRDAI regulation violations, validate medical necessity, and automatically generate professional appeal letters with regulatory citations.

### Problem Statement
Health insurance claim denials in India are increasing, and most policyholders lack the legal and medical knowledge to challenge them. Manual appeal processes are time-consuming and require expertise in IRDAI regulations, policy terms, and medical coding.

### Solution
An AI-powered platform that:
- **Extracts information** from uploaded documents using OCR
- **Analyzes claims** through 4 specialized AI agents
- **Identifies violations** of IRDAI regulations
- **Generates appeal letters** with proper legal citations
- **Provides a chatbot** for insurance guidance
- **Stores user data** securely in Supabase PostgreSQL

---

## 🛠️ Tech Stack

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| **Next.js** | 14.2.35 | React framework (App Router) |
| **React** | 18.x | UI library |
| **TypeScript** | 5.x | Type-safe JavaScript |
| **Chakra UI** | 2.8.2 | Component library & styling |
| **Framer Motion** | 10.16.5 | Animations & transitions |
| **Axios** | 1.13.6 | HTTP client for API calls |
| **React Icons** | 5.6.0 | Icon library (Feather icons) |
| **Emotion** | 11.x | CSS-in-JS (Chakra UI dependency) |

### Backend
| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Backend language |
| **FastAPI** | 0.104.1 | High-performance async API framework |
| **Uvicorn** | 0.24.0 | ASGI server |
| **SQLAlchemy** | 2.0.23 | ORM for database operations |
| **Pydantic** | 2.5.2 | Data validation & serialization |
| **Supabase Python** | 2.3.0 | Supabase REST API client |
| **psycopg2-binary** | 2.9.9 | PostgreSQL adapter |
| **httpx** | 0.25.2 | Async HTTP client (for Ollama) |
| **python-dotenv** | 1.0.0 | Environment variable management |
| **python-multipart** | 0.0.6 | File upload handling |

### AI / ML / NLP Services
| Technology | Purpose |
|---|---|
| **Tesseract OCR** | Optical Character Recognition for documents |
| **pytesseract** | Python wrapper for Tesseract |
| **pdfplumber** | PDF text extraction |
| **PyPDF2** | PDF processing |
| **pdf2image** | PDF to image conversion (for OCR) |
| **Ollama** (optional) | Local LLM for the AI chatbot (Mistral model) |

### Database
| Technology | Purpose |
|---|---|
| **Supabase PostgreSQL** | Cloud database for user auth (REST API) |
| **SQLite** | Local database for documents, claims, appeals |

### Email / SMTP
| Technology | Purpose |
|---|---|
| **Gmail SMTP** | OTP delivery & password reset emails |
| **smtplib** | Python SMTP library |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14)                 │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐ │
│  │  Login/   │ │  Upload   │ │ Pipeline │ │  Appeal   │ │
│  │  Signup   │ │  Docs     │ │  Agent   │ │ Generator │ │
│  └────┬─────┘ └─────┬─────┘ └────┬─────┘ └─────┬─────┘ │
│       │             │            │              │       │
│  ┌────┴─────┐ ┌─────┴─────┐ ┌───┴──────┐ ┌─────┴─────┐ │
│  │ Settings │ │  Reports  │ │Knowledge │ │  Chatbot  │ │
│  │  & Help  │ │           │ │  Graph   │ │  Widget   │ │
│  └──────────┘ └───────────┘ └──────────┘ └───────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │ Axios HTTP (port 3000 → 8000)
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                       │
│                                                         │
│  ┌─── API Routers ──────────────────────────────────┐   │
│  │ /api/auth/*        → Authentication & OTP        │   │
│  │ /api/documents/*   → Upload & OCR extraction     │   │
│  │ /api/pipeline/*    → Multi-Agent AI pipeline     │   │
│  │ /api/appeals/*     → Appeal letter generation    │   │
│  │ /api/claims/*      → Claim analysis              │   │
│  │ /api/knowledge/*   → Insurance knowledge graph   │   │
│  │ /api/chat/*        → AI chatbot (Ollama)         │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─── AI Services ──────────────────────────────────┐   │
│  │ OCR Agent      → Tesseract + PDF extraction      │   │
│  │ NLP Agent      → Entity extraction & sentiment   │   │
│  │ Policy Agent   → IRDAI regulation validation     │   │
│  │ Medical Agent  → ICD-10 & medical necessity      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─── Knowledge Bases ──────────────────────────────┐   │
│  │ Insurance KB   → IRDAI rules, policy terms       │   │
│  │ Medical KB     → ICD-10 codes, clinical guides   │   │
│  └──────────────────────────────────────────────────┘   │
└────────────┬────────────────────────┬───────────────────┘
             │                        │
             ▼                        ▼
   ┌─────────────────┐     ┌──────────────────┐
   │  Supabase Cloud │     │  Local SQLite    │
   │  (User Auth)    │     │  (Docs/Claims)   │
   └─────────────────┘     └──────────────────┘
```

---

## 📁 Project Structure

```
miniproject/
├── frontend/                          # Next.js 14 Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx               # Dashboard (home page)
│   │   │   ├── layout.tsx             # Root layout with Chakra UI
│   │   │   ├── providers.tsx          # Chakra UI provider wrapper
│   │   │   ├── globals.css            # Global styles & animations
│   │   │   ├── login/page.tsx         # Login / Signup / OTP / Forgot Password
│   │   │   ├── upload/page.tsx        # Document upload (drag & drop)
│   │   │   ├── analysis/page.tsx      # Claim analysis view
│   │   │   ├── pipeline/page.tsx      # Multi-agent pipeline execution
│   │   │   ├── appeal/page.tsx        # Appeal letter generation
│   │   │   ├── reports/page.tsx       # Reports & analytics dashboard
│   │   │   ├── knowledge/page.tsx     # Insurance knowledge graph
│   │   │   ├── settings/page.tsx      # User profile & theme settings
│   │   │   └── help/page.tsx          # Help center, FAQs & support
│   │   ├── components/
│   │   │   ├── Sidebar.tsx            # Navigation sidebar
│   │   │   ├── ChatWidget.tsx         # Floating AI chatbot
│   │   │   ├── AuthGuard.tsx          # Route protection component
│   │   │   └── StatsCard.tsx          # Dashboard statistics card
│   │   └── lib/
│   │       └── api.ts                 # Axios API client & endpoints
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                           # FastAPI Backend
│   ├── app/
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── routers/
│   │   │   ├── auth.py                # Authentication (signup, login, OTP, reset)
│   │   │   ├── documents.py           # Document upload & OCR processing
│   │   │   ├── pipeline.py            # Multi-agent pipeline orchestration
│   │   │   ├── appeals.py             # Appeal letter generation
│   │   │   ├── claims.py              # Claim analysis
│   │   │   ├── knowledge.py           # Insurance knowledge graph API
│   │   │   └── chat.py                # AI chatbot (Ollama + fallback)
│   │   ├── services/
│   │   │   ├── ocr_service.py         # Tesseract OCR + PDF text extraction
│   │   │   ├── nlp_service.py         # NLP entity extraction & sentiment
│   │   │   ├── policy_agent.py        # IRDAI regulation validation agent
│   │   │   ├── medical_agent.py       # Medical necessity verification agent
│   │   │   ├── appeal_generator.py    # Appeal letter template engine
│   │   │   ├── email_service.py       # SMTP email delivery (OTP & reset)
│   │   │   ├── insurance_kb.py        # Insurance knowledge base
│   │   │   └── medical_kb.py          # Medical knowledge base (ICD-10)
│   │   └── database/
│   │       └── db.py                  # Database config (Supabase + SQLite)
│   ├── uploads/                       # Uploaded document storage
│   ├── supabase_setup.sql             # SQL script for Supabase table creation
│   ├── requirements.txt               # Python dependencies
│   └── .env                           # Environment variables (secrets)
```

---

## ✨ Features

### 1. 🔐 Authentication System
- Email/password signup with **OTP email verification**
- Secure login with password hashing (SHA-256 + salt)
- **Forgot Password** with email reset links
- Session management via localStorage
- Route protection via `AuthGuard` component

### 2. 📄 Document Upload & OCR
- Drag-and-drop upload for 4 document types:
  - Policy Document
  - Medical Report
  - Denial Letter
  - Medical Bill
- Supported formats: PDF, JPG, JPEG, PNG, DOC, DOCX
- **Tesseract OCR** for text extraction from images
- **pdfplumber + PyPDF2** for PDF text extraction
- Key-value pair extraction (claim amounts, patient names, insurer names, denial reasons)

### 3. 🤖 Multi-Agent AI Pipeline
- 4 specialized AI agents analyze claims simultaneously
- Auto-fills claim details from OCR extraction
- Generates comprehensive analysis scores
- *(See detailed section below)*

### 4. 📝 Appeal Letter Generation
- Dynamic appeal letters based on actual claim data
- IRDAI regulation citations auto-inserted
- Conditional sections based on denial reason
- Copy-to-clipboard and download as text file
- Requires 3-step verification before generation

### 5. 📊 Reports & Analytics
- Appeal Strength Score
- Policy Alignment Score
- Medical Necessity Score
- Document processing metrics
- IRDAI violation count

### 6. 💬 AI Chatbot
- Powered by **Ollama** (local LLM — Mistral model)
- Comprehensive fallback knowledge base (works without Ollama)
- Covers: IRDAI regulations, PED, denials, appeals, insurance terms, claim process, waiting periods, medical necessity, cashless claims, policy types, portability, NCB
- Floating widget accessible on all pages

### 7. ⚙️ Settings
- Edit personal details (name, email, phone, organization)
- Light/Dark theme toggle with live preview
- Password change

### 8. ❓ Help & Support
- FAQ accordion with 8+ common questions
- Quick links: IRDAI website, Insurance Ombudsman, IGMS portal, Consumer Forum
- Contact form
- Company email: `claimassist.support@gmail.com`
- Support hours: Mon-Sat 9 AM - 6 PM IST

---

## 🤖 Multi-Agent Pipeline

The heart of ClaimAssist AI is a **4-agent pipeline** that analyzes insurance claims in parallel:

```
     ┌──────────────────────────────────────────┐
     │           UPLOADED DOCUMENTS              │
     │  (Policy, Medical Report, Denial Letter,  │
     │              Medical Bill)                 │
     └──────────────────┬───────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │   OCR AGENT     │
              │ (Text Extract)  │
              └────────┬────────┘
                       │  raw text
                       ▼
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ NLP      │  │ POLICY   │  │ MEDICAL  │
  │ AGENT    │  │ AGENT    │  │ AGENT    │
  │          │  │          │  │          │
  │ • Entity │  │ • IRDAI  │  │ • ICD-10 │
  │   extract│  │   rules  │  │   codes  │
  │ • Denial │  │ • Policy │  │ • Clinical│
  │   classif│  │   align  │  │   guides │
  │ • Sentim│  │ • Violat │  │ • Medical │
  │   analysis│ │   detect │  │   necess │
  └─────┬────┘  └────┬─────┘  └────┬─────┘
        │            │              │
        └────────────┼──────────────┘
                     ▼
           ┌──────────────────┐
           │  COMBINED RESULT  │
           │  • Scores         │
           │  • Violations     │
           │  • Recommendations│
           └──────────────────┘
```

### Agent Details

| Agent | Input | Output | Key Functions |
|---|---|---|---|
| **OCR Agent** | Document files | Extracted text, key-value pairs | Tesseract OCR, PDF text extraction, amount/name/reason parsing |
| **NLP Agent** | Extracted text | Entities, classifications, sentiment | Named entity recognition, denial reason classification, sentiment analysis |
| **Policy Agent** | Claim data + Insurance KB | IRDAI violations, policy alignment score | Regulation matching, waiting period validation, claim timeline checks |
| **Medical Agent** | Medical reports + Medical KB | Medical necessity score, ICD-10 mapping | Clinical guideline validation, procedure code matching, treatment necessity |

---

## 🗄️ Database Design

### Supabase PostgreSQL (Cloud — User Auth)

```sql
-- Users table
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name   VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    last_login  TIMESTAMPTZ
);

-- OTP records for email verification
CREATE TABLE otp_records (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL,
    otp_code    VARCHAR(6) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    expires_at  TIMESTAMPTZ NOT NULL
);

-- Password reset tokens
CREATE TABLE password_reset_tokens (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL,
    token       VARCHAR(100) UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    expires_at  TIMESTAMPTZ NOT NULL,
    used        BOOLEAN DEFAULT FALSE
);
```

### SQLite (Local — Session Data)

```sql
-- Uploaded documents
documents (id, filename, file_type, file_path, file_size, upload_date, status, extracted_text, metadata_json)

-- Claim analysis results
claim_analyses (id, claim_id, patient_name, insurer_name, claim_amount, denial_reason, analysis_date, status, discrepancies, policy_alignment_score, medical_necessity_score, appeal_strength, pipeline_results)

-- Generated appeal letters
appeal_letters (id, claim_id, appeal_text, citations, regulations_cited, generated_date, status, confidence_score)
```

---

## 🔌 API Endpoints

### Authentication (`/api/auth`)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/signup` | Register new user, sends OTP email |
| POST | `/login` | Authenticate user |
| POST | `/verify-otp` | Verify 6-digit OTP |
| POST | `/resend-otp` | Resend OTP to email |
| POST | `/forgot-password` | Send password reset email |
| POST | `/reset-password` | Reset password using token |

### Documents (`/api/documents`)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload` | Upload a document (multipart form) |
| GET | `/` | List all uploaded documents |
| GET | `/{id}` | Get document details |
| POST | `/{id}/process` | Process document with OCR |
| GET | `/extracted-details` | Get OCR-extracted key-value pairs |

### Pipeline (`/api/pipeline`)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/run` | Execute the 4-agent pipeline |
| GET | `/agent/{agentId}` | Get specific agent output |
| GET | `/agents` | List all agents and their status |
| GET | `/latest-result` | Get most recent pipeline result |
| GET | `/knowledge/insurance` | Get insurance knowledge base |
| GET | `/knowledge/medical` | Get medical knowledge base |

### Appeals (`/api/appeals`)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/generate` | Generate an appeal letter |
| GET | `/` | List generated appeals |
| GET | `/{id}` | Get specific appeal |

### Chat (`/api/chat`)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/` | Send message to AI chatbot |
| GET | `/` | Send message via query param |

### Dashboard (`/api/dashboard`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/stats` | Get dashboard statistics |

---

## 📱 Frontend Pages

| Page | Route | Description |
|---|---|---|
| **Login/Signup** | `/login` | Authentication with OTP verification & password reset |
| **Dashboard** | `/` (home) | Overview with stats cards, recent activity |
| **Upload Documents** | `/upload` | Drag-and-drop document uploader (4 types) |
| **Claim Analysis** | `/analysis` | View OCR-extracted claim details |
| **Agent Pipeline** | `/pipeline` | Run & monitor AI agents, view results |
| **Generate Appeal** | `/appeal` | Generate & download appeal letters |
| **Reports** | `/reports` | Analysis scores and metrics |
| **Knowledge Graph** | `/knowledge` | Browse insurance & medical knowledge |
| **Settings** | `/settings` | Profile editing, theme toggle, password change |
| **Help & Support** | `/help` | FAQs, resource links, contact form |

---

## 🚀 Setup & Installation

### Prerequisites
- **Node.js** 18+ and **npm**
- **Python** 3.10+
- **Tesseract OCR** installed and in PATH
- **Supabase** account (free tier works)
- **Gmail App Password** for SMTP (OTP emails)
- **Ollama** (optional, for AI chatbot LLM)

### Step 1: Clone the Repository
```bash
git clone <repo-url>
cd miniproject
```

### Step 2: Backend Setup
```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Additional OCR dependencies
pip install pytesseract pdfplumber PyPDF2 pdf2image Pillow
```

### Step 3: Frontend Setup
```bash
cd frontend

# Install dependencies
npm install
```

### Step 4: Configure Environment Variables
Create `backend/.env` (see [Environment Variables](#-environment-variables) section below).

### Step 5: Supabase Table Setup
Run the SQL in `backend/supabase_setup.sql` in your Supabase Dashboard SQL Editor.
*(See [Supabase Setup](#-supabase-setup) for details)*

### Step 6: Install Tesseract OCR
- **Windows**: Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### Step 7 (Optional): Install Ollama for AI Chatbot
```bash
# Install Ollama from https://ollama.com
# Then download the Mistral model:
ollama pull mistral
```

---

## 🔑 Environment Variables

Create a file at `backend/.env`:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_DB_URL=postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres

# Application Settings
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Email / SMTP Configuration
# For Gmail: Use an App Password (not your regular password)
# Generate at: https://myaccount.google.com/apppasswords
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_SENDER_NAME=ClaimAssist Support

# Optional: Ollama URL (default: http://localhost:11434)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

> ⚠️ **Important**: Never commit `.env` to version control. Add it to `.gitignore`.

---

## ▶️ Running the Application

### Start Backend (Terminal 1)
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Backend runs at: **http://localhost:8000**
API Docs (Swagger): **http://localhost:8000/docs**

### Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```
Frontend runs at: **http://localhost:3000**

### Start Ollama (Terminal 3 — Optional)
```bash
ollama serve
# In another terminal:
ollama run mistral
```

---

## ☁️ Supabase Setup

### 1. Create a Supabase Project
1. Go to [supabase.com](https://supabase.com) → Create a new project
2. Note down the **Project URL** and **anon/public API key**

### 2. Create Tables
1. Go to **SQL Editor** in your Supabase dashboard
2. Copy and run the contents of `backend/supabase_setup.sql`
3. This creates: `users`, `otp_records`, `password_reset_tokens`

### 3. Enable RLS Policies
The SQL script already includes RLS policies. Verify in **Authentication → Policies**.

### 4. Connection Method
The app uses **Supabase REST API** (over HTTPS) rather than direct PostgreSQL connection. This works on all networks without firewall issues.

---

## 💬 Chatbot (AI Assistant)

### How It Works
1. User sends a message via the floating ChatWidget
2. Frontend calls `POST /api/chat/` with the message
3. Backend tries **Ollama** first (local LLM):
   - If Ollama is running → sends to Mistral model with custom system prompt
   - If Ollama is not available → uses built-in knowledge base
4. Response is returned with type classification (info, regulation, greeting, error)

### Built-in Knowledge Base Topics
The fallback system covers 12+ topics with detailed responses:
- Pre-Existing Disease (PED) exclusions
- IRDAI regulations and circulars
- Claim denial handling (5-step guide)
- Appeal process (3 levels: Internal, Ombudsman, Consumer Forum)
- Insurance terminology (20+ terms defined)
- Claim filing process (cashless + reimbursement)
- Waiting periods
- Medical necessity
- Policy types (individual, floater, group, top-up, critical illness)
- Portability
- No Claim Bonus (NCB)
- Sum insured guidance

### Recommended Ollama Setup
```bash
# Install Ollama
# Download from https://ollama.com

# Pull the Mistral model (recommended)
ollama pull mistral

# The app auto-detects Ollama at http://localhost:11434
```

---

## 🔐 Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  SIGNUP   │────▶│ Send OTP │────▶│  Verify  │────▶│  LOGIN   │
│  (email,  │     │ via Email│     │   OTP    │     │ (success)│
│  password,│     │          │     │ (6-digit)│     │          │
│  name)    │     └──────────┘     └──────────┘     └──────────┘
└──────────┘                                              │
                                                          ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  FORGOT  │────▶│ Send     │────▶│  Reset   │────▶│  LOGIN   │
│ PASSWORD │     │ Reset    │     │ Password │     │ (new pw) │
│ (email)  │     │ Email    │     │ (token)  │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

### Security Features
- Password hashing: SHA-256 with application-specific salt
- OTP: 6-digit, expires in 10 minutes
- Reset tokens: Secure random (48 bytes), expires in 30 minutes
- Dual storage: Supabase (cloud) + SQLite (local fallback)
- Rate limiting: 30-second cooldown on OTP resend

---

## 📸 Screenshots & Workflow

### User Workflow
1. **Sign Up** → Enter email, password, name → Receive OTP → Verify email
2. **Login** → Enter credentials → Dashboard
3. **Upload Documents** → Upload policy, medical report, denial letter, bill
4. **Run Pipeline** → AI agents analyze documents → Auto-fill claim details
5. **View Reports** → See scores and analysis results
6. **Generate Appeal** → Verify details → Download appeal letter
7. **Use Chatbot** → Ask questions about insurance, IRDAI, claims

---

## 👥 Team Contributions

| Team Member | Role | Responsibilities |
|---|---|---|
| | Frontend Developer | Next.js pages, Chakra UI components, responsive design |
| | Backend Developer | FastAPI APIs, database design, authentication |
| | AI/ML Engineer | Multi-agent pipeline, OCR, NLP services |
| | Full Stack | Integration, deployment, testing |

---

## 📝 Key IRDAI Regulations Referenced

| Regulation | Key Point |
|---|---|
| Health Insurance Regulations, 2016 | PED waiting period max 48 months |
| TPA Guidelines, 2016 | Must cite specific policy clauses when denying |
| Master Circular on Health Insurance, 2020 | Lifelong renewability mandatory |
| Claim Settlement Timeline | 30 days after receiving all documents |
| Moratorium Period | No denial after 8 years of continuous coverage |
| Grievance Redressal | Response within 3 days, resolution within 15 days |

---

## 🔗 Useful Links

- **Supabase Dashboard**: [supabase.com/dashboard](https://supabase.com/dashboard)
- **IRDAI Official**: [irdai.gov.in](https://irdai.gov.in)
- **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Next.js Docs**: [nextjs.org/docs](https://nextjs.org/docs)
- **Chakra UI Docs**: [chakra-ui.com](https://chakra-ui.com)
- **Ollama**: [ollama.com](https://ollama.com)
- **Tesseract OCR**: [github.com/tesseract-ocr](https://github.com/tesseract-ocr/tesseract)

---

## 📄 License

This project is developed as an academic mini-project for educational purposes.

---

*Last updated: March 2026*
*Contact: claimassist.support@gmail.com*
