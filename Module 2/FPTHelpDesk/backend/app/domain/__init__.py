# Domain là tầng trong cùng (1), chứa nghiệp vụ thuần business logic của ứng dụng.
# Nó không phụ thuộc vào bất kỳ framework, thư viện hay công nghệ nào khác, giúp cho việc bảo trì và mở rộng ứng dụng trở nên dễ dàng hơn.
# Vì thế không import bất cứ thư viện bên ngoài nào (không Pydantic, không SQLAlchemy, không FastAPI). 