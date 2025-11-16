from flask import Blueprint, render_template, request, jsonify, session
from sqlalchemy import text
from mma_website import db
from mma_website.utils.text_utils import row_to_dict, normalize_ascii
from mma_website.utils.helpers import process_next_event, get_odds_data, get_prop_data, get_linescore_data
import random
import json
import httpx

bp = Blueprint('games', __name__)

@bp.route('/fighter-wordle')
def fighter_wordle():
    """Fighter Wordle game page"""
    return render_template('fighter_wordle.html')

@bp.route('/api/fighter-wordle/new-game')
def new_fighter_wordle_game():
    """Start a new Fighter Wordle game"""
    db_session = db.session
    
    # Get a random UFC fighter
    fighter = db_session.execute(text("""
        SELECT id, full_name, weight_class, headshot_url
        FROM athletes
        WHERE default_league LIKE 'ufc%'
        AND full_name IS NOT NULL
        AND full_name != ''
        ORDER BY RANDOM()
        LIMIT 1
    """)).fetchone()
    
    if not fighter:
        return jsonify({"error": "No fighters found"}), 404
    
    fighter_dict = row_to_dict(fighter)
    
    # Store the answer in session
    session['wordle_answer'] = fighter_dict['full_name'].lower()
    session['wordle_attempts'] = 0
    session['wordle_max_attempts'] = 6
    session['wordle_game_over'] = False
    
    return jsonify({
        "message": "New game started",
        "max_attempts": session['wordle_max_attempts']
    })

@bp.route('/api/fighter-wordle/check-guess', methods=['POST'])
def check_fighter_wordle_guess():
    """Check a Fighter Wordle guess"""
    data = request.get_json()
    guess = data.get('guess', '').strip()
    
    if not guess:
        return jsonify({"error": "No guess provided"}), 400
    
    # Get answer from session
    answer = session.get('wordle_answer')
    if not answer:
        return jsonify({"error": "No active game"}), 400
    
    if session.get('wordle_game_over'):
        return jsonify({"error": "Game is over"}), 400
    
    # Increment attempts
    session['wordle_attempts'] = session.get('wordle_attempts', 0) + 1
    
    # Normalize both guess and answer for comparison
    normalized_guess = normalize_ascii(guess)
    normalized_answer = normalize_ascii(answer)
    
    # Check if guess is correct
    is_correct = normalized_guess == normalized_answer
    
    # Calculate feedback (similar to Wordle)
    feedback = []
    answer_chars = list(normalized_answer)
    guess_chars = list(normalized_guess)
    
    # First pass: mark correct positions
    for i, (guess_char, answer_char) in enumerate(zip(guess_chars, answer_chars)):
        if guess_char == answer_char:
            feedback.append('correct')
            answer_chars[i] = None  # Mark as used
        else:
            feedback.append('incorrect')
    
    # Second pass: mark misplaced characters
    for i, (guess_char, answer_char) in enumerate(zip(guess_chars, answer_chars)):
        if feedback[i] == 'incorrect' and guess_char in answer_chars:
            feedback[i] = 'misplaced'
            # Remove the first occurrence of this character
            for j, char in enumerate(answer_chars):
                if char == guess_char:
                    answer_chars[j] = None
                    break
    
    # Check if game is over
    game_over = is_correct or session['wordle_attempts'] >= session['wordle_max_attempts']
    if game_over:
        session['wordle_game_over'] = True
    
    return jsonify({
        "feedback": feedback,
        "is_correct": is_correct,
        "attempts": session['wordle_attempts'],
        "max_attempts": session['wordle_max_attempts'],
        "game_over": game_over,
        "answer": answer if game_over else None
    })


@bp.route('/tale-of-tape')
def tale_of_tape():
    """Tale of the tape comparison page"""
    db_session = db.session
    
    # Get all UFC fighters for the dropdown
    fighters = db_session.execute(text("""
        SELECT id, full_name
        FROM athletes
        WHERE default_league LIKE 'ufc%'
        ORDER BY full_name
    """)).fetchall()
    fighters = [row_to_dict(row) for row in fighters]
    
    # Get selected fighters from query parameters
    fighter1_id = request.args.get('fighter1')
    fighter2_id = request.args.get('fighter2')
    
    # Get filter parameters for both fighters
    fighter1_filters = {
        'promotion': request.args.get('fighter1_promotion', 'all'),
        'rounds_format': request.args.get('fighter1_rounds_format', 'all'),
        'fight_type': request.args.get('fighter1_fight_type', 'all'),
        'weight_class': request.args.get('fighter1_weight_class', 'all'),
        'odds_type': request.args.get('fighter1_odds_type', 'all')
    }
    
    fighter2_filters = {
        'promotion': request.args.get('fighter2_promotion', 'all'),
        'rounds_format': request.args.get('fighter2_rounds_format', 'all'),
        'fight_type': request.args.get('fighter2_fight_type', 'all'),
        'weight_class': request.args.get('fighter2_weight_class', 'all'),
        'odds_type': request.args.get('fighter2_odds_type', 'all')
    }
    
    selected_fighter1 = None
    selected_fighter2 = None
    
    if fighter1_id:
        from mma_website.services.fighter_service import get_fighter_data
        selected_fighter1 = get_fighter_data(int(fighter1_id), fighter1_filters)
    
    if fighter2_id:
        from mma_website.services.fighter_service import get_fighter_data
        selected_fighter2 = get_fighter_data(int(fighter2_id), fighter2_filters)
    
    return render_template('tale_of_tape.html',
                         fighters=fighters,
                         selected_fighter1=selected_fighter1,
                         selected_fighter2=selected_fighter2,
                         fighter1_filters=fighter1_filters,
                         fighter2_filters=fighter2_filters)

