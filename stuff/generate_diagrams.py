import base64
import json
import urllib.request

def generate_mermaid_url(graph_string):
    state = {
        "code": graph_string,
        "mermaid": {"theme": "default"}
    }
    json_str = json.dumps(state)
    b64_str = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
    return f"https://mermaid.ink/img/{b64_str}?type=png"

def download_diagram(graph_string, filename):
    url = generate_mermaid_url(graph_string)
    print(f"Downloading {filename}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Saved {filename}")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")

# Biểu đồ 1: Hệ thống riêng (System Backend Architecture)
graph1 = """graph TD
    classDef frontend fill:#3498db,stroke:#2980b9,stroke-width:2px,color:white,font-weight:bold
    classDef backend fill:#2c3e50,stroke:#2c3e50,stroke-width:2px,color:white,font-weight:bold
    classDef database fill:#f39c12,stroke:#f39c12,stroke-width:2px,color:white,font-weight:bold

    Client["Client (Browser / React JS)"]:::frontend

    subgraph "Backend Architecture (FastAPI)"
        API["API Layer (Routers / Endpoints)"]:::backend
        Service["Service Layer (Business Logic)"]:::backend
        Repo["Repository Layer (Data Access)"]:::backend
    end

    subgraph "Storage Layer (PostgreSQL)"
        DB[(Relational DB)]:::database
        VectorDB[(Vector DB / pgvector)]:::database
    end

    Client <-->|HTTP REST / JSON| API
    API <-->|Request/Response| Service
    Service <-->|CRUD Objects| Repo
    Repo <-->|SQL Queries| DB
    Repo <-->|Semantic Search| VectorDB
"""
download_diagram(graph1, "KienTrucHeThong.png")

# Biểu đồ 2: Luồng Multi-Agent riêng (AI Agent Workflow)
graph2 = """graph TD
    classDef entrypoint fill:#2ecc71,stroke:#27ae60,stroke-width:2px,color:white
    classDef router fill:#34495e,stroke:#2c3e50,stroke-width:2px,color:white
    classDef agent fill:#16a085,stroke:#1abc9c,stroke-width:2px,color:white
    classDef tools fill:#e74c3c,stroke:#c0392b,stroke-width:2px,color:white
    classDef hitl fill:#f1c40f,stroke:#f39c12,stroke-width:2px,color:black,font-weight:bold
    classDef llm fill:#8e44ad,stroke:#8e44ad,stroke-width:2px,color:white,font-weight:bold
    
    Start((Khách hàng chat)):::entrypoint --> primary_assistant["Supervisor Router (Xác định ý định)"]:::router
    
    subgraph Multi-Agent LangGraph System
        primary_assistant -->|Booking Intent| BookingAgent:::agent
        primary_assistant -->|Ticket Intent| TicketAgent:::agent
        primary_assistant -->|FAQ Intent| FAQAgent:::agent
        primary_assistant -->|IT Support Intent| ITSupportAgent:::agent
        
        BookingAgent --> ToolB[Booking Tools]:::tools
        TicketAgent --> ToolT[Ticket Tools]:::tools
        
        FAQAgent --> RAG[Search RAG Policy/Docs]:::tools
        ITSupportAgent --> RAG
    end

    LLM["External LLM (OpenAI)"]:::llm
    primary_assistant -.->|Reasoning| LLM
    BookingAgent -.->|Reasoning| LLM
    TicketAgent -.->|Reasoning| LLM

    HITL[Human-in-the-Loop Xác nhận]:::hitl
    ToolB -.->|Confirm before DB Write| HITL
    ToolT -.->|Confirm before DB Write| HITL

    BookingAgent --> leave_skill[Hoàn thành]:::entrypoint
    TicketAgent --> leave_skill
    FAQAgent --> leave_skill
    ITSupportAgent --> leave_skill

    leave_skill --> primary_assistant
    primary_assistant --> End((Trả lời Khách hàng)):::entrypoint
"""
download_diagram(graph2, "KienTrucAgents_LangGraph.png")

# Biểu đồ 3: Mô Hình Dữ Liệu riêng (Entity Relationship)
graph3 = """erDiagram
    users {
        int id PK
        string email UK
        string password_hash
        string name
        datetime_tz created_at
    }

    chat_sessions {
        string session_id PK "UUID"
        int user_id FK
        string title
        datetime_tz created_at
        datetime_tz updated_at
    }

    messages {
        int id PK
        string session_id FK
        string role "user | assistant"
        text content
        string message_type "message | confirm | error"
        text metadata_json
        datetime_tz created_at
    }

    bookings {
        int booking_id PK
        int user_id FK
        string room_name
        string customer_name
        string customer_phone
        string email
        string reason
        datetime_tz time
        text note
        string status "Scheduled | Canceled | Finished"
    }

    tickets {
        int ticket_id PK
        int user_id FK
        string content
        text description
        string customer_name
        string customer_phone
        string email
        datetime_tz time
        string status "Pending | Resolving | Finished | Canceled"
    }

    users ||--o{ chat_sessions : "tạo (owns)"
    users ||--o{ bookings : "đặt phòng (makes)"
    users ||--o{ tickets : "gửi yêu cầu (raises)"
    chat_sessions ||--o{ messages : "chứa (contains)"
"""
download_diagram(graph3, "KienTrucDatabase_ERD.png")
