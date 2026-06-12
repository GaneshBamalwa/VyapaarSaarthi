# Vyapaar Saarthi 🚀
### AI-Native Operating System for Indian MSMEs

> Powered by **Gemini 2.5 Flash/Pro · Vertex AI · LangGraph · FastAPI · React**

---

## 🎯 What This Is

Vyapaar Saarthi is a **modular AI agent platform** — not a chatbot. Each agent is independently callable and participates in LangGraph-orchestrated workflows.

**Agents:**
| Agent | Purpose | Model |
|-------|---------|-------|
| 🧾 Intake Agent | Parse Hindi/English orders → Structured JSON | Gemini 2.5 Flash |
| 🔍 Clarification Agent | Detect ambiguous orders | Gemini 2.5 Flash |
| 👁️ OCR Agent | Image/PDF → Text (WhatsApp, receipts) | Gemini 2.5 Pro Vision |
| 🎤 Speech Agent | Voice notes → Transcript | Vertex AI Speech |
| 💰 Collections Agent | Overdue invoice → Hindi reminder + risk | Gemini 2.5 Flash |

---

## 🏗️ Architecture

```
backend/
  app/
    agents/       ← Intake, Clarification, OCR, Speech, Collections
    graph/        ← LangGraph main pipeline with HITL
    services/     ← Business logic layer
    repositories/ ← Data access layer
    routers/      ← Thin API routes
    models/       ← SQLAlchemy models
    schemas/      ← Pydantic schemas
    websocket/    ← Connection manager
    core/         ← Config, logging, Gemini client
    database/     ← SQLAlchemy session

frontend/
  src/
    pages/        ← One page per agent + dashboard
    components/   ← KPICard, AgentStatusCard, FeedItem, HITLCard
    hooks/        ← useWebSocket
    stores/       ← Zustand agent state store
    services/     ← API client layer
    layouts/      ← AppLayout with sidebar
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Gemini API Key (or GCP project with Vertex AI)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set GEMINI_API_KEY or GCP_PROJECT_ID

# Start server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

Open **http://localhost:5174**

---

## 🔑 Environment Variables

```env
# For local dev with Gemini API key (simplest)
GEMINI_API_KEY=your-key-here

# For production with Vertex AI
GCP_PROJECT_ID=your-project
GCP_LOCATION=us-central1
```

---

## 🐳 Docker

```bash
# Copy env file
cp backend/.env.example backend/.env
# Edit backend/.env with your API key

# Start everything
docker-compose up --build
```

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/intake` | Parse order text |
| `GET` | `/api/orders` | List all orders |
| `POST` | `/api/ocr/extract` | OCR from file upload |
| `POST` | `/api/speech/transcribe` | Audio → transcript |
| `POST` | `/api/collections/analyze` | Invoice risk + reminder |
| `GET` | `/api/hitl/pending` | Get HITL queue |
| `POST` | `/api/hitl/{id}/resolve` | Approve/reject |
| `POST` | `/api/simulator/generate-order` | Demo data |
| `WS` | `/ws` | Live agent events |

---

## 🏆 Hackathon Demo Flow

1. Open **Simulator** page → click "Generate Sample Order"
2. Watch **Agent Feed** for real-time streaming events
3. Click "Generate Ambiguous Order" → go to **Approvals** to review HITL
4. Test each **agent page** individually with your own inputs
5. Check **Dashboard** for live KPIs and agent status

---

## 🔌 Adding New Agents

1. Create `agents/new_agent/` with `agent.py`, `prompt.py`, `schemas.py`
2. Extend `BaseAgent` and implement `invoke()`
3. Add router in `routers/new_agent.py`
4. Register in `app/main.py`
5. Add LangGraph node in `graph/nodes.py`
6. Add page in `frontend/src/pages/NewAgentPage.tsx`

The architecture ensures zero structural changes needed.

---

## 🌐 GCP Deployment (Cloud Run)

```bash
# Build and push backend
docker build -t gcr.io/PROJECT_ID/vyapaar-backend ./backend
docker push gcr.io/PROJECT_ID/vyapaar-backend

# Deploy
gcloud run deploy vyapaar-backend \
  --image gcr.io/PROJECT_ID/vyapaar-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```