@bp.route('/next-event')
def next_event():
    """Next UFC event page with ESPN API integration"""
    # Get the next UFC event URL
    ufc_events_url = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/events/?lang=en&region=us"
    ufc_event_response = httpx.get(ufc_events_url)
    ufc_event_response.raise_for_status()
    ufc_event_data = ufc_event_response.json()
    
    next_ufc_event_url = ufc_event_data['items'][0]['$ref']
    
    # Process the next event data
    card, fights = process_next_event(next_ufc_event_url)
    
    # Log initial fights data to see odds URLs
    print(f"🔍 Found {len(fights)} fights from ESPN API")
    for i, fight in enumerate(fights):
        odds_url = fight.get('odds_url')
        print(f"🎯 Fight {i+1}: {fight.get('fight_id')} - Odds URL: {odds_url}")
    
    if card:
        # Always show the event if we have card data
        if fights:
            db_session = db.session
            
            # Get all fighter IDs from the fights
            fighter_ids = set()
            for fight in fights:
                fighter_ids.add(fight['fighter_1_id'])
                fighter_ids.add(fight['fighter_2_id'])
            
            # Only do database lookups if we have fighter IDs
            if fighter_ids:
                # Convert fighter_ids to a comma-separated string for the IN clause
                fighter_ids_str = ','.join(f"'{id}'" for id in fighter_ids)
                
                try:
                    # Get all fighter details in one query
                    fighters = db_session.execute(text(f"""
                        SELECT id, full_name, headshot_url
                        FROM athletes
                        WHERE id IN ({fighter_ids_str})
                    """)).fetchall()
                    
                    # Create a lookup dictionary for fighter details
                    fighter_lookup = {str(f.id): f for f in fighters}
                    
                    # Get all fighter records in one query
                    fighter_records = db_session.execute(text(f"""
                        WITH fighter_results AS (
                            SELECT 
                                fighter_id,
                                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                                SUM(CASE WHEN won = 0 AND result_type NOT IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as losses,
                                SUM(CASE WHEN result_type IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as draws
                            FROM (
                                SELECT 
                                    fighter_1_id as fighter_id,
                                    fighter_1_winner as won,
                                    result_display_name as result_type
                                FROM fights
                                UNION ALL
                                SELECT 
                                    fighter_2_id as fighter_id,
                                    fighter_2_winner as won,
                                    result_display_name as result_type
                                FROM fights
                            ) combined
                            WHERE fighter_id IN ({fighter_ids_str})
                            GROUP BY fighter_id
                        )
                        SELECT 
                            fighter_id,
                            COALESCE(wins, 0) as wins,
                            COALESCE(losses, 0) as losses,
                            COALESCE(draws, 0) as draws
                        FROM fighter_results
                    """)).fetchall()
                    
                    # Create a lookup dictionary for fighter records
                    record_lookup = {str(r.fighter_id): f"{r.wins}-{r.losses}-{r.draws}" for r in fighter_records}
                    
                    # Process fights with the lookup data
                    for fight in fights:
                        # Add fighter 1 details (use ESPN data as fallback)
                        fighter1 = fighter_lookup.get(str(fight['fighter_1_id']))
                        if fighter1:
                            fight['fighter_1_name'] = fighter1.full_name
                            fight['fighter_1_headshot'] = fighter1.headshot_url
                            fight['fighter_1_record'] = record_lookup.get(str(fight['fighter_1_id']), "0-0-0")
                        else:
                            # Fallback: use fighter ID as name if not in database
                            fight['fighter_1_name'] = f"Fighter {fight['fighter_1_id']}"
                            fight['fighter_1_headshot'] = None
                            fight['fighter_1_record'] = "TBD"
                        
                        # Add fighter 2 details (use ESPN data as fallback)
                        fighter2 = fighter_lookup.get(str(fight['fighter_2_id']))
                        if fighter2:
                            fight['fighter_2_name'] = fighter2.full_name
                            fight['fighter_2_headshot'] = fighter2.headshot_url
                            fight['fighter_2_record'] = record_lookup.get(str(fight['fighter_2_id']), "0-0-0")
                        else:
                            # Fallback: use fighter ID as name if not in database
                            fight['fighter_2_name'] = f"Fighter {fight['fighter_2_id']}"
                            fight['fighter_2_headshot'] = None
                            fight['fighter_2_record'] = "TBD"
                        
                        # Get odds data if odds URL exists
                        if fight.get('odds_url'):
                            print(f"💰 Fetching odds from: {fight['odds_url']}")
                            try:
                                odds_data = get_odds_data(fight['odds_url'])
                                if odds_data:
                                    # Get the first provider's odds (usually the most recent)
                                    odds = odds_data[0] if isinstance(odds_data, list) else odds_data
                                    
                                    # Match odds to fighters based on athlete IDs
                                    if str(fight['fighter_1_id']) == odds.get('home_athlete_id'):
                                        fight['fighter_1_odds'] = odds.get('home_moneyLine_odds_current_american')
                                        fight['fighter_2_odds'] = odds.get('away_moneyLine_odds_current_american')
                                    elif str(fight['fighter_1_id']) == odds.get('away_athlete_id'):
                                        fight['fighter_1_odds'] = odds.get('away_moneyLine_odds_current_american')
                                        fight['fighter_2_odds'] = odds.get('home_moneyLine_odds_current_american')
                                    else:
                                        # If IDs don't match, try to match based on favorite/underdog status
                                        if odds.get('home_favorite'):
                                            fight['fighter_1_odds'] = odds.get('home_moneyLine_odds_current_american')
                                            fight['fighter_2_odds'] = odds.get('away_moneyLine_odds_current_american')
                                        else:
                                            fight['fighter_1_odds'] = odds.get('away_moneyLine_odds_current_american')
                                            fight['fighter_2_odds'] = odds.get('home_moneyLine_odds_current_american')
                            except Exception as e:
                                print(f"Error getting odds for fight {fight.get('fight_id')}: {e}")
                
                except Exception as e:
                    print(f"Error looking up fighters in database: {e}")
                    # Set fallback names for all fights
                    for fight in fights:
                        fight['fighter_1_name'] = f"Fighter {fight['fighter_1_id']}"
                        fight['fighter_2_name'] = f"Fighter {fight['fighter_2_id']}"
                        fight['fighter_1_record'] = "TBD"
                        fight['fighter_2_record'] = "TBD"
            
            # Sort fights by match_number
            fights.sort(key=lambda x: x.get('match_number', float('inf')))
        
        return render_template('next_event.html', 
                             event=card,
                             fights=fights)
    else:
        return render_template('next_event.html', 
                             event=None,
                             fights=[])

