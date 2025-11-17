from sqlalchemy import text
from mma_website import db
from mma_website.utils.text_utils import row_to_dict
from typing import List, Dict, Any, Optional, Tuple

def get_event_years() -> List[str]:
    """Get distinct years with events"""
    db_session = db.session
    
    years = db_session.execute(text("""
        SELECT DISTINCT strftime('%Y', date) as year
        FROM cards
        WHERE date IS NOT NULL
        ORDER BY year DESC
    """)).fetchall()
    
    return [row[0] for row in years]

def get_event_year_for_event(event_id: int) -> Optional[str]:
    """Get the year for a specific event"""
    db_session = db.session
    
    event = db_session.execute(text("""
        SELECT strftime('%Y', date) as year
        FROM cards
        WHERE event_id = :event_id
    """), {"event_id": event_id}).fetchone()
    
    return event[0] if event else None

def get_events_for_year(year: str, limit: int = 200) -> List[Dict[str, Any]]:
    """Get events for a specific year, prioritizing UFC events"""
    db_session = db.session
    
    events = db_session.execute(text("""
        SELECT event_id, event_name, date, venue_name, city, country, league
        FROM cards
        WHERE strftime('%Y', date) = :year
        ORDER BY 
            CASE WHEN league = 'ufc' THEN 0 ELSE 1 END,
            date DESC
        LIMIT :limit
    """), {
        "year": year,
        "limit": limit
    }).fetchall()
    
    return [row_to_dict(event) for event in events]

def get_event_details(event_id: int) -> Optional[Dict[str, Any]]:
    """Get detailed information for an event including fights"""
    db_session = db.session
    
    # Get event basic info
    event = db_session.execute(text("""
        SELECT *
        FROM cards
        WHERE event_id = :event_id
    """), {"event_id": event_id}).fetchone()
    
    if not event:
        return None
        
    event_dict = row_to_dict(event)
    
    # Get event date for record calculation
    event_date = event_dict.get('date')

    # Get all fights for this event with fighter details and odds
    fights = db_session.execute(text("""
        WITH latest_odds AS (
            SELECT
                fight_id,
                home_athlete_id,
                away_athlete_id,
                home_moneyLine_odds_current_american,
                away_moneyLine_odds_current_american,
                ROW_NUMBER() OVER (PARTITION BY fight_id ORDER BY provider_id) as rn
            FROM odds
            WHERE provider_id != 59
        )
        SELECT
            f.*,
            a1.full_name as fighter_1_name,
            a1.headshot_url as fighter_1_headshot,
            a2.full_name as fighter_2_name,
            a2.headshot_url as fighter_2_headshot,
            CASE
                WHEN f.fighter_1_id = o.home_athlete_id THEN o.home_moneyLine_odds_current_american
                WHEN f.fighter_1_id = o.away_athlete_id THEN o.away_moneyLine_odds_current_american
                ELSE NULL
            END as fighter_1_odds,
            CASE
                WHEN f.fighter_2_id = o.home_athlete_id THEN o.home_moneyLine_odds_current_american
                WHEN f.fighter_2_id = o.away_athlete_id THEN o.away_moneyLine_odds_current_american
                ELSE NULL
            END as fighter_2_odds
        FROM fights f
        JOIN athletes a1 ON f.fighter_1_id = a1.id
        JOIN athletes a2 ON f.fighter_2_id = a2.id
        LEFT JOIN latest_odds o ON f.fight_id = o.fight_id AND o.rn = 1
        WHERE f.event_id = :event_id
        ORDER BY f.match_number DESC
    """), {"event_id": event_id}).fetchall()
    
    # Process fights and check for stats availability
    event_dict['fights'] = []
    for fight in fights:
        fight_dict = row_to_dict(fight)

        # Calculate fighter 1 record (fights before this event)
        if event_date:
            record1 = db_session.execute(text("""
                SELECT
                    SUM(CASE WHEN (f.fighter_1_id = :fighter_id AND f.fighter_1_winner = 1) OR
                                  (f.fighter_2_id = :fighter_id AND f.fighter_2_winner = 1) THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN (f.fighter_1_id = :fighter_id AND f.fighter_2_winner = 1) OR
                                  (f.fighter_2_id = :fighter_id AND f.fighter_1_winner = 1) THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN (f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id) AND
                                  f.fighter_1_winner = 0 AND f.fighter_2_winner = 0 THEN 1 ELSE 0 END) as draws
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                WHERE (f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id)
                AND c.date < :event_date
            """), {"fighter_id": fight.fighter_1_id, "event_date": event_date}).fetchone()

            if record1 and record1.wins is not None:
                fight_dict['fighter_1_record'] = f"{record1.wins}-{record1.losses}-{record1.draws}"
            else:
                fight_dict['fighter_1_record'] = None
        else:
            fight_dict['fighter_1_record'] = None

        # Calculate fighter 2 record (fights before this event)
        if event_date:
            record2 = db_session.execute(text("""
                SELECT
                    SUM(CASE WHEN (f.fighter_1_id = :fighter_id AND f.fighter_1_winner = 1) OR
                                  (f.fighter_2_id = :fighter_id AND f.fighter_2_winner = 1) THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN (f.fighter_1_id = :fighter_id AND f.fighter_2_winner = 1) OR
                                  (f.fighter_2_id = :fighter_id AND f.fighter_1_winner = 1) THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN (f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id) AND
                                  f.fighter_1_winner = 0 AND f.fighter_2_winner = 0 THEN 1 ELSE 0 END) as draws
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                WHERE (f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id)
                AND c.date < :event_date
            """), {"fighter_id": fight.fighter_2_id, "event_date": event_date}).fetchone()

            if record2 and record2.wins is not None:
                fight_dict['fighter_2_record'] = f"{record2.wins}-{record2.losses}-{record2.draws}"
            else:
                fight_dict['fighter_2_record'] = None
        else:
            fight_dict['fighter_2_record'] = None

        # Check if statistics are available for this fight
        stats = db_session.execute(text("""
            SELECT COUNT(*) as count
            FROM statistics_for_fights
            WHERE event_id = :event_id
            AND (athlete_id = :fighter_1_id OR athlete_id = :fighter_2_id)
        """), {
            "event_id": event_id,
            "fighter_1_id": fight.fighter_1_id,
            "fighter_2_id": fight.fighter_2_id
        }).scalar()

        fight_dict['has_stats'] = stats > 0
        event_dict['fights'].append(fight_dict)

    return event_dict

