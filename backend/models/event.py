"""Event models."""
from typing import Optional
from pydantic import BaseModel


class EventBase(BaseModel):
    """Basic event information."""
    id: int
    name: str
    date: Optional[str] = None
    location: Optional[str] = None
    promotion: Optional[str] = None


class EventDetail(EventBase):
    """Detailed event information with fights."""
    pass  # Will be expanded with fights list


class EventListResponse(BaseModel):
    """Response for event list endpoint."""
    events: list[EventBase]
    total: int