@bp.route('/fight-preview/<fighter1_id>/<fighter2_id>')
@bp.route('/fight-preview/<fighter1_id>/<fighter2_id>/<event_id>/<fight_id>')
def fight_preview(fighter1_id, fighter2_id, event_id=None, fight_id=None):
    """Detailed fight preview page with statistical analysis"""
    db_session = db.session
    
    # Get fighter details
    fighters_data = db_session.execute(text("""
        SELECT id, full_name, nickname, headshot_url, weight_class, height, weight, reach, 
               age, stance, association, association_city, flag_url
        FROM athletes
        WHERE id IN (:fighter1_id, :fighter2_id)
    """), {"fighter1_id": fighter1_id, "fighter2_id": fighter2_id}).fetchall()
    
    if len(fighters_data) < 2:
        # If fighters not in database, create basic info from ESPN
        fighter1 = {"id": fighter1_id, "full_name": f"Fighter {fighter1_id}", "nickname": None}
        fighter2 = {"id": fighter2_id, "full_name": f"Fighter {fighter2_id}", "nickname": None}
        return render_template('fight_preview.html',
                             fighter1=fighter1,
                             fighter2=fighter2,
                             comparison_stats={},
                             recent_fights={})
    
    # Organize fighter data
    fighters_dict = {str(f.id): row_to_dict(f) for f in fighters_data}
    fighter1 = fighters_dict.get(fighter1_id, {})
    fighter2 = fighters_dict.get(fighter2_id, {})
    
    # Get career statistics for both fighters (overall record)
    career_stats = db_session.execute(text("""
        WITH fighter_stats AS (
            SELECT 
                fighter_id,
                COUNT(*) as total_fights,
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN won = 0 AND result_type NOT IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result_type IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as draws,
                SUM(CASE WHEN won = 1 AND result_type LIKE '%KO%' THEN 1 ELSE 0 END) as ko_wins,
                SUM(CASE WHEN won = 1 AND result_type LIKE '%Submission%' THEN 1 ELSE 0 END) as sub_wins,
                SUM(CASE WHEN won = 1 AND result_type LIKE '%Decision%' THEN 1 ELSE 0 END) as dec_wins
            FROM (
                SELECT 
                    fighter_1_id as fighter_id,
                    fighter_1_winner as won,
                    result_display_name as result_type
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                UNION ALL
                SELECT 
                    fighter_2_id as fighter_id,
                    fighter_2_winner as won,
                    result_display_name as result_type
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
            ) combined
            WHERE fighter_id IN (:fighter1_id, :fighter2_id)
            GROUP BY fighter_id
        )
        SELECT * FROM fighter_stats
    """), {"fighter1_id": fighter1_id, "fighter2_id": fighter2_id}).fetchall()
    
    # Get UFC-specific records
    ufc_stats = db_session.execute(text("""
        WITH ufc_fighter_stats AS (
            SELECT 
                fighter_id,
                COUNT(*) as ufc_total_fights,
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as ufc_wins,
                SUM(CASE WHEN won = 0 AND result_type NOT IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as ufc_losses,
                SUM(CASE WHEN result_type IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as ufc_draws,
                SUM(CASE WHEN won = 1 AND result_type LIKE '%KO%' THEN 1 ELSE 0 END) as ufc_ko_wins,
                SUM(CASE WHEN won = 1 AND result_type LIKE '%Submission%' THEN 1 ELSE 0 END) as ufc_sub_wins,
                SUM(CASE WHEN won = 1 AND result_type LIKE '%Decision%' THEN 1 ELSE 0 END) as ufc_dec_wins
            FROM (
                SELECT 
                    fighter_1_id as fighter_id,
                    fighter_1_winner as won,
                    result_display_name as result_type
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                WHERE LOWER(c.league) = 'ufc'
                UNION ALL
                SELECT 
                    fighter_2_id as fighter_id,
                    fighter_2_winner as won,
                    result_display_name as result_type
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                WHERE LOWER(c.league) = 'ufc'
            ) combined
            WHERE fighter_id IN (:fighter1_id, :fighter2_id)
            GROUP BY fighter_id
        )
        SELECT * FROM ufc_fighter_stats
    """), {"fighter1_id": fighter1_id, "fighter2_id": fighter2_id}).fetchall()
    
    # Get weight class specific records for UFC fights
    weight_class_stats = db_session.execute(text("""
        WITH weight_class_stats AS (
            SELECT 
                fighter_id,
                weight_class,
                COUNT(*) as wc_total_fights,
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wc_wins,
                SUM(CASE WHEN won = 0 AND result_type NOT IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as wc_losses,
                SUM(CASE WHEN result_type IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as wc_draws
            FROM (
                SELECT 
                    fighter_1_id as fighter_id,
                    fighter_1_winner as won,
                    result_display_name as result_type,
                    f.weight_class
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                WHERE LOWER(c.league) = 'ufc'
                UNION ALL
                SELECT 
                    fighter_2_id as fighter_id,
                    fighter_2_winner as won,
                    result_display_name as result_type,
                    f.weight_class
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                WHERE LOWER(c.league) = 'ufc'
            ) combined
            WHERE fighter_id IN (:fighter1_id, :fighter2_id)
            GROUP BY fighter_id, weight_class
        )
        SELECT * FROM weight_class_stats
    """), {"fighter1_id": fighter1_id, "fighter2_id": fighter2_id}).fetchall()
    
    # Organize career stats
    stats_dict = {str(s.fighter_id): row_to_dict(s) for s in career_stats}
    
    # Organize UFC-specific stats
    ufc_stats_dict = {str(s.fighter_id): row_to_dict(s) for s in ufc_stats}
    
    # Organize weight class stats - get the stats for the current fight weight class
    fight_weight_class = fighter1.get('weight_class') or fighter2.get('weight_class')
    wc_stats_dict = {}
    for s in weight_class_stats:
        s_dict = row_to_dict(s)
        fighter_id_str = str(s.fighter_id)
        
        # Group by fighter_id, storing all weight classes
        if fighter_id_str not in wc_stats_dict:
            wc_stats_dict[fighter_id_str] = {}
        wc_stats_dict[fighter_id_str][s.weight_class] = s_dict
    
    # Get recent fights for both fighters (last 5 each) with victory method details, statistics, and odds
    recent_fights_data = db_session.execute(text("""
        SELECT DISTINCT f.fight_id, f.fighter_1_id, f.fighter_2_id, f.fighter_1_winner, f.fighter_2_winner,
               f.result_display_name, f.end_round, f.end_time, f.event_id, f.weight_class_id,
               c.date, c.event_name,
               CASE WHEN f.fighter_1_id = :fighter_id THEN a2.full_name ELSE a1.full_name END as opponent_name,
               CASE WHEN f.fighter_1_id = :fighter_id THEN a2.headshot_url ELSE a1.headshot_url END as opponent_headshot,
               CASE WHEN f.fighter_1_id = :fighter_id THEN f.fighter_1_winner ELSE f.fighter_2_winner END as won,
               f.result_display_name as victory_method,
               f.end_round,
               f.end_time,
               MAX(s.knockDowns) as knockDowns,
               MAX(s.sigStrikesLanded) as sigStrikesLanded,
               MAX(s.sigStrikesAttempted) as sigStrikesAttempted,
               MAX(s.totalStrikesLanded) as totalStrikesLanded,
               MAX(s.totalStrikesAttempted) as totalStrikesAttempted,
               MAX(s.takedownsLanded) as takedownsLanded,
               MAX(s.takedownsAttempted) as takedownsAttempted,
               MAX(s.takedownAccuracy) as takedownAccuracy,
               MAX(s.submissions) as submissions,
               MAX(CASE
                   WHEN o.home_athlete_id = :fighter_id THEN o.home_moneyLine_odds_current_american
                   WHEN o.away_athlete_id = :fighter_id THEN o.away_moneyLine_odds_current_american
                   ELSE NULL
               END) as fighter_odds,
               MAX(CASE
                   WHEN o.home_athlete_id = :fighter_id THEN o.home_favorite
                   WHEN o.away_athlete_id = :fighter_id THEN o.away_favorite
                   ELSE NULL
               END) as was_favorite,
               l1.judge_1_score as fighter_judge_1,
               l1.judge_2_score as fighter_judge_2,
               l1.judge_3_score as fighter_judge_3,
               l2.judge_1_score as opponent_judge_1,
               l2.judge_2_score as opponent_judge_2,
               l2.judge_3_score as opponent_judge_3
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        LEFT JOIN athletes a1 ON f.fighter_1_id = a1.id
        LEFT JOIN athletes a2 ON f.fighter_2_id = a2.id
        LEFT JOIN statistics_for_fights s ON (
            (f.fighter_1_id = :fighter_id AND s.event_id = f.event_id AND s.competition_id = f.fight_id AND s.athlete_id = f.fighter_1_id) OR
            (f.fighter_2_id = :fighter_id AND s.event_id = f.event_id AND s.competition_id = f.fight_id AND s.athlete_id = f.fighter_2_id)
        )
        LEFT JOIN odds o ON f.fight_id = o.fight_id
        LEFT JOIN linescores l1 ON f.fight_id = l1.fight_id AND :fighter_id = l1.fighter_id
        LEFT JOIN linescores l2 ON f.fight_id = l2.fight_id AND
                 CASE WHEN f.fighter_1_id = :fighter_id THEN f.fighter_2_id ELSE f.fighter_1_id END = l2.fighter_id
        WHERE f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id
        GROUP BY f.fight_id, f.fighter_1_id, f.fighter_2_id, f.fighter_1_winner, f.fighter_2_winner,
                 f.result_display_name, f.end_round, f.end_time, f.event_id, f.weight_class_id,
                 c.date, c.event_name, a1.full_name, a2.full_name, a1.headshot_url, a2.headshot_url,
                 l1.judge_1_score, l1.judge_2_score, l1.judge_3_score,
                 l2.judge_1_score, l2.judge_2_score, l2.judge_3_score
        ORDER BY c.date DESC
        LIMIT 5
    """), {"fighter_id": fighter1_id}).fetchall()
    
    recent_fights_f2 = db_session.execute(text("""
        SELECT DISTINCT f.fight_id, f.fighter_1_id, f.fighter_2_id, f.fighter_1_winner, f.fighter_2_winner,
               f.result_display_name, f.end_round, f.end_time, f.event_id, f.weight_class_id,
               c.date, c.event_name,
               CASE WHEN f.fighter_1_id = :fighter_id THEN a2.full_name ELSE a1.full_name END as opponent_name,
               CASE WHEN f.fighter_1_id = :fighter_id THEN a2.headshot_url ELSE a1.headshot_url END as opponent_headshot,
               CASE WHEN f.fighter_1_id = :fighter_id THEN f.fighter_1_winner ELSE f.fighter_2_winner END as won,
               f.result_display_name as victory_method,
               f.end_round,
               f.end_time,
               MAX(s.knockDowns) as knockDowns,
               MAX(s.sigStrikesLanded) as sigStrikesLanded,
               MAX(s.sigStrikesAttempted) as sigStrikesAttempted,
               MAX(s.totalStrikesLanded) as totalStrikesLanded,
               MAX(s.totalStrikesAttempted) as totalStrikesAttempted,
               MAX(s.takedownsLanded) as takedownsLanded,
               MAX(s.takedownsAttempted) as takedownsAttempted,
               MAX(s.takedownAccuracy) as takedownAccuracy,
               MAX(s.submissions) as submissions,
               MAX(CASE
                   WHEN o.home_athlete_id = :fighter_id THEN o.home_moneyLine_odds_current_american
                   WHEN o.away_athlete_id = :fighter_id THEN o.away_moneyLine_odds_current_american
                   ELSE NULL
               END) as fighter_odds,
               MAX(CASE
                   WHEN o.home_athlete_id = :fighter_id THEN o.home_favorite
                   WHEN o.away_athlete_id = :fighter_id THEN o.away_favorite
                   ELSE NULL
               END) as was_favorite,
               l1.judge_1_score as fighter_judge_1,
               l1.judge_2_score as fighter_judge_2,
               l1.judge_3_score as fighter_judge_3,
               l2.judge_1_score as opponent_judge_1,
               l2.judge_2_score as opponent_judge_2,
               l2.judge_3_score as opponent_judge_3
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        LEFT JOIN athletes a1 ON f.fighter_1_id = a1.id
        LEFT JOIN athletes a2 ON f.fighter_2_id = a2.id
        LEFT JOIN statistics_for_fights s ON (
            (f.fighter_1_id = :fighter_id AND s.event_id = f.event_id AND s.competition_id = f.fight_id AND s.athlete_id = f.fighter_1_id) OR
            (f.fighter_2_id = :fighter_id AND s.event_id = f.event_id AND s.competition_id = f.fight_id AND s.athlete_id = f.fighter_2_id)
        )
        LEFT JOIN odds o ON f.fight_id = o.fight_id
        LEFT JOIN linescores l1 ON f.fight_id = l1.fight_id AND :fighter_id = l1.fighter_id
        LEFT JOIN linescores l2 ON f.fight_id = l2.fight_id AND
                 CASE WHEN f.fighter_1_id = :fighter_id THEN f.fighter_2_id ELSE f.fighter_1_id END = l2.fighter_id
        WHERE f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id
        GROUP BY f.fight_id, f.fighter_1_id, f.fighter_2_id, f.fighter_1_winner, f.fighter_2_winner,
                 f.result_display_name, f.end_round, f.end_time, f.event_id, f.weight_class_id,
                 c.date, c.event_name, a1.full_name, a2.full_name, a1.headshot_url, a2.headshot_url,
                 l1.judge_1_score, l1.judge_2_score, l1.judge_3_score,
                 l2.judge_1_score, l2.judge_2_score, l2.judge_3_score
        ORDER BY c.date DESC
        LIMIT 5
    """), {"fighter_id": fighter2_id}).fetchall()
    
    # Add career stats to fighter objects
    fighter1.update(stats_dict.get(fighter1_id, {}))
    fighter2.update(stats_dict.get(fighter2_id, {}))
    
    # Add UFC-specific stats
    fighter1.update(ufc_stats_dict.get(fighter1_id, {}))
    fighter2.update(ufc_stats_dict.get(fighter2_id, {}))
    
    # Add weight class specific stats for the current fight weight class
    f1_wc_stats = wc_stats_dict.get(fighter1_id, {}).get(fight_weight_class, {})
    f2_wc_stats = wc_stats_dict.get(fighter2_id, {}).get(fight_weight_class, {})
    
    # Add weight class stats with prefix to avoid naming conflicts
    for key, value in f1_wc_stats.items():
        fighter1[f'weightclass_{key}'] = value
    for key, value in f2_wc_stats.items():
        fighter2[f'weightclass_{key}'] = value
    
    # Calculate comparison stats
    comparison_stats = calculate_fight_comparison(fighter1, fighter2)
    
    # Process recent fights with linescore data and performance trends
    def process_recent_fights_with_trends(fights_data):
        processed_fights = []
        for fight in fights_data:
            fight_dict = row_to_dict(fight)
            
            # Process linescore data for decisions from database
            if 'Decision' in fight_dict.get('victory_method', ''):
                # Fighter scorecard
                if fight_dict.get('fighter_judge_1') and fight_dict.get('fighter_judge_2') and fight_dict.get('fighter_judge_3'):
                    fight_dict['fighter_scorecard'] = {
                        'judge_1': fight_dict['fighter_judge_1'],
                        'judge_2': fight_dict['fighter_judge_2'], 
                        'judge_3': fight_dict['fighter_judge_3']
                    }
                
                # Opponent scorecard  
                if fight_dict.get('opponent_judge_1') and fight_dict.get('opponent_judge_2') and fight_dict.get('opponent_judge_3'):
                    fight_dict['opponent_scorecard'] = {
                        'judge_1': fight_dict['opponent_judge_1'],
                        'judge_2': fight_dict['opponent_judge_2'],
                        'judge_3': fight_dict['opponent_judge_3']
                    }
            
            processed_fights.append(fight_dict)
        return processed_fights

    # Calculate performance trends (streaks)
    def calculate_performance_trends(fights_list):
        if not fights_list:
            return {'current_streak': 'No recent fights', 'streak_type': 'none', 'last_5_record': '0-0'}
        
        # Sort by date (most recent first)
        sorted_fights = sorted(fights_list, key=lambda x: x.get('date', ''), reverse=True)
        
        # Calculate current streak
        current_streak = 0
        streak_type = 'none'
        
        if sorted_fights:
            last_result = sorted_fights[0].get('won')
            streak_type = 'win' if last_result else 'loss'
            
            for fight in sorted_fights:
                if fight.get('won') == last_result:
                    current_streak += 1
                else:
                    break
        
        # Calculate last 5 record
        last_5 = sorted_fights[:5]
        wins = sum(1 for f in last_5 if f.get('won'))
        losses = len(last_5) - wins
        
        return {
            'current_streak': current_streak,
            'streak_type': streak_type,
            'last_5_record': f"{wins}-{losses}",
            'last_5_wins': wins,
            'last_5_losses': losses
        }
    
    recent_fights_f1_processed = process_recent_fights_with_trends(recent_fights_data)
    recent_fights_f2_processed = process_recent_fights_with_trends(recent_fights_f2)
    
    recent_fights = {
        'fighter1': recent_fights_f1_processed,
        'fighter2': recent_fights_f2_processed
    }
    
    # Calculate performance trends for both fighters
    fighter1_trends = calculate_performance_trends(recent_fights_f1_processed)
    fighter2_trends = calculate_performance_trends(recent_fights_f2_processed)
    
    performance_trends = {
        'fighter1': fighter1_trends,
        'fighter2': fighter2_trends
    }
    
    # Prop betting removed - ESPN API doesn't provide enough detail to distinguish prop types
    prop_data = {'fight_props': [], 'fighter1_props': [], 'fighter2_props': []}
    
    # Get betting odds if fight_id is provided
    odds_data = None
    if fight_id:
        try:
            odds_result = db_session.execute(text("""
                SELECT
                    home_athlete_id,
                    away_athlete_id,
                    home_moneyLine_odds_current_american,
                    away_moneyLine_odds_current_american,
                    home_favorite
                FROM odds
                WHERE fight_id = :fight_id
                LIMIT 1
            """), {"fight_id": fight_id}).fetchone()

            if odds_result:
                odds_dict = row_to_dict(odds_result)
                # Match odds to fighters
                if str(fighter1_id) == odds_dict.get('home_athlete_id'):
                    odds_data = {
                        'fighter1_odds': odds_dict.get('home_moneyLine_odds_current_american'),
                        'fighter2_odds': odds_dict.get('away_moneyLine_odds_current_american'),
                        'fighter1_favorite': odds_dict.get('home_favorite', False)
                    }
                elif str(fighter1_id) == odds_dict.get('away_athlete_id'):
                    odds_data = {
                        'fighter1_odds': odds_dict.get('away_moneyLine_odds_current_american'),
                        'fighter2_odds': odds_dict.get('home_moneyLine_odds_current_american'),
                        'fighter1_favorite': not odds_dict.get('home_favorite', False)
                    }
        except Exception as e:
            print(f"Error fetching odds: {e}")

    # Generate AI fight prediction
    try:
        from mma_website.services.fight_prediction_service import fight_prediction_service
        ai_prediction = fight_prediction_service.generate_fight_prediction(fighter1_id, fighter2_id)
    except Exception as e:
        print(f"Error generating AI prediction: {e}")
        ai_prediction = {'success': False, 'error': str(e)}

    return render_template('fight_preview.html',
                         fighter1=fighter1,
                         fighter2=fighter2,
                         comparison_stats=comparison_stats,
                         recent_fights=recent_fights,
                         performance_trends=performance_trends,
                         prop_data=prop_data,
                         ai_prediction=ai_prediction,
                         odds_data=odds_data)