def get_fight_stats(fight_id: str) -> Dict[str, Any]:
    """Get fight statistics for both fighters in a fight"""
    db_session = db.session
    
    # Get fight details to get fighter IDs and event_id
    fight = db_session.execute(text("""
        SELECT f.fighter_1_id, f.fighter_2_id, c.event_id
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        WHERE f.event_id_fight_id = :fight_id
    """), {"fight_id": fight_id}).fetchone()
    
    if not fight:
        return {"error": "Fight not found"}
    
    # Get stats for the first fighter
    fighter1_stats = db_session.execute(text("""
        SELECT 
            totalStrikesLanded,
            totalStrikesAttempted,
            sigStrikesLanded,
            sigStrikesAttempted,
            takedownsLanded,
            takedownsAttempted,
            knockDowns
        FROM statistics_for_fights
        WHERE athlete_id = :fighter_id
        AND event_id = :event_id
    """), {
        "fighter_id": fight.fighter_1_id,
        "event_id": fight.event_id
    }).fetchone()
    
    # Get stats for the second fighter
    fighter2_stats = db_session.execute(text("""
        SELECT 
            totalStrikesLanded,
            totalStrikesAttempted,
            sigStrikesLanded,
            sigStrikesAttempted,
            takedownsLanded,
            takedownsAttempted,
            knockDowns
        FROM statistics_for_fights
        WHERE athlete_id = :fighter_id
        AND event_id = :event_id
    """), {
        "fighter_id": fight.fighter_2_id,
        "event_id": fight.event_id
    }).fetchone()
    
    return {
        "fighter1_stats": row_to_dict(fighter1_stats) if fighter1_stats else None,
        "fighter2_stats": row_to_dict(fighter2_stats) if fighter2_stats else None
    }