"""Ranking models."""
from typing import Optional
from pydantic import BaseModel


class RankingEntry(BaseModel):
    """A single ranking entry."""
    rank: int
    fighter_id: Optional[int] = None
    fighter_name: str
    division: str
    is_champion: bool = False
    is_interim: bool = False


class RankingsResponse(BaseModel):
    """Response for rankings endpoint."""
    divisions: dict[str, list[RankingEntry]]
    last_updated: Optional[str] = None