@bp.route('/fight-predictor')
def fight_predictor():
    """AI-powered fight prediction page"""
    db_session = db.session
    
    # Get all UFC fighters for dropdown selection
    fighters = db_session.execute(text("""
        SELECT id, full_name, weight_class, headshot_url
        FROM athletes
        WHERE default_league LIKE 'ufc%'
        AND full_name IS NOT NULL
        ORDER BY full_name
    """)).fetchall()
    fighters = [row_to_dict(row) for row in fighters]
    
    return render_template('fight_predictor.html', fighters=fighters)

@bp.route('/fight-predictor/analyze', methods=['POST'])
def analyze_fight_prediction():
    """Analyze fight data and construct prompt for AI prediction"""
    data = request.get_json()
    fighter1_id = data.get('fighter1_id')
    fighter2_id = data.get('fighter2_id')
    
    if not fighter1_id or not fighter2_id:
        return jsonify({"error": "Both fighters must be selected"}), 400
    
    if fighter1_id == fighter2_id:
        return jsonify({"error": "Please select two different fighters"}), 400
    
    db_session = db.session
    
    # Get comprehensive fighter data
    fighter_data = get_comprehensive_fighter_data(db_session, fighter1_id, fighter2_id)
    
    if not fighter_data['fighter1'] or not fighter_data['fighter2']:
        return jsonify({"error": "Fighter data not found"}), 404
    
    # Construct the AI prompt
    prompt_data = construct_fight_prediction_prompt(fighter_data)
    
    return jsonify({
        "success": True,
        "fighter1": fighter_data['fighter1'],
        "fighter2": fighter_data['fighter2'],
        "prompt_data": prompt_data,
        "system_prompt": prompt_data['system_prompt'],
        "user_prompt": prompt_data['user_prompt'],
        "data_summary": prompt_data['data_summary']
    })

