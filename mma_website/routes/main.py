from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from mma_website import db, cache
from mma_website.utils.text_utils import row_to_dict
from mma_website.utils.helpers import format_date
import httpx
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.route('/')
@cache.cached(timeout=600)  # Cache for 10 minutes
def home():
    """Home page with recent events and top fighters"""
    db_session = db.session
    
    # Get recent UFC events
    recent_events = db_session.execute(text("""
        SELECT event_id, event_name, date, venue_name, city, country
        FROM cards
        WHERE league = 'ufc'
        ORDER BY date DESC
        LIMIT 5
    """)).fetchall()
    
    # Format dates for recent events
    recent_events = [row_to_dict(row) for row in recent_events]
    for event in recent_events:
        event['date'] = format_date(event['date'])
    
    # Get upcoming UFC events from ESPN API
    upcoming_events = []
    try:
        ufc_events_url = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/events/?lang=en&region=us"
        response = httpx.get(ufc_events_url, timeout=5.0)
        response.raise_for_status()
        events_data = response.json()

        # Get up to 3 upcoming events
        for item in events_data.get('items', [])[:3]:
            event_url = item.get('$ref')
            if event_url:
                try:
                    event_response = httpx.get(event_url, timeout=5.0)
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
                                'event_id': event_data.get('id'),
                                'event_name': event_data.get('name'),
                                'date': event_date.strftime('%m-%d-%Y'),
                                'venue_name': venue.get('fullName', 'TBD'),
                                'city': address.get('city', 'TBD'),
                                'country': address.get('country', 'TBD')
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
        upcoming_events = db_session.execute(text("""
            SELECT event_id, event_name, date, venue_name, city, country
            FROM cards
            WHERE league = 'ufc'
            AND date > date('now')
            ORDER BY date ASC
            LIMIT 3
        """)).fetchall()
        upcoming_events = [row_to_dict(row) for row in upcoming_events]
        for event in upcoming_events:
            event['date'] = format_date(event['date'])
    
    # Get featured fighters - top ranked fighters from different divisions
    top_fighters_with_photos = []
    try:
        featured_fighters = db_session.execute(text("""
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
        """)).fetchall()

        # Get fight count for each fighter
        for fighter in featured_fighters:
            fighter_dict = row_to_dict(fighter)

            # Get fight count
            fight_count_result = db_session.execute(text("""
                SELECT COUNT(*) as fight_count
                FROM fights f
                WHERE f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id
            """), {"fighter_id": fighter_dict['id']}).fetchone()

            if fight_count_result:
                fighter_dict['fight_count'] = fight_count_result.fight_count
            else:
                fighter_dict['fight_count'] = 0

            top_fighters_with_photos.append(fighter_dict)

    except Exception as e:
        print(f"Error loading featured fighters: {e}")
        # Fallback: Get fighters with most fights
        top_fighters = db_session.execute(text("""
            SELECT a.id, a.full_name, a.weight_class, a.headshot_url, COUNT(*) as fight_count
            FROM athletes a
            JOIN fights f ON a.id IN (f.fighter_1_id, f.fighter_2_id)
            WHERE a.default_league = 'ufc'
            AND a.headshot_url IS NOT NULL
            GROUP BY a.id
            ORDER BY fight_count DESC
            LIMIT 4
        """)).fetchall()
        top_fighters_with_photos = [row_to_dict(fighter) for fighter in top_fighters]

    # Get current UFC champions (from rankings) - handle potential missing table gracefully
    try:
        current_champions = db_session.execute(text("""
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
        """)).fetchall()
    except Exception as e:
        print(f"Error loading champions: {e}")
        current_champions = []

    champions = [row_to_dict(row) for row in current_champions] if current_champions else []

    return render_template('index.html',
                         recent_events=recent_events,
                         upcoming_events=upcoming_events,
                         top_fighters=top_fighters_with_photos,
                         current_champions=champions)

