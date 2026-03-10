# Infra là tầng (3) từ trong ra, nơi giao tiếp với các hệ thống bên ngoài như cơ sở dữ liệu, API của bên thứ ba, v.v.
'''
1. Tầng Infra chứa những gì khác ngoài Concrete Interfaces?
Ngoài việc hiện thực hóa (implement) các Interface từ tầng Domain, tầng Infrastructure còn chứa các thành phần "xôi thịt" liên quan đến công nghệ cụ thể:

Database Models (ORM Models): Các class định nghĩa bảng dữ liệu (ví dụ: SQLAlchemy Base, SQLModel, Django Models). Chúng khác với Entities ở chỗ chúng bám sát cấu trúc của CSDL.

Database Migrations: Các file cấu hình để thay đổi cấu trúc bảng (như folder alembic trong Python).

External Service Clients (Adapters): Code để gọi đến các bên thứ ba như:

Gửi Mail (SMTP, SendGrid).

Gửi SMS (Twilio).

Thanh toán (Stripe, VNPay).

AI/LLM Engine: (Như LangGraph, OpenAI SDK, LangChain) – đây chính là nơi chứa các Agents xử lý logic AI.

Security Implementations: Các công cụ mã hóa mật khẩu (Bcrypt, Argon2), tạo và xác thực Token (JWT).

System Configuration (Settings): Code để đọc file .env, quản lý biến môi trường (như Pydantic Settings).

Logging & Observability: Cấu hình để ghi log ra file, gửi log lên Sentry, Prometheus hoặc CloudWatch.

Caching: Cài đặt cho Redis, Memcached.

2. Tầng Infra được phép Import cái gì và từ tầng nào?
Quy tắc bất biến của Clean Architecture là: Mũi tên phụ thuộc chỉ trỏ vào trong. Tầng Infrastructure nằm ở vòng ngoài, nên nó có thể nhìn thấy các tầng bên trong nó.

Import từ tầng Domain:

Interfaces: Để kế thừa và thực thi các bản hợp đồng (ví dụ: class SQLUserRepository(IUserRepository)).

Entities: Để map dữ liệu từ DB Model sang Entity trước khi trả về cho tầng Application.

Enums/Exceptions: Các định nghĩa dùng chung toàn hệ thống.

Import từ tầng Application:

Đôi khi Infra cần import các DTO (Data Transfer Objects) nếu nó đóng vai trò là một Adapter cần format dữ liệu theo yêu cầu của tầng ứng dụng.

Tuyệt đối KHÔNG được import từ tầng Presentation: Tầng hạ tầng không được biết gì về các API Endpoints hay các hàm xử lý Request của FastAPI.

3. Những thư viện nào thường nằm ở tầng Infra?
Bất kỳ thư viện nào "nặng mùi" kỹ thuật hoặc phụ thuộc vào bên ngoài đều nên bị "cách ly" vào tầng này. Ví dụ trong dự án Python của bạn:

Cơ sở dữ liệu: sqlalchemy, motor (MongoDB), alembic, redis.

Mạng (Network/HTTP): httpx, requests, aiohttp (dùng để gọi API bên ngoài).

Bảo mật: passlib, python-jose, cryptography.

AI & LLM: langchain, langgraph, openai, anthropic.

Cấu hình & Tiện ích: pydantic-settings, python-dotenv.

Cloud SDKs: boto3 (AWS), google-cloud-storage.
'''