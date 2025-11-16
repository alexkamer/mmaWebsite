"""Betting analytics API endpoints."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..database.connection import execute_query, execute_query_one

router = APIRouter()


@router.get("/years")
async def get_available_years(league: str = Query("ufc", description="League to filter by")):
    """Get available years with betting data for a league."""
    query = """
        SELECT DISTINCT strftime('%Y', c.date) as year
        FROM cards c
        JOIN fights f ON c.event_id = f.event_id
        WHERE LOWER(c.league) = LOWER(?)
        AND f.fighter_1_winner IS NOT NULL
        AND EXISTS (SELECT 1 FROM odds o WHERE o.fight_id = f.fight_id)
        ORDER BY year DESC
    """
    results = execute_query(query, (league,))
    return {"years": [int(r["year"]) for r in results if r["year"]]}


@router.get("/overview")
async def get_betting_overview(
    league: str = Query("ufc", description="League to filter by"),
    year: Optional[str] = Query(None, description="Year to filter by")
):
    """Get overall favorite vs underdog statistics."""

    # Build query with optional year filter
    year_filter = "AND strftime('%Y', c.date) = ?" if year else ""
    params = [league]
    if year:
        params.append(year)

    query = f"""
        WITH first_odds AS (
            SELECT
                f.fight_id,
                f.fighter_1_winner,
                f.fighter_2_winner,
                MIN(o.provider_id) as first_provider
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            JOIN odds o ON f.fight_id = o.fight_id
            WHERE LOWER(c.league) = LOWER(?)
            {year_filter}
            AND f.fighter_1_winner IS NOT NULL
            GROUP BY f.fight_id
        ),
        fight_outcomes AS (
            SELECT
                fo.fight_id,
                CASE
                    WHEN (o.home_favorite = 1 AND fo.fighter_1_winner = 1) OR
                         (o.away_favorite = 1 AND fo.fighter_2_winner = 1) THEN 'favorite'
                    WHEN (o.home_underdog = 1 AND fo.fighter_1_winner = 1) OR
                         (o.away_underdog = 1 AND fo.fighter_2_winner = 1) THEN 'underdog'
                    ELSE NULL
                END as outcome
            FROM first_odds fo
            JOIN odds o ON fo.fight_id = o.fight_id AND fo.first_provider = o.provider_id
        )
        SELECT
            COUNT(*) as total_fights,
            SUM(CASE WHEN outcome = 'favorite' THEN 1 ELSE 0 END) as favorite_wins,
            SUM(CASE WHEN outcome = 'underdog' THEN 1 ELSE 0 END) as underdog_wins
        FROM fight_outcomes
    """

    result = execute_query_one(query, tuple(params))

    if not result or result["total_fights"] == 0:
        return {
            "total_fights": 0,
            "favorite_wins": 0,
            "underdog_wins": 0,
            "favorite_win_pct": 0,
            "underdog_win_pct": 0
        }

    return {
        "total_fights": result["total_fights"],
        "favorite_wins": result["favorite_wins"],
        "underdog_wins": result["underdog_wins"],
        "favorite_win_pct": round((result["favorite_wins"] / result["total_fights"]) * 100, 1),
        "underdog_win_pct": round((result["underdog_wins"] / result["total_fights"]) * 100, 1)
    }


@router.get("/weight-classes")
async def get_weight_class_breakdown(
    league: str = Query("ufc", description="League to filter by"),
    year: Optional[str] = Query(None, description="Year to filter by")
):
    """Get favorite vs underdog performance by weight class."""

    year_filter = "AND strftime('%Y', c.date) = ?" if year else ""
    params = [league]
    if year:
        params.append(year)

    query = f"""
        WITH first_odds AS (
            SELECT
                f.fight_id,
                f.weight_class,
                f.fighter_1_winner,
                f.fighter_2_winner,
                MIN(o.provider_id) as first_provider
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            JOIN odds o ON f.fight_id = o.fight_id
            WHERE LOWER(c.league) = LOWER(?)
            {year_filter}
            AND f.fighter_1_winner IS NOT NULL
            AND f.weight_class IS NOT NULL
            GROUP BY f.fight_id
        ),
        fight_outcomes AS (
            SELECT
                fo.weight_class,
                CASE
                    WHEN (o.home_favorite = 1 AND fo.fighter_1_winner = 1) OR
                         (o.away_favorite = 1 AND fo.fighter_2_winner = 1) THEN 'favorite'
                    WHEN (o.home_underdog = 1 AND fo.fighter_1_winner = 1) OR
                         (o.away_underdog = 1 AND fo.fighter_2_winner = 1) THEN 'underdog'
                    ELSE NULL
                END as outcome
            FROM first_odds fo
            JOIN odds o ON fo.fight_id = o.fight_id AND fo.first_provider = o.provider_id
        )
        SELECT
            weight_class,
            COUNT(*) as total_fights,
            SUM(CASE WHEN outcome = 'favorite' THEN 1 ELSE 0 END) as favorite_wins,
            SUM(CASE WHEN outcome = 'underdog' THEN 1 ELSE 0 END) as underdog_wins
        FROM fight_outcomes
        WHERE weight_class IS NOT NULL
        GROUP BY weight_class
        HAVING COUNT(*) >= 3
        ORDER BY total_fights DESC
    """

    results = execute_query(query, tuple(params))

    weight_classes = []
    for row in results:
        total = row["total_fights"]
        weight_classes.append({
            "weight_class": row["weight_class"],
            "total_fights": total,
            "favorite_wins": row["favorite_wins"],
            "underdog_wins": row["underdog_wins"],
            "favorite_win_pct": round((row["favorite_wins"] / total) * 100, 1) if total > 0 else 0,
            "underdog_win_pct": round((row["underdog_wins"] / total) * 100, 1) if total > 0 else 0
        })

    return {"weight_classes": weight_classes}


@router.get("/rounds-format")
async def get_rounds_format_analysis(
    league: str = Query("ufc", description="League to filter by"),
    year: Optional[str] = Query(None, description="Year to filter by")
):
    """Get favorite vs underdog performance by rounds format (3-round vs 5-round)."""

    year_filter = "AND strftime('%Y', c.date) = ?" if year else ""
    params = [league]
    if year:
        params.append(year)

    query = f"""
        WITH first_odds AS (
            SELECT
                f.fight_id,
                f.rounds_format,
                f.fighter_1_winner,
                f.fighter_2_winner,
                MIN(o.provider_id) as first_provider
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            JOIN odds o ON f.fight_id = o.fight_id
            WHERE LOWER(c.league) = LOWER(?)
            {year_filter}
            AND f.fighter_1_winner IS NOT NULL
            AND f.rounds_format IN (3, 5)
            GROUP BY f.fight_id
        ),
        fight_outcomes AS (
            SELECT
                fo.rounds_format,
                CASE
                    WHEN (o.home_favorite = 1 AND fo.fighter_1_winner = 1) OR
                         (o.away_favorite = 1 AND fo.fighter_2_winner = 1) THEN 'favorite'
                    WHEN (o.home_underdog = 1 AND fo.fighter_1_winner = 1) OR
                         (o.away_underdog = 1 AND fo.fighter_2_winner = 1) THEN 'underdog'
                    ELSE NULL
                END as outcome
            FROM first_odds fo
            JOIN odds o ON fo.fight_id = o.fight_id AND fo.first_provider = o.provider_id
        )
        SELECT
            rounds_format,
            COUNT(*) as total_fights,
            SUM(CASE WHEN outcome = 'favorite' THEN 1 ELSE 0 END) as favorite_wins,
            SUM(CASE WHEN outcome = 'underdog' THEN 1 ELSE 0 END) as underdog_wins
        FROM fight_outcomes
        GROUP BY rounds_format
        ORDER BY rounds_format
    """

    results = execute_query(query, tuple(params))

    formats = []
    for row in results:
        total = row["total_fights"]
        formats.append({
            "rounds_format": row["rounds_format"],
            "total_fights": total,
            "favorite_wins": row["favorite_wins"],
            "underdog_wins": row["underdog_wins"],
            "favorite_win_pct": round((row["favorite_wins"] / total) * 100, 1) if total > 0 else 0,
            "underdog_win_pct": round((row["underdog_wins"] / total) * 100, 1) if total > 0 else 0
        })

    return {"formats": formats}


@router.get("/finish-types")
async def get_finish_types_by_weight_class(
    league: str = Query("ufc", description="League to filter by"),
    year: Optional[str] = Query(None, description="Year to filter by")
):
    """Get finish types (KO/TKO, Submission, Decision) by weight class."""

    year_filter = "AND strftime('%Y', c.date) = ?" if year else ""
    params = [league]
    if year:
        params.append(year)

    query = f"""
        SELECT
            f.weight_class,
            COUNT(*) as total_fights,
            SUM(CASE WHEN f.result_display_name LIKE '%Decision%' THEN 1 ELSE 0 END) as decisions,
            SUM(CASE WHEN f.result_display_name LIKE '%KO%' OR f.result_display_name LIKE '%TKO%' THEN 1 ELSE 0 END) as knockouts,
            SUM(CASE WHEN f.result_display_name LIKE '%Submission%' THEN 1 ELSE 0 END) as submissions
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        WHERE LOWER(c.league) = LOWER(?)
        {year_filter}
        AND f.fighter_1_winner IS NOT NULL
        AND f.weight_class IS NOT NULL
        AND f.result_display_name IS NOT NULL
        GROUP BY f.weight_class
        HAVING COUNT(*) >= 3
        ORDER BY total_fights DESC
    """

    results = execute_query(query, tuple(params))

    finish_types = []
    for row in results:
        total = row["total_fights"]
        finish_types.append({
            "weight_class": row["weight_class"],
            "total_fights": total,
            "decisions": row["decisions"],
            "knockouts": row["knockouts"],
            "submissions": row["submissions"],
            "decision_pct": round((row["decisions"] / total) * 100, 1) if total > 0 else 0,
            "knockout_pct": round((row["knockouts"] / total) * 100, 1) if total > 0 else 0,
            "submission_pct": round((row["submissions"] / total) * 100, 1) if total > 0 else 0,
            "finish_pct": round(((row["knockouts"] + row["submissions"]) / total) * 100, 1) if total > 0 else 0
        })

    return {"finish_types": finish_types}


@router.get("/cards")
async def get_cards_breakdown(
    league: str = Query("ufc", description="League to filter by"),
    year: Optional[str] = Query(None, description="Year to filter by")
):
    """Get card-by-card breakdown of betting performance."""

    year_filter = "AND strftime('%Y', c.date) = ?" if year else ""
    params = [league]
    if year:
        params.append(year)

    query = f"""
        WITH first_odds AS (
            SELECT
                f.fight_id,
                f.event_id,
                f.fighter_1_winner,
                f.fighter_2_winner,
                f.result_display_name,
                MIN(o.provider_id) as first_provider
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            JOIN odds o ON f.fight_id = o.fight_id
            WHERE LOWER(c.league) = LOWER(?)
            {year_filter}
            AND f.fighter_1_winner IS NOT NULL
            GROUP BY f.fight_id
        ),
        fight_outcomes AS (
            SELECT
                fo.event_id,
                fo.fight_id,
                fo.result_display_name,
                CASE
                    WHEN (o.home_favorite = 1 AND fo.fighter_1_winner = 1) OR
                         (o.away_favorite = 1 AND fo.fighter_2_winner = 1) THEN 'favorite'
                    WHEN (o.home_underdog = 1 AND fo.fighter_1_winner = 1) OR
                         (o.away_underdog = 1 AND fo.fighter_2_winner = 1) THEN 'underdog'
                    ELSE NULL
                END as outcome
            FROM first_odds fo
            JOIN odds o ON fo.fight_id = o.fight_id AND fo.first_provider = o.provider_id
        )
        SELECT
            c.event_id,
            c.event_name,
            c.date,
            COUNT(DISTINCT fo.fight_id) as fights_with_odds,
            SUM(CASE WHEN fo.outcome = 'favorite' THEN 1 ELSE 0 END) as favorite_wins,
            SUM(CASE WHEN fo.outcome = 'underdog' THEN 1 ELSE 0 END) as underdog_wins,
            SUM(CASE WHEN fo.result_display_name LIKE '%Decision%' THEN 1 ELSE 0 END) as decisions,
            SUM(CASE WHEN fo.result_display_name LIKE '%KO%' OR fo.result_display_name LIKE '%TKO%' THEN 1 ELSE 0 END) as knockouts,
            SUM(CASE WHEN fo.result_display_name LIKE '%Submission%' THEN 1 ELSE 0 END) as submissions
        FROM cards c
        JOIN fight_outcomes fo ON c.event_id = fo.event_id
        GROUP BY c.event_id, c.event_name, c.date
        HAVING COUNT(DISTINCT fo.fight_id) > 0
        ORDER BY c.date DESC
    """

    results = execute_query(query, tuple(params))

    cards = []
    for row in results:
        total = row["fights_with_odds"]
        cards.append({
            "event_id": row["event_id"],
            "event_name": row["event_name"],
            "date": row["date"],
            "fights_with_odds": total,
            "favorite_wins": row["favorite_wins"],
            "underdog_wins": row["underdog_wins"],
            "decisions": row["decisions"],
            "knockouts": row["knockouts"],
            "submissions": row["submissions"],
            "favorite_win_pct": round((row["favorite_wins"] / total) * 100, 1) if total > 0 else 0,
            "underdog_win_pct": round((row["underdog_wins"] / total) * 100, 1) if total > 0 else 0,
            "decision_pct": round((row["decisions"] / total) * 100, 1) if total > 0 else 0,
            "knockout_pct": round((row["knockouts"] / total) * 100, 1) if total > 0 else 0,
            "submission_pct": round((row["submissions"] / total) * 100, 1) if total > 0 else 0
        })

    return {"cards": cards, "total": len(cards)}
