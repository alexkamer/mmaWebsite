"""Homepage API endpoints."""
import httpx
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from ..database.connection import execute_query

router = APIRouter()


@router.get("/")
async def get_homepage_data():
    """
    Get all data needed for the homepage.

    Returns:
        - recent_events: List of recent UFC events
        - upcoming_events: List of upcoming UFC events (from ESPN API)
        - current_champions: List of current UFC champions
        - featured_fighters: List of featured top-ranked fighters
    """

    # Get recent UFC events (last 5)
    recent_events_query = """
        SELECT
            event_id as id,
            event_name as name,
            date,
            venue_name,
            city,
            country,
            league as promotion
        FROM cards
        WHERE league = 'ufc'
        ORDER BY date DESC
        LIMIT 5
    """
    recent_events = execute_query(recent_events_query)

    # Get upcoming UFC events from ESPN API
    upcoming_events = []
    try:
        ufc_events_url = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/events/?lang=en&region=us"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(ufc_events_url)
            response.raise_for_status()
            events_data = response.json()

            # Get up to 3 upcoming events
            for item in events_data.get('items', [])[:3]:
                event_url = item.get('$ref')
                if event_url:
                    try:
                        event_response = await client.get(event_url)
                        event_response.raise_for_status()
                        event_data = event_response.json()

                        # Parse event data
                        raw_date = event_data.get("date", "").split("T")[0]
                        try:
                            event_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                            # Only include future events
                            if event_date >= datetime.now().date():
                                venue = event_data.get("competitions", [{}])[0].get("venue", {})
                                address = venue.get("address", {})

                                upcoming_events.append({
                                    'id': event_data.get('id'),
                                    'name': event_data.get('name'),
                                    'date': event_date.isoformat(),
                                    'venue_name': venue.get('fullName', 'TBD'),
                                    'city': address.get('city', 'TBD'),
                                    'country': address.get('country', 'TBD'),
                                    'promotion': 'ufc'
                                })
                        except Exception as e:
                            print(f"Error parsing event date: {e}")
                            continue
                    except Exception as e:
                        print(f"Error fetching event details: {e}")
                        continue
    except Exception as e:
        print(f"Error fetching upcoming events from ESPN: {e}")
        # Fallback to database if ESPN API fails
        upcoming_fallback_query = """
            SELECT
                event_id as id,
                event_name as name,
                date,
                venue_name,
                city,
                country,
                league as promotion
            FROM cards
            WHERE league = 'ufc'
            AND date > date('now')
            ORDER BY date ASC
            LIMIT 3
        """
        upcoming_events = execute_query(upcoming_fallback_query)

    # Get current UFC champions
    champions_query = """
        WITH ranked_champions AS (
            SELECT DISTINCT
                r.division,
                r.fighter_name as full_name,
                a.headshot_url,
                a.id as athlete_id,
                CASE
                    WHEN r.is_champion = 1 THEN 'C'
                    WHEN r.is_interim_champion = 1 THEN 'IC'
                    ELSE 'R'
                END as position,
                ROW_NUMBER() OVER (
                    PARTITION BY r.division, r.fighter_name
                    ORDER BY
                        CASE WHEN a.headshot_url IS NOT NULL AND a.headshot_url != '' THEN 2 ELSE 0 END +
                        CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END DESC,
                        a.id DESC NULLS LAST
                ) as rn
            FROM ufc_rankings r
            LEFT JOIN athletes a ON LOWER(TRIM(a.full_name)) = LOWER(TRIM(r.fighter_name))
            WHERE (r.is_champion = 1 OR r.is_interim_champion = 1)
            AND r.ranking_type = 'Division'
        )
        SELECT division, full_name, headshot_url, athlete_id, position
        FROM ranked_champions
        WHERE rn = 1
        ORDER BY
            CASE division
                WHEN 'Heavyweight' THEN 1
                WHEN 'Light Heavyweight' THEN 2
                WHEN 'Middleweight' THEN 3
                WHEN 'Welterweight' THEN 4
                WHEN 'Lightweight' THEN 5
                WHEN 'Featherweight' THEN 6
                WHEN 'Bantamweight' THEN 7
                WHEN 'Flyweight' THEN 8
                WHEN "Women's Bantamweight" THEN 9
                WHEN "Women's Flyweight" THEN 10
                WHEN "Women's Strawweight" THEN 11
                ELSE 99
            END
    """
    current_champions = execute_query(champions_query)

    # Get featured fighters - top ranked fighters from different divisions
    featured_fighters_query = """
        WITH ranked_fighters AS (
            SELECT DISTINCT
                r.fighter_name,
                r.division,
                r.rank,
                a.id,
                a.full_name,
                a.headshot_url,
                a.weight_class,
                CASE
                    WHEN r.is_champion = 1 THEN 'C'
                    WHEN r.is_interim_champion = 1 THEN 'IC'
                    ELSE CAST(r.rank AS TEXT)
                END as position,
                ROW_NUMBER() OVER (PARTITION BY r.division ORDER BY r.rank) as rn
            FROM ufc_rankings r
            LEFT JOIN athletes a ON LOWER(TRIM(a.full_name)) = LOWER(TRIM(r.fighter_name))
            WHERE r.ranking_type = 'Division'
            AND r.rank BETWEEN 1 AND 5
            AND a.id IS NOT NULL
        )
        SELECT
            id,
            full_name,
            headshot_url,
            weight_class,
            division,
            position,
            rank
        FROM ranked_fighters
        WHERE rn = 1
        ORDER BY RANDOM()
        LIMIT 4
    """
    featured_fighters = execute_query(featured_fighters_query)

    # Get fight count for each featured fighter
    for fighter in featured_fighters:
        fight_count_query = """
            SELECT COUNT(*) as fight_count
            FROM fights f
            WHERE f.fighter_1_id = ? OR f.fighter_2_id = ?
        """
        result = execute_query(fight_count_query, (fighter['id'], fighter['id']))
        fighter['fight_count'] = result[0]['fight_count'] if result else 0

    return {
        "recent_events": recent_events,
        "upcoming_events": upcoming_events,
        "current_champions": current_champions,
        "featured_fighters": featured_fighters
    }
