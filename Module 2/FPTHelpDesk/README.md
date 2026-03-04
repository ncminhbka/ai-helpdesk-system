# 🏢 FPT HelpDesk — Multi-Agent AI Assistant

Hệ thống chatbot hỗ trợ nội bộ FPT sử dụng **LangGraph** multi-agent architecture + **FastAPI** + **React (Vite)** + **PostgreSQL + pgvector**.

## ✨ Tính năng

- 📋 **Ticket Management** — Tạo, tra cứu, cập nhật ticket hỗ trợ
- 📅 **Room Booking** — Đặt, tra cứu, cập nhật, hủy phòng họp
- 📖 **FAQ / Chính sách** — Tra cứu chính sách từ tài liệu (RAG với pgvector)
- 🔧 **IT Support** — Hỗ trợ kỹ thuật (web search)
- ⚠️ **HITL Confirmation** — Xác nhận / sửa / hủy trước khi thực hiện thao tác nhạy cảm

## 📁 Cấu trúc dự án

```
FPTHelpDesk/
├── docker-compose.yml        ← Chạy toàn bộ stack bằng 1 lệnh
├── docker/
│   └── init.sql              ← Tự động bật pgvector extension
├── docs/                     ← Tài liệu chính sách PDF (cho RAG)
├── backend/
│   ├── app/
│   │   ├── agents/           ← LangGraph agents (domain-driven)
│   │   │   ├── shared/       ← base.py, graph.py
│   │   │   ├── primary/      ← Primary assistant
│   │   │   ├── booking/      ← Booking agent + tools + prompt
│   │   │   ├── ticket/       ← Ticket agent + tools + prompt
│   │   │   ├── faq/          ← FAQ agent + RAG tools + prompt
│   │   │   └── it_support/   ← IT Support agent + search tools
│   │   ├── api/              ← FastAPI endpoints
│   │   ├── core/             ← Config, database
│   │   ├── models/           ← SQLAlchemy models
│   │   ├── services/         ← Business logic
│   │   └── main.py
│   ├── ingest.py             ← Script nhập tài liệu vào pgvector
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env                  ← Cấu hình (KHÔNG commit lên git)
└── frontend/
    ├── src/
    ├── nginx.conf            ← Proxy /api/ → backend
    ├── Dockerfile
    └── package.json
```

---

## 🚀 Hướng dẫn chạy dự án

### Yêu cầu

- **Docker Desktop** (đã cài và đang chạy)
- **Python 3.11+** + **Conda** (chỉ cần để chạy `ingest.py` lần đầu)

---

### Bước 1: Cấu hình file `.env`

Mở file `backend/.env` và điền thông tin của bạn:

```env
# OpenAI (bắt buộc)
OPENAI_API_KEY=sk-proj-...

# Tavily - IT Support search (bắt buộc)
TAVILY_API_KEY=tvly-...

# Database PostgreSQL
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fpt_helpdesk

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# RAG
DOCS_DIR=../docs

# HITL - xác nhận trước thao tác nhạy cảm (true/false)
ENABLE_HITL=true

# LangSmith (tùy chọn - monitoring)
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=lsv2_pt_...
# LANGCHAIN_PROJECT=FPTHelpDesk
```

---

### Bước 2: Khởi động toàn bộ stack

```bash
# Chạy tại thư mục gốc FPTHelpDesk/
docker compose up -d --build
```

Lệnh này sẽ tự động:
1. 🐘 Khởi động **PostgreSQL + pgvector** (port 5432)
2. ⚙️ Build và khởi động **FastAPI backend** (port 8000)
3. 🌐 Build và khởi động **React frontend qua nginx** (port 80)

---

### Bước 3: Nhập tài liệu vào pgvector (chỉ cần làm 1 lần)

> Đảm bảo stack đã chạy và `DB_HOST=localhost` trong `.env`

```bash
cd backend
conda activate intern_env
python ingest.py
```

Sau lần đầu, tài liệu được lưu trong PostgreSQL — không cần chạy lại trừ khi tài liệu thay đổi.

---

### Bước 4: Truy cập ứng dụng

| Service | URL |
|---------|-----|
| 🌐 Frontend | http://localhost |
| ⚙️ Backend API | http://localhost:8000 |
| 📋 Swagger Docs | http://localhost:8000/docs |
| ❤️ Health check | http://localhost:8000/health |

---

## 🛑 Hướng dẫn tắt

```bash
# Tắt tất cả service (giữ nguyên data)
docker compose down

# Tắt và XÓA toàn bộ data (reset hoàn toàn)
docker compose down -v
```

---

## 🔧 Các lệnh thường dùng

```bash
# Xem trạng thái các container
docker compose ps

# Xem log realtime
docker compose logs -f              # Tất cả service
docker compose logs -f backend      # Chỉ backend
docker compose logs -f db           # Chỉ database

# Restart một service
docker compose restart backend

# Vào shell PostgreSQL
docker exec -it fpt_helpdesk_db psql -U postgres -d fpt_helpdesk

# Re-ingest khi tài liệu thay đổi
cd backend && python ingest.py --force
```

---

## 🧪 Kiểm tra nhanh

1. Mở **http://localhost** trên trình duyệt
2. Đăng ký tài khoản mới hoặc đăng nhập
3. Tạo session mới → nhắn thử:
   - `"Đặt phòng CR7 lúc 10:00 ngày mai"` → test Booking + HITL confirm
   - `"Tra cứu booking của tôi"` → test safe tool
   - `"Tạo ticket lỗi mạng"` → test Ticket + HITL
   - `"Chính sách nghỉ phép"` → test FAQ / RAG

---

## 📌 Ghi chú

- **HITL**: Khi `ENABLE_HITL=true`, các thao tác tạo/sửa/xóa sẽ yêu cầu xác nhận. Đặt `ENABLE_HITL=false` để tắt.
- **Agent State**: Context hội thoại được lưu trong PostgreSQL — reload trang vẫn giữ context.
- **pgvector**: Embeddings của tài liệu chính sách được lưu trong bảng `langchain_pg_embedding`.
