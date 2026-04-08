# ClaimAssist AI

## Agentic LLM Framework for Automated Health Insurance Claim Appeals Using Policy-Medical Evidence Alignment and Insurance Knowledge Graphs

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Proposed Solution](#3-proposed-solution)
4. [System Architecture](#4-system-architecture)
5. [Tech Stack](#5-tech-stack)
6. [Multi-Agent Pipeline](#6-multi-agent-pipeline)
7. [Frontend Pages & Features](#7-frontend-pages--features)
8. [Backend API Endpoints](#8-backend-api-endpoints)
9. [Database Design](#9-database-design)
10. [Knowledge Bases](#10-knowledge-bases)
11. [Key Features](#11-key-features)
12. [Project Structure](#12-project-structure)
13. [Setup & Installation](#13-setup--installation)
14. [Environment Variables](#14-environment-variables)
15. [Future Scope](#15-future-scope)

---

## 1. Project Overview

**ClaimAssist AI** is an intelligent, multi-agent platform designed to assist Indian health insurance policyholders in appealing wrongfully denied claims. It leverages **Large Language Models (LLMs)**, **Retrieval-Augmented Generation (RAG)**, and structured **Insurance + Medical Knowledge Bases** to automatically analyze uploaded documents, identify IRDAI regulation violations by insurers, verify medical necessity, and generate legally-grounded appeal letters.

| Attribute         | Detail                                                     |
| ----------------- | ---------------------------------------------------------- |
| **Project Type**  | Web Application (Full-Stack)                               |
| **Domain**        | Health Insurance / InsurTech / Legal-AI                    |
| **Architecture**  | Multi-Agent LLM Pipeline + RAG                             |
| **Target Users**  | Indian health insurance policyholders                      |
| **Regulation**    | IRDAI (Insurance Regulatory and Development Authority)     |

---

## 2. Problem Statement

Health insurance claim denials are a pervasive issue in India:

- **30-40% of health insurance claims** are initially denied or underpaid
- Policyholders often lack the legal and medical knowledge to effectively challenge denials
- Understanding IRDAI regulations and aligning medical evidence with policy terms is complex
- The appeal process is time-consuming, document-heavy, and intimidating for individuals
- Existing tools provide no automated, intelligent support for Indian health insurance appeals

**Key Challenges:**
- No centralized system to verify insurer compliance with IRDAI regulations
- Difficulty in mapping medical diagnoses to policy coverage
- Lack of awareness about policyholder rights under Indian law
- Manual appeal letter writing requires specialized legal/medical knowledge

---

## 3. Proposed Solution

ClaimAssist AI provides an **end-to-end automated appeal generation pipeline** that:

1. **Extracts** text and structured data from uploaded documents (policy, medical reports, denial letters) using OCR
2. **Classifies** the denial reason and extracts medical/legal entities using NLP
3. **Checks** insurer compliance against IRDAI regulations using a Policy Agent
4. **Verifies** medical necessity using a Medical Agent and knowledge base
5. **Generates** a comprehensive, legally-grounded appeal letter
6. **Provides** an AI chatbot for real-time guidance

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 14)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Dashboard │ │ Upload   │ │ Pipeline │ │ Appeal   │          │
│  │          │ │Documents │ │ Analysis │ │Generator │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Reports  │ │Knowledge │ │ Settings │ │Help &    │          │
│  │          │ │  Graph   │ │          │ │Support   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────────────────┐                                      │
│  │  AI Chat Widget      │  (Floating, available on all pages)  │
│  └──────────────────────┘                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API (axios)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│                                                                 │
│  ┌─────────────────── Agent Pipeline ──────────────────────┐    │
│  │                                                         │    │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌──────┐│    │
│  │  │ OCR Agent │→│NLP Agent  │→│Policy     │→│Medical││    │
│  │  │ (Groq    ││ │(Groq LLM)│ │Agent      │ │Agent  ││    │
│  │  │  Vision) ││ │           │ │(IRDAI KB) │ │(Med KB)││    │
│  │  └───────────┘  └───────────┘  └───────────┘  └──────┘│    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌──────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────┐ │
│  │Auth (JWT)│ │RAG + ChromaDB│ │Appeal Gen    │ │Email Svc  │ │
│  └──────────┘ └──────────────┘ └──────────────┘ └───────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Supabase    │  │  ChromaDB    │  │   SQLite (Local)     │  │
│  │ (PostgreSQL) │  │(Vector Store)│  │   (Fallback DB)      │  │
│  │              │  │              │  │                      │  │
│  │ • Users      │  │ • IRDAI KB   │  │ • Users              │  │
│  │ • Documents  │  │ • Medical KB │  │ • Claims             │  │
│  │ • Claims     │  │ • Doc Chunks │  │ • Analyses           │  │
│  │ • Analyses   │  │              │  │                      │  │
│  │ • Chats      │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Tech Stack

### Frontend

| Technology              | Purpose                                    | Version   |
| ----------------------- | ------------------------------------------ | --------- |
| **Next.js**             | React framework with SSR/SSG               | 14.2.35   |
| **React**               | UI component library                       | 18.x      |
| **TypeScript**          | Static type checking                       | 5.x       |
| **Chakra UI**           | Component library with theming             | 2.x       |
| **Axios**               | HTTP client for API calls                  | 1.x       |
| **React Icons (Fi)**    | Feather icon set                           | 5.x       |
| **next/font**           | Google Fonts (Inter) optimization          | Built-in  |

### Backend

| Technology              | Purpose                                    | Version   |
| ----------------------- | ------------------------------------------ | --------- |
| **FastAPI**             | High-performance async Python API          | 0.104.1   |
| **Uvicorn**             | ASGI server                                | 0.24.0    |
| **Pydantic**            | Request/response validation                | 2.5.2     |
| **SQLAlchemy**          | ORM for local SQLite fallback              | 2.0.23    |
| **PyJWT**               | JWT token authentication                   | ≥ 2.8.0   |
| **ReportLab**           | PDF generation for appeal letters          | ≥ 4.0     |
| **python-dotenv**       | Environment variable management            | 1.0.0     |

### AI / ML

| Technology              | Purpose                                    |
| ----------------------- | ------------------------------------------ |
| **Groq API**            | LLM inference (Llama 4 Scout/Maverick)     |
| **Groq Vision**         | OCR via vision models (Llama 3.2, Llama 4) |
| **ChromaDB**            | Vector database for embedding storage      |
| **Sentence Transformers** | Text embedding (all-MiniLM-L6-v2)        |
| **RAG Pipeline**        | Retrieval-Augmented Generation for chat    |
| **Semantic Chunking**   | Intelligent document splitting             |

### Database & Infrastructure

| Technology              | Purpose                                    |
| ----------------------- | ------------------------------------------ |
| **Supabase**            | Cloud PostgreSQL (primary data store)      |
| **ChromaDB**            | Vector store for knowledge base embeddings |
| **SQLite**              | Local fallback database                    |
| **SMTP (Gmail)**        | OTP email delivery for authentication      |

### LLM Models Used

| Model                                        | Use Case                    |
| -------------------------------------------- | --------------------------- |
| `meta-llama/llama-4-scout-17b-16e-instruct`  | Vision OCR (primary)        |
| `meta-llama/llama-4-maverick-17b-128e-instruct` | Vision OCR (fallback)    |
| `llama-3.2-90b-vision-preview`               | Vision OCR (fallback)       |
| `llama-3.3-70b-versatile`                    | NLP / Chat / Analysis       |
| `llama-3.1-8b-instant`                       | Fast fallback for chat      |
| `mixtral-8x7b-32768`                         | Extended-context fallback   |

---

## 6. Multi-Agent Pipeline

The core of ClaimAssist AI is a **4-agent sequential pipeline** that processes uploaded documents:

```
Documents (PDF/Images) → OCR Agent → NLP Agent → Policy Agent → Medical Agent
                                                                      ↓
                                                              Appeal Generator
```

### Agent 1: OCR Agent (Document Data Extraction)
- **Input:** Uploaded policy documents, medical reports, denial letters (PDF/images)
- **Technology:** Groq Vision API (Llama 4 Scout)
- **Output:** Extracted text, key-value pairs (patient name, policy number, hospital, claim amount, diagnosis)
- **Features:** Intelligent image conversion, multi-page PDF support, structured metadata extraction

### Agent 2: NLP Agent (Denial Classification & Entity Extraction)
- **Input:** Extracted text from OCR Agent
- **Technology:** Groq LLM (Llama 3.3-70b)
- **Output:** Denial category, confidence score, sentiment analysis, medical entities (conditions, medications, procedures), appeal window detection
- **Denial Categories:** Pre-existing condition, Policy exclusion, Insufficient documentation, Waiting period, Network restriction, Claim limit exceeded, Late filing, Other

### Agent 3: Policy Agent (IRDAI Compliance Check)
- **Input:** NLP output + IRDAI Knowledge Base
- **Technology:** RAG (ChromaDB + Groq LLM)
- **Output:** Policy alignment score (%), IRDAI violations found, insurer compliance issues, applicable regulations with citations
- **Knowledge Base:** 150+ IRDAI regulations, guidelines, and circulars

### Agent 4: Medical Agent (Medical Necessity Verification)
- **Input:** NLP output + Medical Knowledge Base
- **Technology:** RAG (ChromaDB + Groq LLM)
- **Output:** Medical necessity score (%), ICD-10 codes, treatment appropriateness, evidence-based justification, procedure verification
- **Knowledge Base:** Medical conditions, standard treatments, ICD-10 mappings

### Overall Assessment
After all 4 agents complete, the system produces:
- **Appeal Strength:** Strong / Moderate / Weak
- **Policy Alignment Score:** 0–100%
- **Medical Necessity Score:** 0–100%
- **IRDAI Violations Count**
- **IRDAI Verified Status**

---

## 7. Frontend Pages & Features

| # | Page                  | Route         | Description                                                    |
|---|----------------------|---------------|----------------------------------------------------------------|
| 1 | **Dashboard**        | `/`           | Overview with stats cards, recent claims table, quick actions   |
| 2 | **Upload Documents** | `/upload`     | Drag-and-drop file upload for PDF/images with OCR processing   |
| 3 | **Claim Data Extraction** | `/pipeline` | Form to enter claim details + run multi-agent analysis pipeline |
| 4 | **Analysis**         | `/analysis`   | Detailed view of analysis results per claim                    |
| 5 | **Generate Appeal**  | `/appeal`     | AI-generated appeal letter with PDF download                   |
| 6 | **Reports**          | `/reports`    | Statistics and analytics on processed claims                   |
| 7 | **Knowledge Graph**  | `/knowledge`  | Insurance policy–medical evidence relationship explorer        |
| 8 | **Settings**         | `/settings`   | Profile management, theme toggle (dark/light), password change |
| 9 | **Help & Support**   | `/help`       | FAQ, contact form, links to IRDAI & Insurance Ombudsman        |
| 10| **Login/Signup**     | `/login`      | Authentication with email/password, OTP verification, password reset |

### Reusable Components
| Component        | Description                                          |
|-----------------|------------------------------------------------------|
| `Sidebar`       | Persistent navigation with sections (Main, Tools, Settings) |
| `ChatWidget`    | Floating AI chatbot with RAG-powered responses       |
| `StatsCard`     | Dashboard metric cards with trend indicators         |
| `AuthGuard`     | Route protection — redirects unauthenticated users   |

### UI Features
- ✅ Dark / Light mode toggle with full theme persistence
- ✅ Responsive design with Chakra UI semantic tokens
- ✅ Animated transitions and micro-interactions
- ✅ Premium glassmorphism design aesthetic
- ✅ Real-time toast notifications for all operations

---

## 8. Backend API Endpoints

### Authentication (`/api/auth`)
| Method | Endpoint           | Description                          |
|--------|--------------------|--------------------------------------|
| POST   | `/signup`          | Create account with email + password |
| POST   | `/login`           | Authenticate and get JWT token       |
| POST   | `/verify-otp`      | Verify email with 6-digit OTP        |
| POST   | `/resend-otp`      | Resend OTP to email                  |
| POST   | `/forgot-password` | Send password reset link             |
| POST   | `/reset-password`  | Reset password with token            |

### Documents (`/api/documents`)
| Method | Endpoint              | Description                        |
|--------|-----------------------|------------------------------------|
| POST   | `/upload`             | Upload documents with OCR          |
| GET    | `/`                   | List user's uploaded documents     |
| GET    | `/extracted-details`  | Get OCR-extracted claim details    |
| DELETE | `/{document_id}`      | Delete a document                  |

### Pipeline (`/api/pipeline`)
| Method | Endpoint    | Description                              |
|--------|-------------|------------------------------------------|
| POST   | `/run`      | Run the full 4-agent analysis pipeline   |
| GET    | `/result`   | Get the latest pipeline result           |

### Appeals (`/api/appeals`)
| Method | Endpoint            | Description                       |
|--------|---------------------|-----------------------------------|
| POST   | `/generate`         | Generate appeal letter from analysis |
| GET    | `/`                 | List user's generated appeals     |
| GET    | `/download/{id}`    | Download appeal as PDF            |

### Claims (`/api/claims`)
| Method | Endpoint           | Description                        |
|--------|--------------------|------------------------------------|
| GET    | `/`                | List user's claims                 |
| GET    | `/{claim_id}`      | Get specific claim details         |

### Chat (`/api/chat`)
| Method | Endpoint           | Description                        |
|--------|--------------------|------------------------------------|
| POST   | `/message`         | Send message, get AI response      |
| GET    | `/history`         | Get user's chat history            |
| DELETE | `/history`         | Clear chat history                 |

### Knowledge Graph (`/api/knowledge`)
| Method | Endpoint           | Description                        |
|--------|--------------------|------------------------------------|
| GET    | `/search`          | Search IRDAI/medical knowledge     |
| GET    | `/stats`           | Knowledge base statistics          |

### Dashboard (`/api/dashboard`)
| Method | Endpoint           | Description                        |
|--------|--------------------|------------------------------------|
| GET    | `/stats`           | Per-user dashboard statistics      |

---

## 9. Database Design

### Supabase Tables

#### `users`
| Column            | Type        | Description                |
|-------------------|-------------|----------------------------|
| id                | UUID (PK)   | Unique user identifier     |
| email             | VARCHAR     | User email (unique)        |
| password_hash     | VARCHAR     | Bcrypt hashed password     |
| full_name         | VARCHAR     | User's full name           |
| email_verified    | BOOLEAN     | OTP verification status    |
| otp_code          | VARCHAR     | Current OTP (hashed)       |
| otp_expires_at    | TIMESTAMP   | OTP expiration time        |
| created_at        | TIMESTAMP   | Account creation time      |

#### `documents`
| Column            | Type        | Description                |
|-------------------|-------------|----------------------------|
| id                | UUID (PK)   | Document identifier        |
| user_email        | VARCHAR     | Owner's email              |
| filename          | VARCHAR     | Original filename          |
| file_type         | VARCHAR     | Document type (policy/med) |
| extracted_text    | TEXT        | OCR-extracted text         |
| metadata          | JSONB       | Structured key-value pairs |
| status            | VARCHAR     | Processing status          |
| created_at        | TIMESTAMP   | Upload timestamp           |

#### `claim_analyses`
| Column            | Type        | Description                |
|-------------------|-------------|----------------------------|
| id                | UUID (PK)   | Analysis identifier        |
| user_email        | VARCHAR     | Owner's email              |
| claim_id          | VARCHAR     | Associated claim ID        |
| pipeline_result   | JSONB       | Full pipeline output       |
| appeal_strength   | VARCHAR     | Strong/Moderate/Weak       |
| policy_score      | FLOAT       | Policy alignment (0-100)   |
| medical_score     | FLOAT       | Medical necessity (0-100)  |
| created_at        | TIMESTAMP   | Analysis timestamp         |

#### `chat_messages`
| Column            | Type        | Description                |
|-------------------|-------------|----------------------------|
| id                | UUID (PK)   | Message identifier         |
| user_email        | VARCHAR     | User's email               |
| role              | VARCHAR     | "user" or "assistant"      |
| content           | TEXT        | Message content            |
| created_at        | TIMESTAMP   | Message timestamp          |

---

## 10. Knowledge Bases

### IRDAI Insurance Knowledge Base (`insurance_kb.py`)
- **Size:** 150+ regulations, guidelines, and circulars
- **Source:** IRDAI official guidelines and regulations
- **Coverage:**
  - Health insurance claim settlement timelines
  - Policyholder rights and grievance redressal
  - Pre-existing disease (PED) definitions and coverage
  - Cashless and reimbursement claim procedures
  - IRDAI circular mandates for insurers
  - Waiting period regulations
  - Exclusion clause limitations
  - TPA (Third Party Administrator) obligations
  - Portability rules

### Medical Knowledge Base (`medical_kb.py`)
- **Size:** 100+ medical conditions and treatment protocols
- **Coverage:**
  - Common medical conditions with ICD-10 codes
  - Standard treatment protocols and procedures
  - Medical necessity criteria
  - Emergency vs. elective classification
  - Standard hospitalization durations
  - Diagnostic test requirements

### Vector Store (ChromaDB)
- **Embedding Model:** `all-MiniLM-L6-v2` (Sentence Transformers)
- **Collections:** `irdai_knowledge`, `medical_knowledge`, `document_chunks`
- **Purpose:** Semantic similarity search for RAG-powered responses

---

## 11. Key Features

| Feature                         | Description                                                        |
| ------------------------------- | ------------------------------------------------------------------ |
| 🔐 **Secure Authentication**    | JWT tokens, email OTP verification, password reset via email       |
| 📄 **Document OCR**             | Groq Vision-based extraction with multi-model fallback             |
| 🤖 **4-Agent Analysis Pipeline**| OCR → NLP → IRDAI Policy → Medical Necessity                      |
| 📊 **Appeal Strength Scoring**  | Combined policy alignment + medical necessity scoring              |
| 📝 **Appeal Letter Generation** | AI-generated, legally-grounded appeal with PDF download            |
| 💬 **RAG-Powered AI Chatbot**   | Context-aware guidance using IRDAI + medical knowledge bases       |
| 🌙 **Dark / Light Mode**        | Full theme support with Chakra UI semantic tokens                  |
| 📈 **Dashboard Analytics**      | Real-time stats on documents, claims, and appeals                  |
| 🔒 **Per-User Data Isolation**  | Every piece of data is scoped to the authenticated user            |
| 📱 **Responsive Design**        | Works across desktop and tablet form factors                       |
| ⚡ **Real-time Processing**      | Toast notifications, loading states, streaming updates             |
| 🏥 **ICD-10 Code Mapping**      | Automatic medical condition to ICD-10 code mapping                 |
| ⚖️ **IRDAI Violation Detection** | Identifies insurer non-compliance with Indian regulations          |
| 📋 **Claim History**            | Persistent record of all analyses and appeals per user             |

---

## 12. Project Structure

```
miniproject/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── database/
│   │   │   ├── db.py                  # SQLAlchemy engine + base models
│   │   │   ├── supabase_repo.py       # Supabase CRUD operations
│   │   │   ├── user_repo.py           # User management (signup, OTP, JWT)
│   │   │   └── jwt_utils.py           # JWT token generation/verification
│   │   ├── middleware/
│   │   │   └── jwt_middleware.py       # FastAPI middleware for auth
│   │   ├── models/
│   │   │   └── schemas.py             # Pydantic models
│   │   ├── routers/
│   │   │   ├── auth.py                # Authentication endpoints 
│   │   │   ├── documents.py           # Document upload + OCR
│   │   │   ├── pipeline.py            # Multi-agent pipeline orchestration
│   │   │   ├── appeals.py             # Appeal generation + PDF 
│   │   │   ├── claims.py              # Claim management
│   │   │   ├── chat.py                # AI chatbot with RAG
│   │   │   └── knowledge.py           # Knowledge base search
│   │   ├── services/
│   │   │   ├── ocr_service.py         # Agent 1: OCR text extraction
│   │   │   ├── nlp_service.py         # Agent 2: NLP denial classification
│   │   │   ├── policy_agent.py        # Agent 3: IRDAI compliance check
│   │   │   ├── medical_agent.py       # Agent 4: Medical necessity verification
│   │   │   ├── groq_service.py        # Groq API wrapper (Vision + Chat)
│   │   │   ├── insurance_kb.py        # IRDAI knowledge base
│   │   │   ├── medical_kb.py          # Medical knowledge base
│   │   │   ├── vector_store.py        # ChromaDB vector operations
│   │   │   ├── rag_service.py         # RAG pipeline for chatbot
│   │   │   ├── semantic_chunker.py    # Document chunking for embeddings
│   │   │   ├── appeal_generator.py    # Appeal letter construction
│   │   │   ├── pdf_service.py         # PDF generation (ReportLab)
│   │   │   └── email_service.py       # SMTP email (OTP, reset links)
│   │   └── data/
│   │       └── insurance_kb.json      # Structured IRDAI knowledge data
│   ├── requirements.txt               # Python dependencies
│   └── .env                           # Environment variables
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root layout with ColorModeScript
│   │   │   ├── providers.tsx          # Chakra UI theme provider
│   │   │   ├── page.tsx               # Dashboard (home page)
│   │   │   ├── login/page.tsx         # Login / Signup / OTP / Reset
│   │   │   ├── upload/page.tsx        # Document upload
│   │   │   ├── pipeline/page.tsx      # Claim data extraction + pipeline
│   │   │   ├── analysis/page.tsx      # Analysis results
│   │   │   ├── appeal/page.tsx        # Appeal generation + PDF download
│   │   │   ├── reports/page.tsx       # Claim reports & statistics
│   │   │   ├── knowledge/page.tsx     # Knowledge graph explorer
│   │   │   ├── settings/page.tsx      # User settings + theme toggle
│   │   │   └── help/page.tsx          # Help & support
│   │   ├── components/
│   │   │   ├── Sidebar.tsx            # Navigation sidebar
│   │   │   ├── ChatWidget.tsx         # Floating AI chatbot
│   │   │   ├── StatsCard.tsx          # Dashboard stat cards
│   │   │   └── AuthGuard.tsx          # Route protection
│   │   ├── lib/
│   │   │   └── api.ts                 # Axios API client functions
│   │   └── theme/
│   │       └── index.ts               # Chakra UI theme + semantic tokens
│   ├── package.json
│   └── tsconfig.json
│
└── PROJECT_DOCUMENTATION.md
```

---

## 13. Setup & Installation

### Prerequisites
- **Node.js** ≥ 18.x
- **Python** ≥ 3.10
- **Supabase** account (for cloud PostgreSQL)
- **Groq API** key (for LLM inference)

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
# or
npx next dev --port 3000
```

### Access Points
| Service      | URL                        |
|-------------|----------------------------|
| Frontend    | http://localhost:3000       |
| Backend API | http://localhost:8000       |
| API Docs    | http://localhost:8000/docs  |
| ReDoc       | http://localhost:8000/redoc |

---

## 14. Environment Variables

### Backend (`.env`)
```env
# Groq API (required for LLM/OCR)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx

# Supabase (required for cloud database)
SUPABASE_URL=https://xxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx

# JWT Secret
JWT_SECRET=your-secret-key

# Email Service (for OTP)
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# CORS
CORS_ORIGINS=http://localhost:3000
```

---

## 15. Future Scope

| Enhancement                     | Description                                                     |
| ------------------------------- | --------------------------------------------------------------- |
| 🔄 **Multi-language Support**    | Hindi, Tamil, Telugu, etc. for regional policyholders           |
| 📊 **Knowledge Graph Visualization** | Interactive graph of policy-medical-regulation relationships |
| 🔗 **Direct IRDAI IGMS Integration** | Auto-file complaints to IRDAI Bima Bharosa portal           |
| 📱 **Mobile App**                | React Native / Flutter companion app                            |
| 🏢 **Enterprise Dashboard**      | Bulk claim processing for hospitals and TPAs                    |
| 🤖 **Fine-tuned Models**         | Custom LLMs trained on Indian insurance case law                |
| 📈 **Predictive Analytics**      | ML models to predict appeal success probability                 |
| 🔐 **Aadhaar/DigiLocker**       | Government ID verification for claim authentication             |
| 📋 **Audit Trail**               | Complete logging for regulatory compliance                      |
| 🌐 **Cloud Deployment**          | AWS/GCP production deployment with CI/CD                        |

---

## 🏷️ Summary

**ClaimAssist AI** demonstrates the practical application of **Agentic AI**, **RAG**, and **Knowledge Graphs** in the **InsurTech** domain. By combining multiple specialized LLM agents with structured Indian insurance and medical knowledge bases, it automates the complex process of health insurance claim appeals — empowering policyholders to effectively challenge wrongful denials with legally-grounded, evidence-backed appeal letters.

---

*Built with ❤️ using Next.js, FastAPI, Groq, ChromaDB, and Supabase*
