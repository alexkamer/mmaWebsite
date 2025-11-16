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

    if promotion:
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

    # Get fights for this event
    fights_query = """
        SELECT
            f.id,
            a1.id as fighter1_id,
            a1.display_name as fighter1_name,
            a1.headshot_url as fighter1_image,
            a2.id as fighter2_id,
            a2.display_name as fighter2_name,
            a2.headshot_url as fighter2_image,
            f.winner_id,
            f.method,
            f.method_detail,
            f.round,
            f.time,
            f.weight_class,
            f.is_title_fight
        FROM fights f
        JOIN cards c ON f.card_id = c.year_league_event_id_event_name
        LEFT JOIN athletes a1 ON f.fighter_1_id = a1.id
        LEFT JOIN athletes a2 ON f.fighter_2_id = a2.id
        WHERE c.event_id = ?
        ORDER BY f.bout_order DESC
    """

    fights = execute_query(fights_query, (event_id,))

    # Add winner info to each fight
    for fight in fights:
        if fight["winner_id"] is None:
            fight["result"] = "No Contest/Draw"
        elif fight["winner_id"] == fight["fighter1_id"]:
            fight["winner"] = "fighter1"
        elif fight["winner_id"] == fight["fighter2_id"]:
            fight["winner"] = "fighter2"

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
