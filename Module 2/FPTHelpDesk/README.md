# 🏢 FPT HelpDesk — Multi-Agent AI Assistant

Hệ thống chatbot hỗ trợ nội bộ FPT sử dụng **LangGraph** multi-agent architecture + **FastAPI** + **React (Vite)** + **PostgreSQL + pgvector**, được thiết kế theo chuẩn **Clean Architecture**.

## ✨ Tính năng

- 📋 **Ticket Management** — Tạo, tra cứu, cập nhật ticket hỗ trợ
- 📅 **Room Booking** — Đặt, tra cứu, cập nhật, hủy phòng họp
- 📖 **FAQ / Chính sách** — Tra cứu chính sách từ tài liệu (RAG với pgvector)
- 🔧 **IT Support** — Hỗ trợ kỹ thuật (web search)
- ⚠️ **HITL Confirmation** — Xác nhận / sửa / hủy trước khi thực hiện thao tác nhạy cảm

---

## 🏛️ Kiến trúc

Dự án tuân theo **Clean Architecture** với 4 tầng độc lập, phụ thuộc một chiều từ ngoài vào trong:

```
┌─────────────────────────────────────────────┐
│  Presentation Layer  (FastAPI)              │  HTTP endpoints, DI wiring
├─────────────────────────────────────────────┤
│  Application Layer   (Use Cases + DTOs)     │  Business workflows, validation
├─────────────────────────────────────────────┤
│  Infrastructure Layer (Repositories, AI)    │  DB, Security, LangGraph agents
├─────────────────────────────────────────────┤
│  Domain Layer        (Entities, Interfaces) │  Pure Python, zero dependencies
└─────────────────────────────────────────────┘
```

**Nguyên tắc phụ thuộc:**
- `Domain` — không import từ bất kỳ tầng nào
- `Application` — chỉ import từ `Domain`
- `Infrastructure` — import từ `Domain` + `Application`
- `Presentation` — import từ tất cả, nhưng chỉ gọi qua `Application`

---

## 📁 Cấu trúc dự án

```
FPTHelpDesk/
├── docker-compose.yml
├── docker/
│   └── init.sql                         ← Bật pgvector extension
├── docs/                                ← Tài liệu chính sách PDF (RAG)
├── backend/
│   ├── ingest.py                        ← Nhập tài liệu vào pgvector
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env                             ← Cấu hình (KHÔNG commit)
│   └── app/
│       ├── main.py                      ← FastAPI entry point + lifespan
│       ├── domain/                      ← Tầng 1: Pure business logic
│       │   ├── entities/                ← Python dataclasses (User, Ticket, Booking, Chat)
│       │   ├── interfaces/              ← ABC interfaces (IUserRepository, IPasswordHasher, ...)
│       │   └── exceptions.py            ← Domain exceptions (TicketNotFoundError, ...)
│       ├── application/                 ← Tầng 2: Use cases & DTOs
│       │   ├── dtos/                    ← Pydantic DTOs (input/output)
│       │   ├── use_cases/               ← Business logic (AuthUseCase, ChatUseCase, ...)
│       │   └── utils/
│       │       └── helpers.py           ← Utility functions (parse_datetime, ...)
│       ├── infrastructure/              ← Tầng 3: Concrete implementations
│       │   ├── config/settings.py       ← Pydantic Settings
│       │   ├── database/                ← SQLAlchemy engine + models
│       │   ├── repositories/            ← Concrete repos (UserRepository, ...)
│       │   ├── security/
│       │   │   ├── jwt_bcrypt.py        ← JWT + bcrypt functions
│       │   │   └── password_hasher.py   ← BcryptPasswordHasher (implements IPasswordHasher)
│       │   └── ai/                      ← LangGraph multi-agent system
│       │       ├── shared/
│       │       │   ├── state.py         ← AgentState (LangGraph TypedDict)
│       │       │   ├── base.py          ← Assistant class + transfer schemas
│       │       │   └── graph.py         ← StateGraph orchestration
│       │       ├── hitl/
│       │       │   └── decorator.py     ← @hitl_protected decorator
│       │       ├── primary/             ← Primary routing agent
│       │       ├── booking/             ← Booking agent + tools
│       │       ├── ticket/              ← Ticket agent + tools
│       │       ├── faq/                 ← FAQ agent + RAG tools
│       │       ├── it_support/          ← IT Support agent + search tools
│       │       └── graph_runner.py      ← LangGraphRunner (implements IGraphRunner)
│       └── presentation/               ← Tầng 4: HTTP interface
│           ├── dependencies.py          ← FastAPI DI chain (DB → Repo → UseCase)
│           └── api_v1/
│               ├── router.py
│               └── endpoints/           ← auth.py, chat.py, users.py
└── frontend/
    ├── src/
    ├── nginx.conf                       ← Proxy /api/ → backend
    ├── Dockerfile
    └── package.json
```

