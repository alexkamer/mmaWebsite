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
    headshot_url: Optional[str] = None
    flag_url: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    reach: Optional[float] = None
    stance: Optional[str] = None
    fight_count: int = 0


class RankingsResponse(BaseModel):
    """Response for rankings endpoint."""
    divisions: dict[str, list[RankingEntry]]
    last_updated: Optional[str] = None
