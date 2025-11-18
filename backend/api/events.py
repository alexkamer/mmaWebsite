"""Event API endpoints."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..database.connection import execute_query, execute_query_one
from ..models.event import EventBase, EventDetail, EventListResponse

router = APIRouter()


@router.get("/", response_model=EventListResponse)
async def list_events(
    year: Optional[int] = None,
    promotion: Optional[str] = Query(None, description="Filter by promotion (e.g., 'ufc')"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get list of events with optional filtering.
    """
    where_clauses = []
    params = []

    if year:
        where_clauses.append("strftime('%Y', date) = ?")
        params.append(str(year))

    # Only apply promotion filter if it's not "all" or empty
    if promotion and promotion.lower() != "all":
        where_clauses.append("LOWER(league) = LOWER(?)")
        params.append(promotion)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    query = f"""
        SELECT
            event_id as id,
            event_name as name,
            date,
            COALESCE(city || ', ' || state, city, state, country) as location,
            league as promotion
        FROM cards
        WHERE {where_sql}
        ORDER BY date DESC
        LIMIT ?
    """
    params.append(limit)

    events = execute_query(query, tuple(params))

    return {
        "events": events,
        "total": len(events)
    }


@router.get("/years")
async def get_event_years():
    """
    Get list of years with events.
    """
    query = """
        SELECT DISTINCT strftime('%Y', date) as year
        FROM cards
        WHERE date IS NOT NULL
        ORDER BY year DESC
    """
    results = execute_query(query)
    return {"years": [int(r["year"]) for r in results if r["year"]]}


@router.get("/recent-finishes")
async def get_recent_finishes(
    limit: int = Query(12, ge=1, le=50, description="Number of recent finishes to return"),
    promotion: Optional[str] = Query("ufc", description="Filter by promotion (e.g., 'ufc')")
):
    """
    Get recent spectacular finishes (KOs, TKOs, and Submissions).
    Returns fights with finish details and fighter information.
    """
    query = """
        SELECT
            f.fight_id,
            f.event_id,
            c.event_name,
            c.date as event_date,
            a1.id as fighter1_id,
            COALESCE(a1.display_name, a1.full_name, 'Unknown') as fighter1_name,
            a1.headshot_url as fighter1_image,
            a2.id as fighter2_id,
            COALESCE(a2.display_name, a2.full_name, 'Unknown') as fighter2_name,
            a2.headshot_url as fighter2_image,
            CASE
                WHEN f.fighter_1_winner = 1 THEN COALESCE(a1.display_name, a1.full_name, 'Unknown')
                WHEN f.fighter_2_winner = 1 THEN COALESCE(a2.display_name, a2.full_name, 'Unknown')
                ELSE 'Unknown'
            END as winner_name,
            CASE
                WHEN f.fighter_1_winner = 1 THEN a1.id
                WHEN f.fighter_2_winner = 1 THEN a2.id
                ELSE NULL
            END as winner_id,
            CASE
                WHEN f.fighter_1_winner = 1 THEN a1.headshot_url
                WHEN f.fighter_2_winner = 1 THEN a2.headshot_url
                ELSE NULL
            END as winner_image,
            f.result_display_name as finish_type,
            f.end_round as round,
            f.end_time as time,
            f.weight_class
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        LEFT JOIN athletes a1 ON f.fighter_1_id = a1.id
        LEFT JOIN athletes a2 ON f.fighter_2_id = a2.id
        WHERE (
            f.result_display_name LIKE 'KO%'
            OR f.result_display_name LIKE 'TKO%'
            OR f.result_display_name LIKE 'Submission%'
        )
        AND c.league = LOWER(?)
        AND c.date IS NOT NULL
        ORDER BY c.date DESC, f.match_number DESC
        LIMIT ?
    """

    finishes = execute_query(query, (promotion, limit))

    return {
        "finishes": finishes,
        "total": len(finishes)
    }


