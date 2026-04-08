# ClaimAssist AI

An agentic LLM framework for automated health insurance claim appeals using Policy-Medical Evidence Alignment and Insurance Knowledge Graphs.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, Chakra UI, TypeScript |
| Backend | FastAPI, Python 3.11 |
| Database | Supabase (PostgreSQL) |
| AI/LLM | Groq API (LLaMA 3) |
| Vector Search | FAISS + Sentence Transformers |
| PDF Processing | pdfplumber, PyMuPDF |

## Project Structure

```
├── backend/          FastAPI backend
│   ├── app/
│   │   ├── routers/  API routes
│   │   ├── services/ Business logic
│   │   ├── models/   Pydantic schemas
│   │   └── database/ DB + JWT utils
│   ├── requirements.txt
│   └── .env.example
├── frontend/         Next.js frontend
│   ├── src/
│   │   ├── app/      Pages
│   │   ├── components/
│   │   └── lib/
│   └── package.json
└── render.yaml       Render deployment blueprint
```

## Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # fill in your values
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
# Create .env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## Deployment

See [render.yaml](./render.yaml) for Render deployment configuration.
