"""Rankings API endpoints."""
from fastapi import APIRouter

from ..database.connection import execute_query
from ..models.ranking import RankingsResponse, RankingEntry

router = APIRouter()


@router.get("/", response_model=RankingsResponse)
async def get_rankings():
    """
    Get current UFC rankings by division.
    """
    query = """
        SELECT
            r.rank,
            a.id as fighter_id,
            r.fighter_name,
            r.division,
            r.is_champion
        FROM ufc_rankings r
        LEFT JOIN athletes a ON r.fighter_name = a.full_name
        WHERE r.ranking_type IN ('Division', 'P4P')
        ORDER BY
            CASE r.division
                WHEN 'Men''s Pound-for-Pound' THEN 1
                WHEN 'Women''s Pound-for-Pound' THEN 2
                WHEN 'Heavyweight' THEN 3
                WHEN 'Light Heavyweight' THEN 4
                WHEN 'Middleweight' THEN 5
                WHEN 'Welterweight' THEN 6
                WHEN 'Lightweight' THEN 7
                WHEN 'Featherweight' THEN 8
                WHEN 'Bantamweight' THEN 9
                WHEN 'Flyweight' THEN 10
                WHEN 'Women''s Bantamweight' THEN 11
                WHEN 'Women''s Flyweight' THEN 12
                WHEN 'Women''s Strawweight' THEN 13
                ELSE 99
            END,
            r.rank
    """

    results = execute_query(query)

    # Group by division
    divisions = {}
    for row in results:
        division = row["division"]
        if division not in divisions:
            divisions[division] = []

        divisions[division].append({
            "rank": row["rank"],
            "fighter_id": row["fighter_id"],
            "fighter_name": row["fighter_name"],
            "division": division,
            "is_champion": bool(row["is_champion"]),
            "is_interim": False  # Not tracked in current schema
        })

    # Get last update date
    date_query = """
        SELECT MAX(last_updated) as last_updated
        FROM ufc_rankings
        WHERE ranking_type IN ('Division', 'P4P')
    """
    date_result = execute_query(date_query)
    last_updated = date_result[0]["last_updated"] if date_result else None

    return {
        "divisions": divisions,
        "last_updated": last_updated
    }


@router.get("/division/{division_name}")
async def get_division_rankings(division_name: str):
    """
    Get rankings for a specific division.
    """
    query = """
        SELECT
            r.rank,
            a.id as fighter_id,
            r.fighter_name,
            r.division,
            r.is_champion
        FROM ufc_rankings r
        LEFT JOIN athletes a ON r.fighter_name = a.full_name
        WHERE r.ranking_type IN ('Division', 'P4P')
            AND LOWER(REPLACE(r.division, ' ', '-')) = LOWER(?)
        ORDER BY r.rank
    """

    results = execute_query(query, (division_name.replace('-', ' '),))

    return {
        "division": division_name,
        "rankings": [
            {
                "rank": r["rank"],
                "fighter_id": r["fighter_id"],
                "fighter_name": r["fighter_name"],
                "division": r["division"],
                "is_champion": bool(r["is_champion"]),
                "is_interim": False
            }
            for r in results
        ]
    }
