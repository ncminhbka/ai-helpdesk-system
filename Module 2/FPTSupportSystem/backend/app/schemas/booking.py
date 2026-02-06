
from typing import Optional
from pydantic import BaseModel

class BookingResponse(BaseModel):
    booking_id: int
    customer_name: Optional[str]
    customer_phone: Optional[str]
    email: Optional[str]
    reason: str
    time: Optional[str]
    note: Optional[str]
    status: str

    class Config:
        from_attributes = True