@bp.route('/fighters')
@cache.cached(timeout=1800)  # Cache for 30 minutes
def fighters():
    """Fighters listing page"""
    db_session = db.session

    # Get all UFC fighters
    fighters = db_session.execute(text("""
        SELECT id, full_name
        FROM athletes
        WHERE default_league LIKE 'ufc%'
        ORDER BY full_name
    """)).fetchall()

    fighters = [row_to_dict(row) for row in fighters]

    return render_template('fighters.html', fighters=fighters)

@bp.route('/rankings')
@cache.cached(timeout=3600)  # Cache for 1 hour (rankings don't change often)
def rankings():
    """UFC Rankings page"""
    db_session = db.session

    # Get current UFC rankings with athlete stats and recent fight info
    rankings = db_session.execute(text("""
        WITH ranked_athletes AS (
            SELECT
                r.division,
                r.fighter_name as full_name,
                r.rank,
                r.is_champion,
                r.is_interim_champion,
                r.ranking_type,
                a.headshot_url,
                a.id as athlete_id,
                a.age,
                a.height,
                a.reach,
                a.stance,
                a.flag_url,
                a.date_of_birth,
                a.weight,
                r.last_updated,
                CASE
                    WHEN r.is_champion = 1 THEN 'C'
                    WHEN r.is_interim_champion = 1 THEN 'IC'
                    ELSE CAST(r.rank AS TEXT)
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
            WHERE r.ranking_type = 'Division'
        ),
        last_fights AS (
            SELECT
                CASE
                    WHEN f.fighter_1_id = ra.athlete_id THEN f.fighter_1_id
                    WHEN f.fighter_2_id = ra.athlete_id THEN f.fighter_2_id
                END as fighter_id,
                MAX(c.date) as last_fight_date,
                CASE
                    WHEN f.fighter_1_id = ra.athlete_id AND f.fighter_1_winner = 1 THEN 'W'
                    WHEN f.fighter_2_id = ra.athlete_id AND f.fighter_2_winner = 1 THEN 'W'
                    ELSE 'L'
                END as last_result
            FROM ranked_athletes ra
            JOIN fights f ON (f.fighter_1_id = ra.athlete_id OR f.fighter_2_id = ra.athlete_id)
            JOIN cards c ON f.event_id = c.event_id
            WHERE ra.athlete_id IS NOT NULL
            GROUP BY fighter_id
        ),
        rank_movements AS (
            SELECT
                division,
                fighter_name,
                rank as current_rank,
                LAG(rank) OVER (PARTITION BY division, fighter_name ORDER BY snapshot_date) as previous_rank
            FROM (
                SELECT division, fighter_name, rank, snapshot_date,
                       ROW_NUMBER() OVER (PARTITION BY division, fighter_name ORDER BY snapshot_date DESC) as rn
                FROM ufc_rankings_history
                WHERE rank IS NOT NULL
            ) recent_history
            WHERE rn <= 2
        )
        SELECT
            ra.division, ra.full_name, ra.rank, ra.is_champion, ra.is_interim_champion,
            ra.ranking_type, ra.headshot_url, ra.athlete_id, ra.position, ra.age, ra.height,
            ra.reach, ra.stance, ra.flag_url, ra.date_of_birth, ra.weight, ra.last_updated,
            lf.last_fight_date, lf.last_result,
            rm.previous_rank,
            CASE
                WHEN rm.previous_rank IS NULL THEN 'NEW'
                WHEN ra.rank < rm.previous_rank THEN 'UP'
                WHEN ra.rank > rm.previous_rank THEN 'DOWN'
                ELSE 'SAME'
            END as rank_movement
        FROM ranked_athletes ra
        LEFT JOIN last_fights lf ON ra.athlete_id = lf.fighter_id
        LEFT JOIN rank_movements rm ON ra.division = rm.division AND ra.full_name = rm.fighter_name
        WHERE ra.rn = 1
        ORDER BY
            CASE ra.division
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
            END,
            CASE
                WHEN ra.is_champion = 1 THEN 0
                WHEN ra.is_interim_champion = 1 THEN 0.5
                ELSE ra.rank
            END
    """)).fetchall()

    rankings_data = [row_to_dict(row) for row in rankings]

    # Get last update timestamp
    last_update = None
    if rankings_data:
        last_update = rankings_data[0].get('last_updated')

    # Group by division
    divisions = {}
    for fighter in rankings_data:
        division = fighter['division']
        if division not in divisions:
            divisions[division] = []
        divisions[division].append(fighter)

    return render_template('rankings.html', divisions=divisions, last_updated=last_update)

