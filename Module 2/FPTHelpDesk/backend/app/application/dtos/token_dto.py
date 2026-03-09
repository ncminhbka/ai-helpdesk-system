from pydantic import BaseModel


class Token(BaseModel):
    """Schema chứa thông tin Access Token trả về sau khi đăng nhập thành công."""
    access_token: str        # Chuỗi token dùng để xác thực các yêu cầu sau này
    token_type: str = "bearer" # Loại token (mặc định là bearer)
