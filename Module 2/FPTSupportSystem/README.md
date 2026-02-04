# FPT Customer Support Chatbot

AI-powered customer support system with multi-agent architecture using LangGraph, FastAPI, and React.

## Features

- 🤖 **Multi-Agent System**: Hierarchical architecture with specialized agents
  - Primary Assistant: Intent classification and routing
  - FAQ Agent: RAG-based policy questions
  - Ticket Agent: Support ticket management
  - Booking Agent: Meeting room booking
  - IT Support Agent: Technical troubleshooting with web search

- 🔐 **Authentication**: JWT-based auth with secure password hashing
- 💬 **Session Management**: Multiple chat sessions per user
- ✅ **HITL Confirmation**: Human-in-the-loop for critical operations
- 🛡️ **Safety Features**: Prompt injection detection, out-of-scope filtering
- 🌐 **Bilingual**: Vietnamese and English support

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   Auth      │ │   Session   │ │     Chat Interface      ││
│  │   Page      │ │   Sidebar   │ │   + Confirmation Form   ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST
┌───────────────────────────▼─────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   LangGraph Orchestration                ││
│  │  ┌─────────────────────────────────────────────────────┐││
│  │  │               Primary Assistant                      │││
│  │  │         (Intent Classification & Routing)           │││
│  │  └──────┬──────────┬──────────┬──────────┬────────────┘││
│  │         │          │          │          │              ││
│  │    ┌────▼───┐ ┌────▼───┐ ┌────▼───┐ ┌────▼────┐        ││
│  │    │  FAQ   │ │ Ticket │ │Booking │ │   IT    │        ││
│  │    │ Agent  │ │ Agent  │ │ Agent  │ │ Support │        ││
│  │    │ (RAG)  │ │ (HITL) │ │ (HITL) │ │ (Search)│        ││
│  │    └────────┘ └────────┘ └────────┘ └─────────┘        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │   ChromaDB   │ │    SQLite    │ │    Tavily Search     │ │
│  │ (Vector Store│ │  (Database)  │ │   (IT Solutions)     │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API Key
- Tavily API Key (for IT Support)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and add your API keys
cp .env.example .env
# Edit .env with your keys

# Initialize database
python database.py

# Ingest PDF documents (place PDFs in ../docs folder first)
python ingest.py

# Run server
python main.py
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Access

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
FPTSupportSystem/
├── backend/
│   ├── agents/              # LangGraph agents
│   │   ├── primary_assistant.py
│   │   ├── faq_agent.py
│   │   ├── ticket_agent.py
│   │   ├── booking_agent.py
│   │   └── it_support_agent.py
│   ├── tools/               # Agent tools
│   │   ├── ticket_tools.py
│   │   ├── booking_tools.py
│   │   ├── rag_tools.py
│   │   └── search_tools.py
│   ├── utils/               # Utilities
│   │   ├── intent_classifier.py
│   │   └── helpers.py
│   ├── auth.py              # JWT authentication
│   ├── database.py          # SQLAlchemy models
│   ├── graph.py             # LangGraph orchestration
│   ├── ingest.py            # PDF ingestion
│   ├── main.py              # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthPage.jsx
│   │   │   ├── SessionSidebar.jsx
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── ConfirmationForm.jsx
│   │   │   └── DatabaseViewer.jsx
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── docs/                    # PDF documents for RAG
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login
- `GET /auth/me` - Get current user

### Sessions
- `GET /sessions` - List sessions
- `POST /sessions` - Create session
- `GET /sessions/{id}` - Get session with messages
- `DELETE /sessions/{id}` - Delete session

### Chat
- `POST /chat` - Send message
- `POST /confirm/{action_id}` - Confirm HITL action
- `POST /cancel/{action_id}` - Cancel action

### Dashboard
- `GET /tickets` - List user tickets
- `GET /bookings` - List user bookings

## Environment Variables

```
# JWT
JWT_SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OpenAI
OPENAI_API_KEY=sk-...

# Tavily (for IT Support)
TAVILY_API_KEY=tvly-...

# Database
DATABASE_URL=sqlite+aiosqlite:///./fpt_chatbot.db

# RAG
CHROMA_PERSIST_DIR=./chroma_db
DOCS_DIR=../docs
```

## License

MIT License - FPT Corporation