@bp.route('/career-timeline')
def career_timeline():
    """Career timeline landing page"""
    db_session = db.session
    
    # Get all UFC fighters for search functionality
    fighters = db_session.execute(text("""
        SELECT id, full_name
        FROM athletes
        WHERE default_league LIKE 'ufc%'
        ORDER BY full_name
    """)).fetchall()
    
    fighters = [row_to_dict(row) for row in fighters]
    
    return render_template('career_timeline_landing.html', fighters=fighters)

@bp.route('/system-checker')
def system_checker():
    """Simple, clear betting analytics - card-by-card breakdown (FIXED: one outcome per fight)"""
    from mma_website.utils.text_utils import row_to_dict
    from datetime import datetime
    
    db_session = db.session
    
    # Get selected league (default to UFC)
    selected_league = request.args.get('league', 'ufc').lower()
    
    # Get selected year (default to current year)
    current_year = datetime.now().year
    selected_year = request.args.get('year', str(current_year))
    
    # Validate league
    if selected_league not in ['ufc', 'pfl', 'bellator']:
        selected_league = 'ufc'
    
    # Get basic stats for selected league
    league_stats = db_session.execute(text("""
        SELECT 
            COUNT(DISTINCT f.fight_id) as total_fights,
            COUNT(DISTINCT c.event_id) as total_events,
            COUNT(DISTINCT CASE WHEN o.fight_id IS NOT NULL THEN f.fight_id END) as fights_with_odds
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        LEFT JOIN odds o ON f.fight_id = o.fight_id
        WHERE LOWER(c.league) = :league
        AND f.fighter_1_winner IS NOT NULL
    """), {"league": selected_league}).fetchone()
    
    league_stats_dict = row_to_dict(league_stats) if league_stats else {}
    
    # Get favorite/underdog stats - ONE outcome per fight (use first odds entry per fight)
    favorite_stats = None
    if league_stats_dict.get('fights_with_odds', 0) > 0:
        favorite_result = db_session.execute(text("""
            WITH first_odds AS (
                SELECT 
                    f.fight_id,
                    f.fighter_1_winner,
                    f.fighter_2_winner,
                    MIN(o.provider_id) as first_provider
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                JOIN odds o ON f.fight_id = o.fight_id
                WHERE LOWER(c.league) = :league
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
        """), {"league": selected_league}).fetchone()
        
        if favorite_result:
            favorite_stats = row_to_dict(favorite_result)
            # Calculate percentages
            if favorite_stats['total_fights'] > 0:
                favorite_stats['favorite_win_pct'] = round((favorite_stats['favorite_wins'] / favorite_stats['total_fights']) * 100, 1)
                favorite_stats['underdog_win_pct'] = round((favorite_stats['underdog_wins'] / favorite_stats['total_fights']) * 100, 1)
            else:
                favorite_stats['favorite_win_pct'] = 0
                favorite_stats['underdog_win_pct'] = 0

    # Get weight class breakdown for selected year
    weight_class_results = db_session.execute(text("""
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
            WHERE LOWER(c.league) = :league
            AND strftime('%Y', c.date) = :year
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
    """), {"league": selected_league, "year": selected_year}).fetchall()

    weight_class_data = []
    for row in weight_class_results:
        wc = row_to_dict(row)
        if wc['total_fights'] > 0:
            wc['favorite_win_pct'] = round((wc['favorite_wins'] / wc['total_fights']) * 100, 1)
            wc['underdog_win_pct'] = round((wc['underdog_wins'] / wc['total_fights']) * 100, 1)
        else:
            wc['favorite_win_pct'] = 0
            wc['underdog_win_pct'] = 0
        weight_class_data.append(wc)

    # Get rounds format analysis (3-round vs 5-round)
    rounds_format_results = db_session.execute(text("""
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
            WHERE LOWER(c.league) = :league
            AND strftime('%Y', c.date) = :year
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
    """), {"league": selected_league, "year": selected_year}).fetchall()

    rounds_format_data = []
    for row in rounds_format_results:
        rf = row_to_dict(row)
        if rf['total_fights'] > 0:
            rf['favorite_win_pct'] = round((rf['favorite_wins'] / rf['total_fights']) * 100, 1)
            rf['underdog_win_pct'] = round((rf['underdog_wins'] / rf['total_fights']) * 100, 1)
        else:
            rf['favorite_win_pct'] = 0
            rf['underdog_win_pct'] = 0
        rounds_format_data.append(rf)

    # Get decision rate by weight class (goes the distance)
    decision_rate_results = db_session.execute(text("""
        SELECT
            f.weight_class,
            COUNT(*) as total_fights,
            SUM(CASE WHEN f.result_display_name LIKE '%Decision%' THEN 1 ELSE 0 END) as decisions,
            SUM(CASE WHEN f.result_display_name LIKE '%KO%' OR f.result_display_name LIKE '%TKO%' THEN 1 ELSE 0 END) as knockouts,
            SUM(CASE WHEN f.result_display_name LIKE '%Submission%' THEN 1 ELSE 0 END) as submissions
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        WHERE LOWER(c.league) = :league
        AND strftime('%Y', c.date) = :year
        AND f.fighter_1_winner IS NOT NULL
        AND f.weight_class IS NOT NULL
        AND f.result_display_name IS NOT NULL
        GROUP BY f.weight_class
        HAVING COUNT(*) >= 3
        ORDER BY total_fights DESC
    """), {"league": selected_league, "year": selected_year}).fetchall()

    decision_rate_data = []
    for row in decision_rate_results:
        dr = row_to_dict(row)
        if dr['total_fights'] > 0:
            dr['decision_pct'] = round((dr['decisions'] / dr['total_fights']) * 100, 1)
            dr['knockout_pct'] = round((dr['knockouts'] / dr['total_fights']) * 100, 1)
            dr['submission_pct'] = round((dr['submissions'] / dr['total_fights']) * 100, 1)
            dr['finish_pct'] = round(((dr['knockouts'] + dr['submissions']) / dr['total_fights']) * 100, 1)
        else:
            dr['decision_pct'] = 0
            dr['knockout_pct'] = 0
            dr['submission_pct'] = 0
            dr['finish_pct'] = 0
        decision_rate_data.append(dr)

    # Get card-by-card breakdown - ONE outcome per fight + finish types
    card_results = db_session.execute(text("""
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
            WHERE LOWER(c.league) = :league
            AND strftime('%Y', c.date) = :year
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
    """), {"league": selected_league, "year": selected_year}).fetchall()
    
    cards_data = [row_to_dict(row) for row in card_results]
    
    # Calculate percentages for each card
    for card in cards_data:
        if card['fights_with_odds'] > 0:
            card['favorite_win_pct'] = round((card['favorite_wins'] / card['fights_with_odds']) * 100, 1)
            card['underdog_win_pct'] = round((card['underdog_wins'] / card['fights_with_odds']) * 100, 1)
            card['decision_pct'] = round((card['decisions'] / card['fights_with_odds']) * 100, 1)
            card['knockout_pct'] = round((card['knockouts'] / card['fights_with_odds']) * 100, 1)
            card['submission_pct'] = round((card['submissions'] / card['fights_with_odds']) * 100, 1)
        else:
            card['favorite_win_pct'] = 0
            card['underdog_win_pct'] = 0
            card['decision_pct'] = 0
            card['knockout_pct'] = 0
            card['submission_pct'] = 0
    
    # Get available years for this league
    available_years = db_session.execute(text("""
        SELECT DISTINCT strftime('%Y', c.date) as year
        FROM cards c
        JOIN fights f ON c.event_id = f.event_id
        WHERE LOWER(c.league) = :league
        AND f.fighter_1_winner IS NOT NULL
        AND EXISTS (SELECT 1 FROM odds o WHERE o.fight_id = f.fight_id)
        ORDER BY year DESC
    """), {"league": selected_league}).fetchall()
    
    years_list = [row[0] for row in available_years]
    
    return render_template('system_checker.html',
                         selected_league=selected_league,
                         selected_year=selected_year,
                         years_list=years_list,
                         league_stats=league_stats_dict,
                         favorite_stats=favorite_stats,
                         weight_class_data=weight_class_data,
                         rounds_format_data=rounds_format_data,
                         decision_rate_data=decision_rate_data,
                         cards_data=cards_data)

