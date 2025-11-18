"""Rankings API endpoints."""
from fastapi import APIRouter

from ..database.connection import execute_query
from ..models.ranking import RankingsResponse, RankingEntry

router = APIRouter()


@router.get("/", response_model=RankingsResponse)
async def get_rankings():
    """
    Get current UFC rankings by division with fighter details.
    """
    query = """
        WITH ranked_fighters AS (
            SELECT
                r.rank,
                r.fighter_name,
                r.division,
                r.is_champion,
                r.is_interim_champion,
                a.id as fighter_id,
                a.headshot_url,
                a.flag_url,
                a.weight,
                a.height,
                a.reach,
                a.stance,
                ROW_NUMBER() OVER (
                    PARTITION BY r.division, r.fighter_name
                    ORDER BY
                        CASE WHEN a.headshot_url IS NOT NULL AND a.headshot_url != '' THEN 2 ELSE 0 END +
                        CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END DESC,
                        a.id DESC NULLS LAST
                ) as rn
            FROM ufc_rankings r
            LEFT JOIN athletes a ON LOWER(TRIM(a.full_name)) = LOWER(TRIM(r.fighter_name))
            WHERE r.ranking_type IN ('Division', 'P4P')
        )
        SELECT
            rank,
            fighter_id,
            fighter_name,
            division,
            is_champion,
            is_interim_champion,
            headshot_url,
            flag_url,
            weight,
            height,
            reach,
            stance
        FROM ranked_fighters
        WHERE rn = 1
        ORDER BY
            CASE division
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
            rank
    """

    results = execute_query(query)

    # Group by division
    divisions = {}
    for row in results:
        division = row["division"]
        if division not in divisions:
            divisions[division] = []

        # Get fight count for fighter
        fight_count = 0
        if row["fighter_id"]:
            fight_count_query = """
                SELECT COUNT(*) as count
                FROM fights f
                WHERE f.fighter_1_id = ? OR f.fighter_2_id = ?
            """
            fight_count_result = execute_query(fight_count_query, (row["fighter_id"], row["fighter_id"]))
            fight_count = fight_count_result[0]["count"] if fight_count_result else 0

        # Parse weight and height to floats (they may be strings in DB)
        weight = None
        if row["weight"]:
            try:
                weight = float(str(row["weight"]).replace(" lbs", "").strip())
            except (ValueError, AttributeError):
                weight = None

        height = None
        if row["height"]:
            try:
                # Convert height like "6' 4"" to inches (76)
                height_str = str(row["height"]).strip()
                if "'" in height_str:
                    parts = height_str.replace('"', '').split("'")
                    feet = float(parts[0].strip())
                    inches = float(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
                    height = feet * 12 + inches
                else:
                    height = float(height_str)
            except (ValueError, AttributeError, IndexError):
                height = None

        reach = None
        if row["reach"]:
            try:
                reach = float(row["reach"])
            except (ValueError, TypeError):
                reach = None

        divisions[division].append({
            "rank": row["rank"],
            "fighter_id": row["fighter_id"],
            "fighter_name": row["fighter_name"],
            "division": division,
            "is_champion": bool(row["is_champion"]),
            "is_interim": bool(row["is_interim_champion"]),
            "headshot_url": row["headshot_url"],
            "flag_url": row["flag_url"],
            "weight": weight,
            "height": height,
            "reach": reach,
            "stance": row["stance"],
            "fight_count": fight_count
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