def get_comprehensive_fighter_data(db_session, fighter1_id, fighter2_id):
    """Get all relevant fighter data for prediction analysis"""
    
    # Basic fighter info
    fighters_info = db_session.execute(text("""
        SELECT id, full_name, nickname, headshot_url, weight_class, height, weight, reach, 
               age, stance, association, flag_url
        FROM athletes
        WHERE id IN (:fighter1_id, :fighter2_id)
    """), {"fighter1_id": fighter1_id, "fighter2_id": fighter2_id}).fetchall()
    
    fighters_dict = {str(f.id): row_to_dict(f) for f in fighters_info}
    
    # Career statistics
    career_stats = db_session.execute(text("""
        WITH fighter_stats AS (
            SELECT 
                fighter_id,
                COUNT(*) as total_fights,
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN won = 0 AND result_type NOT IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result_type IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as draws,
                SUM(CASE WHEN won = 1 AND (result_type LIKE '%KO%' OR result_type LIKE '%TKO%') THEN 1 ELSE 0 END) as ko_wins,
                SUM(CASE WHEN won = 1 AND result_type LIKE '%Submission%' THEN 1 ELSE 0 END) as sub_wins,
                SUM(CASE WHEN won = 1 AND result_type LIKE '%Decision%' THEN 1 ELSE 0 END) as dec_wins,
                SUM(CASE WHEN won = 0 AND (result_type LIKE '%KO%' OR result_type LIKE '%TKO%') THEN 1 ELSE 0 END) as ko_losses,
                SUM(CASE WHEN won = 0 AND result_type LIKE '%Submission%' THEN 1 ELSE 0 END) as sub_losses
            FROM (
                SELECT 
                    fighter_1_id as fighter_id,
                    fighter_1_winner as won,
                    result_display_name as result_type
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                WHERE LOWER(c.league) = 'ufc'
                UNION ALL
                SELECT 
                    fighter_2_id as fighter_id,
                    fighter_2_winner as won,
                    result_display_name as result_type
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                WHERE LOWER(c.league) = 'ufc'
            ) combined
            WHERE fighter_id IN (:fighter1_id, :fighter2_id)
            GROUP BY fighter_id
        )
        SELECT * FROM fighter_stats
    """), {"fighter1_id": fighter1_id, "fighter2_id": fighter2_id}).fetchall()
    
    # Recent form (last 5 fights)
    recent_form = {}
    for fighter_id in [fighter1_id, fighter2_id]:
        recent_fights = db_session.execute(text("""
            SELECT 
                CASE WHEN f.fighter_1_id = :fighter_id THEN f.fighter_1_winner ELSE f.fighter_2_winner END as won,
                f.result_display_name,
                c.date,
                c.event_name,
                CASE WHEN f.fighter_1_id = :fighter_id THEN a2.full_name ELSE a1.full_name END as opponent
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            LEFT JOIN athletes a1 ON f.fighter_1_id = a1.id
            LEFT JOIN athletes a2 ON f.fighter_2_id = a2.id
            WHERE (f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id)
            AND LOWER(c.league) = 'ufc'
            AND (f.fighter_1_winner IS NOT NULL OR f.fighter_2_winner IS NOT NULL)
            ORDER BY c.date DESC
            LIMIT 5
        """), {"fighter_id": fighter_id}).fetchall()
        
        recent_form[fighter_id] = [row_to_dict(fight) for fight in recent_fights]
    
    # Common opponents analysis
    common_opponents = db_session.execute(text("""
        WITH fighter1_opponents AS (
            SELECT CASE WHEN f.fighter_1_id = :fighter1_id THEN f.fighter_2_id ELSE f.fighter_1_id END as opponent_id,
                   CASE WHEN f.fighter_1_id = :fighter1_id THEN f.fighter_1_winner ELSE f.fighter_2_winner END as f1_won
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            WHERE (f.fighter_1_id = :fighter1_id OR f.fighter_2_id = :fighter1_id)
            AND LOWER(c.league) = 'ufc'
        ),
        fighter2_opponents AS (
            SELECT CASE WHEN f.fighter_1_id = :fighter2_id THEN f.fighter_2_id ELSE f.fighter_1_id END as opponent_id,
                   CASE WHEN f.fighter_1_id = :fighter2_id THEN f.fighter_1_winner ELSE f.fighter_2_winner END as f2_won
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            WHERE (f.fighter_1_id = :fighter2_id OR f.fighter_2_id = :fighter2_id)
            AND LOWER(c.league) = 'ufc'
        )
        SELECT a.full_name as opponent_name, f1.f1_won, f2.f2_won
        FROM fighter1_opponents f1
        JOIN fighter2_opponents f2 ON f1.opponent_id = f2.opponent_id
        JOIN athletes a ON f1.opponent_id = a.id
    """), {"fighter1_id": fighter1_id, "fighter2_id": fighter2_id}).fetchall()
    
    # Merge all data
    fighter1_data = fighters_dict.get(fighter1_id, {})
    fighter2_data = fighters_dict.get(fighter2_id, {})
    
    # Add career stats
    for stats in career_stats:
        stats_dict = row_to_dict(stats)
        if str(stats.fighter_id) == fighter1_id:
            fighter1_data.update(stats_dict)
        elif str(stats.fighter_id) == fighter2_id:
            fighter2_data.update(stats_dict)
    
    return {
        'fighter1': fighter1_data,
        'fighter2': fighter2_data,
        'recent_form': recent_form,
        'common_opponents': [row_to_dict(opp) for opp in common_opponents]
    }

