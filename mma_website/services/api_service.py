from sqlalchemy import text
from mma_website import db
from mma_website.utils.text_utils import row_to_dict
from typing import List, Dict, Any, Optional, Tuple

def search_fighters(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for fighters by name
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of fighter dictionaries
    """
    if not query or len(query) < 2:
        return []
        
    db_session = db.session
    
    fighters = db_session.execute(text("""
        SELECT id, full_name, weight_class, headshot_url
        FROM athletes
        WHERE default_league LIKE 'ufc%'
        AND (
            LOWER(full_name) LIKE :query
            OR LOWER(full_name) LIKE :query_start
            OR LOWER(full_name) LIKE :query_end
            OR LOWER(full_name) LIKE :query_contains
        )
        ORDER BY 
            CASE 
                WHEN LOWER(full_name) = LOWER(:exact_query) THEN 1
                WHEN LOWER(full_name) LIKE :query_start THEN 2
                WHEN LOWER(full_name) LIKE :query_end THEN 3
                ELSE 4
            END,
            full_name
        LIMIT :limit
    """), {
        "query": f"%{query.lower()}%",
        "query_start": f"{query.lower()}%",
        "query_end": f"%{query.lower()}",
        "query_contains": f"%{query.lower()}%",
        "exact_query": query.lower(),
        "limit": limit
    }).fetchall()
    
    return [row_to_dict(fighter) for fighter in fighters]

def get_fight_details(fight_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a fight
    
    Args:
        fight_id: The fight ID in format 'event_id_fight_id'
        
    Returns:
        Fight details dictionary or None if not found
    """
    db_session = db.session
    
    # Parse fight_id (format: event_id_fight_id)
    try:
        event_id, competition_id = fight_id.split('_')
        event_id = int(event_id)
        competition_id = int(competition_id)
    except (ValueError, AttributeError):
        return None
    
    # Get fight details
    fight = db_session.execute(text("""
        SELECT f.*, c.event_name, c.date,
               a1.full_name as fighter_1_name, a1.headshot_url as fighter_1_headshot,
               a2.full_name as fighter_2_name, a2.headshot_url as fighter_2_headshot
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        JOIN athletes a1 ON f.fighter_1_id = a1.id
        JOIN athletes a2 ON f.fighter_2_id = a2.id
        WHERE f.event_id = :event_id AND f.fight_id = :competition_id
    """), {"event_id": event_id, "competition_id": competition_id}).fetchone()
    
    if not fight:
        return None
    
    fight_dict = row_to_dict(fight)
    
    # Get statistics for both fighters
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
        "event_id": event_id
    }).fetchone()
    
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
        "event_id": event_id
    }).fetchone()
    
    fight_dict['fighter1_stats'] = row_to_dict(fighter1_stats) if fighter1_stats else None
    fight_dict['fighter2_stats'] = row_to_dict(fighter2_stats) if fighter2_stats else None
    
    return fight_dict