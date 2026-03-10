# Presentation là tầng ngoài cùng (4) của ứng dụng, nơi giao tiếp trực tiếp với người dùng.
# nhiệm vụ duy nhất là nhận http request, chuyển thành dto, chuyển vào application service, nhận kết quả trả về từ application service, chuyển thành http response và trả về cho người dùng.
'''
1. Tầng Presentation thường chứa code gì?
Nhiệm vụ duy nhất của nó là "Phiên dịch": Dịch yêu cầu từ người dùng (HTTP) sang ngôn ngữ của ứng dụng (DTO/Use Case) và dịch kết quả từ ứng dụng về lại định dạng mà người dùng hiểu (JSON/HTML).

Routers & Endpoints: Định nghĩa các đường dẫn API (Ví dụ: @router.post("/tickets")).

Dependency Injection (DI): File dependencies.py – nơi "lắp ráp" toàn bộ các bộ phận (Repo, Use Case, Service) lại với nhau.

Exception Handlers: Nơi biến các lỗi nghiệp vụ (như UserNotFoundError) thành mã HTTP chuẩn (như 404 Not Found).

Middlewares: Xử lý các vấn đề xuyên suốt như Logging request, CORS, tối ưu hóa dữ liệu.

Authentication Schemas: Định nghĩa cách lấy Token từ Header (OAuth2, Bearer Token).

2. Tầng Presentation được phép Import từ đâu?
Theo quy tắc phụ thuộc, tầng này chỉ được phép nhìn vào bên trong:

3. Các thư viện thường xuất hiện ở tầng này
Đây là nơi tập hợp các thư viện liên quan đến Giao thức truyền tải (Transport):

FastAPI: Framework chính để điều hướng request.

Pydantic: Dùng để định nghĩa các Schema đầu vào/đầu ra (mặc dù DTO cũng dùng Pydantic, nhưng ở Presentation nó phục vụ việc tạo tài liệu Swagger UI).

Slowapi: Nếu bạn muốn giới hạn số lần gọi API (Rate limiting).

Fastapi-pagination: Nếu bạn cần phân trang cho danh sách dữ liệu.

Multipart/Form-data: Các thư viện hỗ trợ upload file.
'''