def construct_fight_prediction_prompt(fighter_data):
    """Construct comprehensive prompt for AI fight prediction"""
    f1 = fighter_data['fighter1']
    f2 = fighter_data['fighter2']
    
    # System prompt
    system_prompt = """You are an expert MMA analyst with deep knowledge of fighting styles, statistics, and matchup dynamics. 
    You will analyze two fighters and provide a detailed prediction including win probability, most likely finish method, 
    key factors, and round prediction. Be analytical and consider all provided data points."""
    
    # Construct detailed user prompt
    user_prompt_parts = []
    
    # Fighter introductions
    user_prompt_parts.append("FIGHT ANALYSIS REQUEST")
    user_prompt_parts.append("=" * 50)
    user_prompt_parts.append(f"Fighter 1: {f1.get('full_name', 'Unknown')} {f'({f1.get('nickname', '')})' if f1.get('nickname') else ''}")
    user_prompt_parts.append(f"Fighter 2: {f2.get('full_name', 'Unknown')} {f'({f2.get('nickname', '')})' if f2.get('nickname') else ''}")
    user_prompt_parts.append("")
    
    # Physical attributes
    user_prompt_parts.append("PHYSICAL ATTRIBUTES:")
    user_prompt_parts.append("-" * 30)
    user_prompt_parts.append(f"{f1.get('full_name', 'Fighter 1')}: Age {f1.get('age', 'N/A')}, Height {f1.get('height', 'N/A')}, Reach {f1.get('reach', 'N/A')}, Stance: {f1.get('stance', 'N/A')}")
    user_prompt_parts.append(f"{f2.get('full_name', 'Fighter 2')}: Age {f2.get('age', 'N/A')}, Height {f2.get('height', 'N/A')}, Reach {f2.get('reach', 'N/A')}, Stance: {f2.get('stance', 'N/A')}")
    user_prompt_parts.append("")
    
    # Career records
    user_prompt_parts.append("CAREER RECORDS:")
    user_prompt_parts.append("-" * 30)
    f1_record = f"{f1.get('wins', 0)}-{f1.get('losses', 0)}-{f1.get('draws', 0)}"
    f2_record = f"{f2.get('wins', 0)}-{f2.get('losses', 0)}-{f2.get('draws', 0)}"
    user_prompt_parts.append(f"{f1.get('full_name', 'Fighter 1')}: {f1_record} ({f1.get('total_fights', 0)} total fights)")
    user_prompt_parts.append(f"{f2.get('full_name', 'Fighter 2')}: {f2_record} ({f2.get('total_fights', 0)} total fights)")
    user_prompt_parts.append("")
    
    # Finish statistics
    user_prompt_parts.append("FINISH STATISTICS:")
    user_prompt_parts.append("-" * 30)
    user_prompt_parts.append(f"{f1.get('full_name', 'Fighter 1')}: {f1.get('ko_wins', 0)} KO/TKO wins, {f1.get('sub_wins', 0)} submission wins, {f1.get('dec_wins', 0)} decision wins")
    user_prompt_parts.append(f"{f2.get('full_name', 'Fighter 2')}: {f2.get('ko_wins', 0)} KO/TKO wins, {f2.get('sub_wins', 0)} submission wins, {f2.get('dec_wins', 0)} decision wins")
    user_prompt_parts.append("")
    
    # Recent form
    user_prompt_parts.append("RECENT FORM (Last 5 Fights):")
    user_prompt_parts.append("-" * 30)
    
    for fighter_id, fighter_name in [(f1.get('id'), f1.get('full_name')), (f2.get('id'), f2.get('full_name'))]:
        if str(fighter_id) in fighter_data['recent_form']:
            recent_fights = fighter_data['recent_form'][str(fighter_id)]
            user_prompt_parts.append(f"{fighter_name}:")
            for i, fight in enumerate(recent_fights, 1):
                result = "Won" if fight.get('won') else "Lost"
                method = fight.get('result_display_name', 'N/A')
                opponent = fight.get('opponent', 'N/A')
                user_prompt_parts.append(f"  {i}. {result} vs {opponent} ({method})")
            user_prompt_parts.append("")
    
    # Common opponents
    if fighter_data['common_opponents']:
        user_prompt_parts.append("COMMON OPPONENTS:")
        user_prompt_parts.append("-" * 30)
        for opp in fighter_data['common_opponents']:
            f1_result = "Won" if opp['f1_won'] else "Lost"
            f2_result = "Won" if opp['f2_won'] else "Lost"
            user_prompt_parts.append(f"vs {opp['opponent_name']}: {f1.get('full_name')} {f1_result}, {f2.get('full_name')} {f2_result}")
        user_prompt_parts.append("")
    
    # Analysis request
    user_prompt_parts.append("ANALYSIS REQUEST:")
    user_prompt_parts.append("-" * 30)
    user_prompt_parts.append("Please provide a comprehensive fight prediction including:")
    user_prompt_parts.append("1. Win probability for each fighter (as percentages)")
    user_prompt_parts.append("2. Most likely finish method (KO/TKO, Submission, Decision)")
    user_prompt_parts.append("3. Predicted round (if not going to decision)")
    user_prompt_parts.append("4. Key factors that will determine the fight")
    user_prompt_parts.append("5. Each fighter's path to victory")
    user_prompt_parts.append("6. X-factors or wild cards to consider")
    user_prompt_parts.append("")
    user_prompt_parts.append("Format your response as a detailed analysis with clear sections.")
    
    user_prompt = "\n".join(user_prompt_parts)
    
    # Data summary for display
    data_summary = {
        'fighter1_record': f1_record,
        'fighter2_record': f2_record,
        'fighter1_finishes': f1.get('ko_wins', 0) + f1.get('sub_wins', 0),
        'fighter2_finishes': f2.get('ko_wins', 0) + f2.get('sub_wins', 0),
        'common_opponents_count': len(fighter_data['common_opponents']),
        'data_points_analyzed': len([x for x in [
            f1.get('age'), f1.get('height'), f1.get('reach'), f1.get('total_fights'),
            f2.get('age'), f2.get('height'), f2.get('reach'), f2.get('total_fights')
        ] if x is not None])
    }
    
    return {
        'system_prompt': system_prompt,
        'user_prompt': user_prompt,
        'data_summary': data_summary,
        'prompt_length': len(user_prompt),
        'estimated_tokens': len(user_prompt.split())
    }

