from sqlalchemy import text
from mma_website import db
from mma_website.utils.text_utils import row_to_dict
from datetime import datetime
import json

def get_fighter_timeline(fighter_id):
    """Get fighter timeline data with fights and rankings history"""
    db_session = db.session
    
    # Get fighter basic info
    fighter = db_session.execute(text("""
        SELECT *
        FROM athletes
        WHERE id = :fighter_id
    """), {"fighter_id": fighter_id}).fetchone()
    
    if not fighter:
        return None
        
    fighter_dict = row_to_dict(fighter)
    
    # Get all fights for the fighter
    fights = db_session.execute(text("""
        SELECT f.*, c.date, c.event_name
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        WHERE f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id
        ORDER BY c.date DESC
    """), {"fighter_id": fighter_id}).fetchall()
    
    # Get fighter's rankings history
    rankings = db_session.execute(text("""
        SELECT *
        FROM ufc_rankings
        WHERE fighter_name = :fighter_name
        ORDER BY last_updated DESC
    """), {"fighter_name": fighter_dict['full_name']}).fetchall()
    
    # Process fights into timeline events
    timeline_events = []
    
    for fight in fights:
        fight_dict = row_to_dict(fight)
        
        # Determine if fighter was fighter_1 or fighter_2
        is_fighter_1 = fight_dict['fighter_1_id'] == fighter_id
        opponent_id = fight_dict['fighter_2_id'] if is_fighter_1 else fight_dict['fighter_1_id']
        
        # Get opponent details using parameterized query
        opponent = db_session.execute(text("""
            SELECT full_name, headshot_url
            FROM athletes
            WHERE id = :opponent_id
        """), {"opponent_id": opponent_id}).fetchone()
        
        # Get fight statistics
        stats = None
        try:
            if fight_dict['fighter_1_statistics'] and is_fighter_1:
                stats = json.loads(fight_dict['fighter_1_statistics'])
            elif fight_dict['fighter_2_statistics'] and not is_fighter_1:
                stats = json.loads(fight_dict['fighter_2_statistics'])
        except (json.JSONDecodeError, TypeError):
            stats = None
            
        # Determine fight result
        result = None
        if fight_dict['result_display_name']:
            if 'Draw' in fight_dict['result_display_name']:
                result = 'draw'
            elif 'No Contest' in fight_dict['result_display_name']:
                result = 'nc'
            else:
                if is_fighter_1 and fight_dict['fighter_1_winner']:
                    result = 'win'
                elif not is_fighter_1 and fight_dict['fighter_2_winner']:
                    result = 'win'
                else:
                    result = 'loss'
                    
        # Extract method of victory
        method = None
        if fight_dict['result_display_name']:
            if 'KO' in fight_dict['result_display_name']:
                method = 'KO/TKO'
            elif 'Submission' in fight_dict['result_display_name']:
                method = 'Submission'
            elif 'Decision' in fight_dict['result_display_name']:
                method = 'Decision'
            elif 'DQ' in fight_dict['result_display_name']:
                method = 'Disqualification'
                
        # Create fight event
        fight_event = {
            'type': 'fights',
            'date': datetime.strptime(str(fight_dict['date']), '%Y-%m-%d %H:%M:%S.%f').strftime('%B %d, %Y'),
            'title': f"vs {opponent.full_name if opponent else 'Unknown'}",
            'opponent_headshot': opponent.headshot_url if opponent else None,
            'description': f"{fight_dict['event_name']} - {fight_dict['weight_class']}",
            'result': result,
            'method': method,
            'round': fight_dict['end_round'],
            'is_title_fight': bool(fight_dict['fight_title'] and ('Championship' in fight_dict['fight_title'] or 'Title' in fight_dict['fight_title'])),
            'stats': []
        }
        
        # Add fight statistics if available
        if stats:
            try:
                if 'strikes' in stats:
                    fight_event['stats'].append({
                        'label': 'Strikes',
                        'value': f"{stats['strikes']['landed']}/{stats['strikes']['attempted']}"
                    })
                if 'takedowns' in stats:
                    fight_event['stats'].append({
                        'label': 'Takedowns',
                        'value': f"{stats['takedowns']['landed']}/{stats['takedowns']['attempted']}"
                    })
                if 'submissions' in stats:
                    fight_event['stats'].append({
                        'label': 'Submissions',
                        'value': stats['submissions']
                    })
            except (KeyError, TypeError):
                # If any of the expected keys are missing or have unexpected types, skip adding stats
                pass
                
        timeline_events.append(fight_event)
        
    # Add ranking events
    for ranking in rankings:
        ranking_dict = row_to_dict(ranking)
        try:
            # Parse the date with microseconds
            ranking_date = datetime.strptime(str(ranking_dict['last_updated']), '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                # Try parsing without microseconds
                ranking_date = datetime.strptime(str(ranking_dict['last_updated']), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # If both fail, skip this ranking
                continue
                
        ranking_event = {
            'type': 'rankings',
            'date': ranking_date.strftime('%B %d, %Y'),
            'title': f"{ranking_dict['division']} Division",
            'description': f"Rank #{ranking_dict['rank']}" if ranking_dict['rank'] else "Champion" if ranking_dict['is_champion'] else "Interim Champion" if ranking_dict['is_interim_champion'] else "Unranked",
            'is_champion': bool(ranking_dict['is_champion']),
            'is_interim_champion': bool(ranking_dict['is_interim_champion'])
        }
        timeline_events.append(ranking_event)
        
    # Sort all events by date
    timeline_events.sort(key=lambda x: datetime.strptime(x['date'], '%B %d, %Y'))
    
    # Calculate fighter's record
    wins = sum(1 for fight in fights if (fight.fighter_1_id == fighter_id and fight.fighter_1_winner) or 
              (fight.fighter_2_id == fighter_id and fight.fighter_2_winner))
    losses = sum(1 for fight in fights if (fight.fighter_1_id == fighter_id and not fight.fighter_1_winner) or 
                (fight.fighter_2_id == fighter_id and not fight.fighter_2_winner))
    draws = sum(1 for fight in fights if (
        fight.fighter_1_id == fighter_id or fight.fighter_2_id == fighter_id) and 
        ('Draw' in fight.result_display_name or 'No Contest' in fight.result_display_name)
    )
                
    fighter_dict['record'] = f"{wins}-{losses}-{draws}"
    fighter_dict['timeline_events'] = timeline_events
    
    return fighter_dict