---

## 🔗 Dependency Injection Chain

```
get_db()
  └─→ get_user_repository()    → IUserRepository
  └─→ get_ticket_repository()  → ITicketRepository
  └─→ get_booking_repository() → IBookingRepository
  └─→ get_chat_repository()    → IChatRepository

get_password_hasher()          → IPasswordHasher

get_auth_use_case(repo, hasher)    → AuthUseCase
get_user_use_case(repo, hasher)    → UserUseCase
get_ticket_use_case(repo)          → TicketUseCase
get_booking_use_case(repo)         → BookingUseCase
get_chat_use_case(repo)            → ChatUseCase
```

---

## 🤖 Multi-Agent Architecture

```
START
  └─→ fetch_user_info
  └─→ route_to_workflow
        ├─→ primary_assistant
        │     ├─→ enter_booking   → booking_agent   ↔ booking_tools   → leave_skill
        │     ├─→ enter_ticket    → ticket_agent    ↔ ticket_tools    → leave_skill
        │     ├─→ enter_faq       → faq_agent       ↔ faq_tools       → leave_skill
        │     └─→ enter_it_support→ it_support_agent↔ it_support_tools→ leave_skill
        └─→ [resume từ dialog_state nếu đang interrupted]
```

**HITL Flow:** Các tool nhạy cảm dùng `@hitl_protected` → gọi `interrupt()` → graph tạm dừng → frontend hiện card xác nhận → user approve/reject/edit → graph resume.

---

## 🚀 Hướng dẫn chạy

### Yêu cầu

- **Docker Desktop** (đang chạy)
- **Python 3.11+** (chỉ để chạy `ingest.py`)

### Bước 1: Cấu hình `.env`

```env
# OpenAI (bắt buộc)
OPENAI_API_KEY=sk-proj-...

# Tavily - IT Support search (bắt buộc)
TAVILY_API_KEY=tvly-...

# Database
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fpt_helpdesk

# Security
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# RAG
DOCS_DIR=../docs

# HITL (true/false)
ENABLE_HITL=true

# LangSmith (tùy chọn)
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=lsv2_pt_...
# LANGCHAIN_PROJECT=FPTHelpDesk
```

### Bước 2: Khởi động stack

```bash
docker compose up -d --build
```

Tự động khởi động: PostgreSQL + pgvector (5432) → FastAPI backend (8000) → React frontend via nginx (80)

### Bước 3: Nhập tài liệu RAG (chỉ làm 1 lần)

```bash
cd backend
python ingest.py
```

### Bước 4: Truy cập

| Service | URL |
|---------|-----|
| 🌐 Frontend | http://localhost |
| ⚙️ Backend API | http://localhost:8000 |
| 📋 Swagger Docs | http://localhost:8000/docs |
| ❤️ Health check | http://localhost:8000/health |

---

## 🛑 Tắt hệ thống

```bash
docker compose down        # Tắt, giữ nguyên data
docker compose down -v     # Tắt và xóa toàn bộ data
```

---

## 🔧 Lệnh thường dùng

```bash
docker compose ps
docker compose logs -f backend
docker compose restart backend
docker exec -it fpt_helpdesk_db psql -U postgres -d fpt_helpdesk
cd backend && python ingest.py --force   # Re-ingest khi tài liệu thay đổi
```

---

## 🧪 Test nhanh

Sau khi đăng nhập tại http://localhost, tạo session mới và thử:

| Message | Agent được kích hoạt |
|---------|----------------------|
| `"Đặt phòng CR7 lúc 10:00 ngày mai"` | Booking + HITL confirm |
| `"Tra cứu booking của tôi"` | Booking (safe read) |
| `"Tạo ticket lỗi mạng"` | Ticket + HITL confirm |
| `"Chính sách nghỉ phép"` | FAQ / RAG |
| `"Máy tính không kết nối được wifi"` | IT Support |

---

## 📌 Ghi chú

- **HITL**: Khi `ENABLE_HITL=true`, các thao tác tạo/sửa/hủy sẽ yêu cầu xác nhận từ người dùng trước khi thực thi.
- **Agent State**: Context hội thoại được lưu trong PostgreSQL — reload trang vẫn giữ nguyên context.
- **pgvector**: Embeddings tài liệu chính sách lưu trong bảng `langchain_pg_embedding`.
