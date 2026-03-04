# 🏢 FPT HelpDesk — Multi-Agent AI Assistant

Hệ thống chatbot hỗ trợ nội bộ FPT sử dụng **LangGraph** multi-agent architecture + **FastAPI** + **React (Vite)**.

## ✨ Tính năng

- 📋 **Ticket Management** — Tạo, tra cứu, cập nhật ticket hỗ trợ
- 📅 **Room Booking** — Đặt, tra cứu, cập nhật, hủy phòng họp
- 📖 **FAQ / Chính sách** — Tra cứu chính sách từ tài liệu (RAG)
- 🔧 **IT Support** — Hỗ trợ kỹ thuật (web search)
- ⚠️ **HITL Confirmation** — Xác nhận / sửa / hủy trước khi thực hiện thao tác nhạy cảm

## 📁 Cấu trúc dự án

```
FPTHelpDesk/
├── backend/
│   ├── app/
│   │   ├── agents/       # LangGraph agents + graph
│   │   ├── api/          # FastAPI endpoints
│   │   ├── core/         # Config, database
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic (chat_service)
│   │   ├── tools/        # LangChain tools (booking, ticket)
│   │   ├── utils/        # Helpers, state, RAG
│   │   └── main.py       # Entry point
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── contexts/     # AuthContext
│   │   └── App.jsx
│   └── package.json
└── docs/                 # Tài liệu chính sách (cho RAG)
```

---

## 🚀 Hướng dẫn chạy dự án

### Yêu cầu

- **Python** 3.10+
- **Node.js** 18+
- **Conda** (khuyến nghị) hoặc **venv**

### 1. Clone & tạo môi trường

```bash
# Tạo conda environment
conda create -n intern_env python=3.11 -y
conda activate intern_env
```

### 2. Cài đặt Backend

```bash
cd backend

# Cài dependencies
pip install -r requirements.txt
```

### 3. Cấu hình file `.env`

Tạo file `backend/.env` (hoặc sửa file có sẵn):

```env
# OpenAI (bắt buộc)
OPENAI_API_KEY=sk-proj-...

# Tavily - IT Support search (bắt buộc)
TAVILY_API_KEY=tvly-...

# Database
DATABASE_URL=sqlite+aiosqlite:///./fpt_helpdesk.db

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# RAG - đường dẫn tới thư mục docs
DOCS_DIR=../docs
CHROMA_PERSIST_DIR=./chroma_db

# HITL - bật/tắt xác nhận trước thao tác nhạy cảm
ENABLE_HITL=true

# LangSmith (tùy chọn - monitoring)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=FPTHelpDesk
```

### 4. Chạy Backend

```bash
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend sẽ chạy tại: **http://localhost:8000**

- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 5. Cài đặt & chạy Frontend

```bash
cd frontend

# Cài dependencies (lần đầu)
npm install

# Chạy dev server
npm run dev
```

Frontend sẽ chạy tại: **http://localhost:5173**

---

## 🔧 Cấu hình quan trọng

| Biến | Mô tả | Mặc định |
|------|--------|----------|
| `OPENAI_API_KEY` | API key OpenAI (bắt buộc) | — |
| `TAVILY_API_KEY` | API key Tavily cho IT Support | — |
| `ENABLE_HITL` | Bật HITL confirmation cho thao tác nhạy cảm | `true` |
| `DATABASE_URL` | Connection string database | SQLite local |
| `SECRET_KEY` | JWT secret key | cần đổi khi production |

---

## 🧪 Kiểm tra nhanh

1. Mở **http://localhost:5173** trên trình duyệt
2. Đăng ký tài khoản mới hoặc đăng nhập
3. Tạo session mới → nhắn thử:
   - `"Đặt phòng CR7 lúc 10:00 ngày mai"` → test HITL confirm
   - `"Tra cứu booking"` → test safe tool (không cần confirm)
   - `"Tạo ticket lỗi mạng"` → test ticket HITL
   - `"Chính sách nghỉ phép"` → test FAQ / RAG

---

## 📌 Ghi chú

- Database SQLite sẽ tự tạo file `fpt_helpdesk.db` khi chạy lần đầu
- ChromaDB (vector store) sẽ cache tại `chroma_db/` sau lần ingest đầu tiên
- Khi `ENABLE_HITL=true`, các thao tác tạo/sửa/xóa sẽ yêu cầu xác nhận trước khi thực hiện
- Đổi `ENABLE_HITL=false` để tắt xác nhận (tools chạy trực tiếp)