@bp.route('/card-detail/<int:event_id>')
def card_detail(event_id):
    """Detailed view of a single card showing fight-by-fight results"""
    from mma_website.utils.text_utils import row_to_dict

    db_session = db.session

    # Get navigation parameters
    league = request.args.get('league', 'ufc')
    year = request.args.get('year', '')

    # Get card information
    card_info = db_session.execute(text("""
        SELECT event_id, event_name, date, venue_name, city, country, league
        FROM cards
        WHERE event_id = :event_id
    """), {"event_id": event_id}).fetchone()

    if not card_info:
        return "Card not found", 404

    card = row_to_dict(card_info)

    # Get fight-by-fight results with favorite/underdog outcomes
    fights_results = db_session.execute(text("""
        WITH first_odds AS (
            SELECT
                f.fight_id,
                f.fighter_1_id,
                f.fighter_2_id,
                f.fighter_1_winner,
                f.fighter_2_winner,
                f.weight_class,
                f.result_display_name,
                f.match_number,
                f.card_segment,
                MIN(o.provider_id) as first_provider
            FROM fights f
            JOIN odds o ON f.fight_id = o.fight_id
            WHERE f.event_id = :event_id
            AND f.fighter_1_winner IS NOT NULL
            GROUP BY f.fight_id
        )
        SELECT
            fo.fight_id,
            fo.weight_class,
            fo.result_display_name as result,
            fo.match_number,
            fo.card_segment,
            a1.full_name as fighter_1_name,
            a1.headshot_url as fighter_1_photo,
            a2.full_name as fighter_2_name,
            a2.headshot_url as fighter_2_photo,
            fo.fighter_1_winner,
            fo.fighter_2_winner,
            o.home_moneyLine_odds as home_odds,
            o.away_moneyLine_odds as away_odds,
            o.home_favorite,
            o.away_favorite,
            o.home_underdog,
            o.away_underdog,
            CASE
                WHEN (o.home_favorite = 1 AND fo.fighter_1_winner = 1) OR
                     (o.away_favorite = 1 AND fo.fighter_2_winner = 1) THEN 'favorite'
                WHEN (o.home_underdog = 1 AND fo.fighter_1_winner = 1) OR
                     (o.away_underdog = 1 AND fo.fighter_2_winner = 1) THEN 'underdog'
                ELSE NULL
            END as outcome
        FROM first_odds fo
        JOIN odds o ON fo.fight_id = o.fight_id AND fo.first_provider = o.provider_id
        LEFT JOIN athletes a1 ON fo.fighter_1_id = a1.id
        LEFT JOIN athletes a2 ON fo.fighter_2_id = a2.id
        ORDER BY fo.match_number ASC
    """), {"event_id": event_id}).fetchall()

    fights = [row_to_dict(row) for row in fights_results]

    # Calculate card summary stats
    total_fights = len(fights)
    favorite_wins = sum(1 for f in fights if f.get('outcome') == 'favorite')
    underdog_wins = sum(1 for f in fights if f.get('outcome') == 'underdog')

    if total_fights > 0:
        favorite_win_pct = round((favorite_wins / total_fights) * 100, 1)
        underdog_win_pct = round((underdog_wins / total_fights) * 100, 1)
    else:
        favorite_win_pct = 0
        underdog_win_pct = 0

    card_stats = {
        'total_fights': total_fights,
        'favorite_wins': favorite_wins,
        'underdog_wins': underdog_wins,
        'favorite_win_pct': favorite_win_pct,
        'underdog_win_pct': underdog_win_pct
    }

    return render_template('card_detail.html',
                         card=card,
                         fights=fights,
                         card_stats=card_stats,
                         league=league,
                         year=year)