from typing import Optional
from pydantic import BaseModel, Field


class TicketResponse(BaseModel):
    ticket_id: int
    content: str
    description: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    email: Optional[str]
    time: Optional[str]
    status: str

    class Config:
        from_attributes = True


class TicketData(BaseModel):
    """Schema for create_ticket tool arguments."""
    content: str = Field(description="Brief description of the issue")
    description: str = Field(description="Detailed description of the issue")
    customer_name: Optional[str] = Field(default=None, description="Customer's name")
    customer_phone: Optional[str] = Field(default=None, description="Customer's phone number")
    email: Optional[str] = Field(default=None, description="Customer's email address")


class TicketUpdateData(BaseModel):
    """Schema for update_ticket tool arguments."""
    ticket_id: int = Field(description="ID of the ticket to update")
    content: Optional[str] = Field(default=None, description="Updated content")
    description: Optional[str] = Field(default=None, description="Updated description")
    customer_name: Optional[str] = Field(default=None, description="Updated customer name")
    customer_phone: Optional[str] = Field(default=None, description="Updated phone number")
    email: Optional[str] = Field(default=None, description="Updated email")