@router.get("/{event_id}")
async def get_event(event_id: int):
    """
    Get detailed information about a specific event including fight card.
    """
    # Get event details
    event_query = """
        SELECT
            event_id as id,
            event_name as name,
            date,
            venue_name as venue,
            COALESCE(city || ', ' || state, city, state, country) as location,
            league as promotion
        FROM cards
        WHERE event_id = ?
        LIMIT 1
    """

    event = execute_query_one(event_query, (event_id,))

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get fights for this event with fighter records and odds
    fights_query = """
        SELECT
            f.year_league_event_id_fight_id_f1_f2 as id,
            a1.id as fighter1_id,
            COALESCE(a1.display_name, a1.full_name, 'Unknown') as fighter1_name,
            a1.headshot_url as fighter1_image,
            a2.id as fighter2_id,
            COALESCE(a2.display_name, a2.full_name, 'Unknown') as fighter2_name,
            a2.headshot_url as fighter2_image,
            f.fighter_1_winner,
            f.fighter_2_winner,
            f.result_display_name as method,
            f.end_round as round,
            f.end_time as time,
            f.weight_class,
            f.fight_title as is_title_fight,
            f.match_number,
            f.card_segment
        FROM fights f
        LEFT JOIN athletes a1 ON f.fighter_1_id = a1.id
        LEFT JOIN athletes a2 ON f.fighter_2_id = a2.id
        WHERE f.event_id = ?
        ORDER BY f.match_number DESC
    """

    fights = execute_query(fights_query, (event_id,))

    # Get fighter records and odds for each fight
    for fight in fights:
        # Calculate fighter 1 record
        record_query = """
            SELECT
                SUM(CASE WHEN (f.fighter_1_id = ? AND f.fighter_1_winner = 1) OR
                              (f.fighter_2_id = ? AND f.fighter_2_winner = 1) THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN (f.fighter_1_id = ? AND f.fighter_2_winner = 1) OR
                              (f.fighter_2_id = ? AND f.fighter_1_winner = 1) THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN (f.fighter_1_id = ? OR f.fighter_2_id = ?) AND
                              f.fighter_1_winner = 0 AND f.fighter_2_winner = 0 THEN 1 ELSE 0 END) as draws
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            WHERE (f.fighter_1_id = ? OR f.fighter_2_id = ?)
            AND c.date < (SELECT date FROM cards WHERE event_id = ?)
        """

        fighter1_id = fight["fighter1_id"]
        fighter2_id = fight["fighter2_id"]

        if fighter1_id:
            record1 = execute_query_one(record_query, (
                fighter1_id, fighter1_id, fighter1_id, fighter1_id,
                fighter1_id, fighter1_id, fighter1_id, fighter1_id, event_id
            ))
            if record1 and record1["wins"] is not None:
                fight["fighter1_record"] = f"{record1['wins']}-{record1['losses']}-{record1['draws']}"
            else:
                fight["fighter1_record"] = None

        if fighter2_id:
            record2 = execute_query_one(record_query, (
                fighter2_id, fighter2_id, fighter2_id, fighter2_id,
                fighter2_id, fighter2_id, fighter2_id, fighter2_id, event_id
            ))
            if record2 and record2["wins"] is not None:
                fight["fighter2_record"] = f"{record2['wins']}-{record2['losses']}-{record2['draws']}"
            else:
                fight["fighter2_record"] = None

        # Get odds if available
        odds_query = """
            SELECT
                CASE WHEN home_athlete_id = ? THEN home_moneyLine_odds_current_american
                     WHEN away_athlete_id = ? THEN away_moneyLine_odds_current_american
                     ELSE NULL END as fighter1_odds,
                CASE WHEN home_athlete_id = ? THEN home_moneyLine_odds_current_american
                     WHEN away_athlete_id = ? THEN away_moneyLine_odds_current_american
                     ELSE NULL END as fighter2_odds
            FROM odds
            WHERE fight_id = ?
            ORDER BY provider_name = 'consensus' DESC
            LIMIT 1
        """

        odds = execute_query_one(odds_query, (
            str(fighter1_id), str(fighter1_id),
            str(fighter2_id), str(fighter2_id),
            str(fight["id"])
        ))

        if odds:
            fight["fighter1_odds"] = odds.get("fighter1_odds")
            fight["fighter2_odds"] = odds.get("fighter2_odds")
        else:
            fight["fighter1_odds"] = None
            fight["fighter2_odds"] = None

    # Add winner info to each fight
    for fight in fights:
        if fight["fighter_1_winner"] == 0 and fight["fighter_2_winner"] == 0:
            fight["result"] = "No Contest/Draw"
            fight["winner"] = None
        elif fight["fighter_1_winner"] == 1:
            fight["winner"] = "fighter1"
        elif fight["fighter_2_winner"] == 1:
            fight["winner"] = "fighter2"
        else:
            fight["winner"] = None

    event_dict = dict(event)
    event_dict["fights"] = fights

    return event_dict


@router.get("/upcoming/next")
async def get_next_event():
    """
    Get the next upcoming event.
    """
    query = """
        SELECT
            event_id as id,
            event_name as name,
            date,
            COALESCE(city || ', ' || state, city, state, country) as location,
            league as promotion
        FROM cards
        WHERE date >= date('now')
        ORDER BY date ASC
        LIMIT 1
    """

    event = execute_query_one(query)

    if not event:
        return {"message": "No upcoming events found"}

    return event
