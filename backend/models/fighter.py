"""Fighter models."""
from typing import Optional
from pydantic import BaseModel


class FighterBase(BaseModel):
    """Basic fighter information."""
    id: int
    name: str
    nickname: Optional[str] = None
    image_url: Optional[str] = None
    weight_class: Optional[str] = None
    nationality: Optional[str] = None
    flag_url: Optional[str] = None
    team: Optional[str] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    draws: Optional[int] = None


class FighterDetail(FighterBase):
    """Detailed fighter information."""
    height: Optional[str] = None
    weight: Optional[str] = None
    reach: Optional[str] = None
    stance: Optional[str] = None
    date_of_birth: Optional[str] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    draws: Optional[int] = None
    no_contests: Optional[int] = None


class FighterListResponse(BaseModel):
    """Response for fighter list endpoint."""
    fighters: list[FighterBase]
    total: int
    page: int
    page_size: int
