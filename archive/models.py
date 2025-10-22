from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Fighter(BaseModel):
    name: str
    rank: Optional[int] = None
    is_champion: bool = False
    division: Optional[str] = None

class Division(BaseModel):
    name: str
    champion: Optional[Fighter] = None
    interim_champion: Optional[Fighter] = None
    ranked_fighters: List[Fighter] = []

class Linescore(BaseModel):
    event_id_fight_id_fighter_id: str
    event_id: str
    fight_id: str
    fighter_id: str
    score_value: Optional[int] = None
    judge_1_score: Optional[int] = None
    judge_2_score: Optional[int] = None
    judge_3_score: Optional[int] = None


class RankingsResponse(BaseModel):
    mens_p4p: List[Fighter]
    womens_p4p: List[Fighter]
    mens_divisions: List[Division]
    womens_divisions: List[Division]
    last_updated: datetime
    ranking_rules: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "mens_p4p": [
                    {"name": "Islam Makhachev", "rank": 1, "is_champion": True, "division": "Lightweight"},
                    {"name": "Jon Jones", "rank": 2, "is_champion": True, "division": "Heavyweight"}
                ],
                "womens_p4p": [
                    {"name": "Valentina Shevchenko", "rank": 1, "is_champion": True, "division": "Flyweight"},
                    {"name": "Zhang Weili", "rank": 2, "is_champion": True, "division": "Strawweight"}
                ],
                "mens_divisions": [
                    {
                        "name": "Heavyweight",
                        "champion": {"name": "Jon Jones", "is_champion": True},
                        "interim_champion": {"name": "Tom Aspinall", "is_champion": True},
                        "ranked_fighters": []
                    }
                ],
                "womens_divisions": [
                    {
                        "name": "Strawweight",
                        "champion": {"name": "Zhang Weili", "is_champion": True},
                        "ranked_fighters": []
                    }
                ],
                "last_updated": "2024-06-03T00:00:00",
                "ranking_rules": [
                    "Voted on by a panel of media members, only active fighters are eligible",
                    "Champions/interim champions are top of their divisions, but can be ranked in pound-for-pound"
                ]
            }
        } 