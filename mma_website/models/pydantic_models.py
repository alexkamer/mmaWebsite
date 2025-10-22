from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Fighter(BaseModel):
    name: str
    rank: Optional[int] = None
    is_champion: bool = False
    division: Optional[str] = None

 