# 🇵🇰 Pakistan Terror Attacks Intelligence Chatbot

A full-stack AI chatbot system for researching terror attacks in Pakistan.
Built with **FastAPI** (Python backend) + **React** (frontend) + **Grok 4.1 Fast** (AI model).

---

## 📁 Project Structure

```
pakistan-chatbot/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example               # Environment config template
│   ├── models/
│   │   └── schemas.py             # Pydantic data models
│   ├── routers/
│   │   ├── chat.py                # POST /api/chat/ — main chatbot endpoint
│   │   ├── attacks.py             # GET /api/attacks/ — database browser
│   │   ├── search.py              # POST /api/search/ — semantic search
│   │   └── health.py              # GET /api/health — status check
│   ├── services/
│   │   ├── rag_service.py         # RAG retrieval engine (vector similarity)
│   │   ├── grok_service.py        # Grok 4.1 API client + fallback
│   │   └── session_service.py     # In-memory session/history manager
│   └── data/
│       └── attacks_db.py          # 20 curated Pakistan attack records
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx                # Root component with routing
        ├── main.jsx               # React entry point
        ├── styles/
        │   └── globals.css        # Full dark editorial design system
        ├── components/
        │   └── Sidebar.jsx        # Navigation sidebar
        └── pages/
            ├── ChatPage.jsx       # AI chat interface
            ├── DatabasePage.jsx   # Filterable attack table
            └── StatsPage.jsx      # Statistics & bar charts
```

---

## 🚀 Setup & Running

### 1. Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROK_API_KEY

# Run the server
uvicorn main:app --reload --port 8000
```

Backend will be live at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

### 2. Frontend (React + Vite)

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend will be live at: **http://localhost:3000**

---

## 🔑 Getting Your Grok API Key

1. Go to **https://console.x.ai**
2. Create an account / sign in
3. Navigate to API Keys
4. Generate a new key
5. Paste it in `backend/.env` as `GROK_API_KEY=xai-...`

> **Demo Mode**: The app works without a Grok API key — it returns structured database results directly. Add the key for natural language AI responses.

---

## 🧠 Architecture Blocks Explained

### Block 1: Input Layer (FastAPI Router)
- `routers/chat.py` receives the user's message via POST
- Validates input length, checks for empty messages
- Assigns or retrieves a session ID

### Block 2: Intent Detection
- `services/grok_service.py → detect_intent()`
- Lightweight keyword-based classifier (no API call)
- Categories: temporal, location, perpetrator, ranking, statistics, general

### Block 3: RAG Retrieval Engine
- `services/rag_service.py`
- Tokenizes query and scores all 20 attack records
- Supports filters: province, year, perpetrator group
- Returns top-K most relevant records with scores

### Block 4: Context Builder
- `rag_service.build_context()` formats retrieved docs into a structured prompt
- Injected into the Grok system prompt before every API call

### Block 5: Grok 4.1 Fast Reasoning
- `services/grok_service.py → chat()`
- Calls `api.x.ai/v1/chat/completions` with model `grok-4-1-fast`
- Reasoning mode toggled based on intent
- Low temperature (0.1) for factual accuracy

### Block 6: Session Memory
- `services/session_service.py`
- In-memory store with TTL (2 hours)
- Keeps last 20 messages per session
- For production: replace with Redis (`aioredis`)

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + API key status |
| POST | `/api/chat/` | Main chatbot endpoint |
| GET | `/api/chat/session/{id}/history` | Get conversation history |
| DELETE | `/api/chat/session/{id}` | Clear session |
| GET | `/api/attacks/` | List attacks (with filters) |
| GET | `/api/attacks/stats` | Aggregate statistics |
| GET | `/api/attacks/deadliest` | Top N deadliest attacks |
| GET | `/api/attacks/{id}` | Single attack by ID |
| POST | `/api/search/` | Semantic search over KB |

---

## 🔧 Extending the Knowledge Base

To add more attack records, edit `backend/data/attacks_db.py`:

```python
{
    "id": "pk021",
    "date": "YYYY-MM-DD",
    "location": "City, Area",
    "province": "Province Name",
    "attack_type": "Type of attack",
    "target": "Who was targeted",
    "perpetrator": "Group name",
    "deaths": 0,
    "injuries": 0,
    "description": "Detailed description...",
    "source": "Dawn / Geo / SATP"
}
```

---

## 🚀 Production Deployment

### Backend (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend (Build)
```bash
cd frontend
npm run build
# Deploy dist/ folder to Vercel, Netlify, or serve via nginx
```

### Session Storage (Production)
Replace `session_service.py` memory store with Redis:
```python
import aioredis
redis = await aioredis.create_redis_pool("redis://localhost")
```

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | FastAPI (Python) |
| AI Model | Grok 4.1 Fast (xAI) |
| RAG Engine | Custom TF-IDF scoring (upgradeable to sentence-transformers) |
| Session Memory | In-memory (upgradeable to Redis) |
| Frontend | React 18 + Vite |
| Styling | Pure CSS (no UI framework) |
| Font | Playfair Display + JetBrains Mono + Barlow |