def calculate_fight_comparison(fighter1, fighter2):
    """Calculate statistical comparisons between two fighters"""
    comparisons = {}
    
    # Win percentage
    f1_win_pct = (fighter1.get('wins', 0) / max(fighter1.get('total_fights', 1), 1)) * 100
    f2_win_pct = (fighter2.get('wins', 0) / max(fighter2.get('total_fights', 1), 1)) * 100
    comparisons['win_percentage'] = {'fighter1': f1_win_pct, 'fighter2': f2_win_pct}
    
    # Finish rates
    f1_finish_rate = ((fighter1.get('ko_wins', 0) + fighter1.get('sub_wins', 0)) / max(fighter1.get('wins', 1), 1)) * 100
    f2_finish_rate = ((fighter2.get('ko_wins', 0) + fighter2.get('sub_wins', 0)) / max(fighter2.get('wins', 1), 1)) * 100
    comparisons['finish_rate'] = {'fighter1': f1_finish_rate, 'fighter2': f2_finish_rate}
    
    # Physical advantages
    comparisons['reach_advantage'] = {
        'fighter1': fighter1.get('reach', 0) or 0,
        'fighter2': fighter2.get('reach', 0) or 0
    }
    
    comparisons['height_advantage'] = {
        'fighter1': fighter1.get('height', 0) or 0,
        'fighter2': fighter2.get('height', 0) or 0
    }
    
    # Experience
    comparisons['experience'] = {
        'fighter1': fighter1.get('total_fights', 0),
        'fighter2': fighter2.get('total_fights', 0)
    }
    
    return comparisons 