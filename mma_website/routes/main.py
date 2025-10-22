from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from mma_website import db, cache
from mma_website.utils.text_utils import row_to_dict
from mma_website.utils.helpers import format_date

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
    
    # Get upcoming UFC events
    upcoming_events = db_session.execute(text("""
        SELECT event_id, event_name, date, venue_name, city, country
        FROM cards
        WHERE league = 'ufc'
        AND date > date('now')
        ORDER BY date ASC
        LIMIT 5
    """)).fetchall()
    
    # Format dates for upcoming events
    upcoming_events = [row_to_dict(row) for row in upcoming_events]
    for event in upcoming_events:
        event['date'] = format_date(event['date'])
    
    # Get top fighters
    top_fighters = db_session.execute(text("""
        SELECT a.full_name, a.weight_class, COUNT(*) as fight_count
        FROM athletes a
        JOIN fights f ON a.id IN (f.fighter_1_id, f.fighter_2_id)
        WHERE a.default_league = 'ufc'
        GROUP BY a.id
        ORDER BY fight_count DESC
        LIMIT 5
    """)).fetchall()
    
    # Convert top fighters to dictionaries and add headshots
    top_fighters_with_photos = []
    for fighter in top_fighters:
        fighter_dict = row_to_dict(fighter)
        # Get fighter photo from athletes table
        fighter_details = db_session.execute(text("""
            SELECT headshot_url, id
            FROM athletes
            WHERE full_name = :name
            AND default_league = 'ufc'
            LIMIT 1
        """), {"name": fighter_dict['full_name']}).fetchone()
        if fighter_details:
            fighter_dict['headshot_url'] = fighter_details.headshot_url
            fighter_dict['id'] = fighter_details.id
        top_fighters_with_photos.append(fighter_dict)

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

    # Get current UFC rankings with deduplication prioritizing fighters with photos and recent activity
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
                CASE
                    WHEN r.is_champion = 1 THEN 'C'
                    WHEN r.is_interim_champion = 1 THEN 'IC'
                    ELSE CAST(r.rank AS TEXT)
                END as position,
                -- Priority scoring: headshot_url + recent activity
                CASE
                    WHEN a.headshot_url IS NOT NULL AND a.headshot_url != '' THEN 2
                    ELSE 0
                END +
                CASE
                    WHEN a.id IS NOT NULL THEN 1
                    ELSE 0
                END as priority_score,
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
        )
        SELECT
            division, full_name, rank, is_champion, is_interim_champion,
            ranking_type, headshot_url, athlete_id, position
        FROM ranked_athletes
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
            END,
            CASE
                WHEN is_champion = 1 THEN 0
                WHEN is_interim_champion = 1 THEN 0.5
                ELSE rank
            END
    """)).fetchall()

    rankings_data = [row_to_dict(row) for row in rankings]

    # Group by division
    divisions = {}
    for fighter in rankings_data:
        division = fighter['division']
        if division not in divisions:
            divisions[division] = []
        divisions[division].append(fighter)

    return render_template('rankings.html', divisions=divisions)

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
@cache.cached(timeout=900, query_string=True)  # Cache for 15 minutes, vary by query string
def system_checker():
    """MMA Analytics and Pattern Recognition System"""
    db_session = db.session

    # Get filter parameters
    date_range = request.args.get('date_range', 'all')
    weight_class = request.args.get('weight_class', 'all')
    card_position = request.args.get('card_position', 'all')
    
    # Build filter conditions
    filter_conditions = ["LOWER(c.league) = 'ufc'"]
    filter_params = {}
    
    # Date range filter
    if date_range != 'all':
        if date_range in ['2021', '2022', '2023', '2024']:
            filter_conditions.append("strftime('%Y', c.date) = :year")
            filter_params['year'] = date_range
        elif date_range == 'last_2_years':
            filter_conditions.append("c.date >= date('now', '-2 years')")
    
    # Weight class filter
    if weight_class != 'all':
        weight_class_mapping = {
            # Men's Weight Classes
            'heavyweight': 'Heavyweight',
            'light_heavyweight': 'Light Heavyweight', 
            'middleweight': 'Middleweight',
            'welterweight': 'Welterweight',
            'lightweight': 'Lightweight',
            'featherweight': 'Featherweight',
            'bantamweight': 'Bantamweight',
            'flyweight': 'Flyweight',
            # Women's Weight Classes
            'womens_featherweight': "Women's Featherweight",
            'womens_bantamweight': "Women's Bantamweight",
            'womens_flyweight': "Women's Flyweight",
            'womens_strawweight': "Women's Strawweight",
            'womens_atomweight': "Women's Atomweight"
        }
        if weight_class in weight_class_mapping:
            filter_conditions.append("f.weight_class LIKE :weight_class")
            filter_params['weight_class'] = f"%{weight_class_mapping[weight_class]}%"
    
    # Card position filter
    if card_position != 'all':
        position_mapping = {
            'main_card': 'Main Card',
            'preliminary': 'Preliminary Card',
            'early_preliminary': 'Early Preliminary Card'
        }
        if card_position in position_mapping:
            filter_conditions.append("f.card_segment LIKE :card_segment")
            filter_params['card_segment'] = f"%{position_mapping[card_position]}%"
    
    # Combine all filter conditions
    filter_clause = " AND ".join(filter_conditions)
    
    # 1. Fighter Win Streaks Analysis
    fighter_streaks_query = f"""
        WITH fighter_results AS (
            SELECT 
                fighter_1_id as fighter_id, 
                fighter_1_winner as won,
                c.date,
                a.full_name
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            JOIN athletes a ON f.fighter_1_id = a.id
            WHERE f.fighter_1_winner IS NOT NULL
            AND {filter_clause}
            UNION ALL
            SELECT 
                fighter_2_id as fighter_id, 
                fighter_2_winner as won,
                c.date,
                a.full_name
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id  
            JOIN athletes a ON f.fighter_2_id = a.id
            WHERE f.fighter_2_winner IS NOT NULL
            AND {filter_clause}
        ),
        streak_analysis AS (
            SELECT 
                fighter_id,
                full_name,
                COUNT(*) as total_fights,
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as total_wins,
                ROUND(AVG(CASE WHEN won = 1 THEN 100.0 ELSE 0.0 END), 1) as win_percentage
            FROM fighter_results
            GROUP BY fighter_id, full_name
            HAVING COUNT(*) >= 5
        )
        SELECT * FROM streak_analysis 
        ORDER BY win_percentage DESC, total_fights DESC
        LIMIT 10
    """
    fighter_streaks = db_session.execute(text(fighter_streaks_query), filter_params).fetchall()
    
    # 2. Weight Class Finish Rate Analysis  
    weight_class_stats = db_session.execute(text("""
        SELECT 
            f.weight_class,
            COUNT(*) as total_fights,
            SUM(CASE WHEN f.result_display_name LIKE '%KO%' OR f.result_display_name LIKE '%TKO%' 
                     OR f.result_display_name LIKE '%Submission%' THEN 1 ELSE 0 END) as finishes,
            ROUND(
                (SUM(CASE WHEN f.result_display_name LIKE '%KO%' OR f.result_display_name LIKE '%TKO%' 
                          OR f.result_display_name LIKE '%Submission%' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 100, 1
            ) as finish_rate,
            SUM(CASE WHEN f.result_display_name LIKE '%KO%' OR f.result_display_name LIKE '%TKO%' THEN 1 ELSE 0 END) as ko_tko,
            SUM(CASE WHEN f.result_display_name LIKE '%Submission%' THEN 1 ELSE 0 END) as submissions
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        WHERE f.weight_class IS NOT NULL 
        AND f.weight_class != ''
        AND LOWER(c.league) = 'ufc'
        GROUP BY f.weight_class
        HAVING COUNT(*) >= 20
        ORDER BY finish_rate DESC
    """)).fetchall()
    
    # 3. Enhanced Betting Favorites Performance Analysis
    betting_favorites = db_session.execute(text("""
        SELECT 
            COUNT(*) as total_fights_with_odds,
            SUM(CASE WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1 THEN 1
                     WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1 THEN 1
                     ELSE 0 END) as favorite_wins,
            ROUND(
                (SUM(CASE WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1 THEN 1.0
                          WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1 THEN 1.0
                          ELSE 0.0 END) / COUNT(*)) * 100, 1
            ) as favorite_win_rate,
            -- Favorite finish rate
            ROUND(
                (SUM(CASE 
                    WHEN (o.home_favorite = 1 AND f.fighter_1_winner = 1) OR (o.away_favorite = 1 AND f.fighter_2_winner = 1) THEN
                        CASE WHEN f.result_display_name LIKE '%KO%' OR f.result_display_name LIKE '%TKO%' 
                                  OR f.result_display_name LIKE '%Submission%' THEN 1.0 ELSE 0.0 END
                    ELSE 0.0
                END) / NULLIF(SUM(CASE WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1 THEN 1
                                       WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1 THEN 1
                                       ELSE 0 END), 0)) * 100, 1
            ) as favorite_finish_rate,
            -- Underdog performance
            COUNT(*) - SUM(CASE WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1 THEN 1
                               WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1 THEN 1
                               ELSE 0 END) as underdog_wins,
            ROUND(
                ((COUNT(*) - SUM(CASE WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1 THEN 1
                                     WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1 THEN 1
                                     ELSE 0 END)) / COUNT(*)) * 100, 1
            ) as underdog_win_rate
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        JOIN odds o ON f.fight_id = o.fight_id
        WHERE (o.home_favorite = 1 OR o.away_favorite = 1)
        AND LOWER(c.league) = 'ufc'
        AND f.fighter_1_winner IS NOT NULL
    """)).fetchone()
    
    # 4. Betting Odds Range Analysis
    odds_range_analysis = db_session.execute(text("""
        WITH favorite_odds AS (
            SELECT 
                f.fight_id,
                f.result_display_name,
                CASE 
                    WHEN o.home_favorite = 1 THEN o.home_moneyLine_odds_current_american
                    WHEN o.away_favorite = 1 THEN o.away_moneyLine_odds_current_american
                END as favorite_odds,
                CASE 
                    WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1 THEN 1
                    WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1 THEN 1
                    ELSE 0
                END as favorite_won
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            JOIN odds o ON f.fight_id = o.fight_id
            WHERE (o.home_favorite = 1 OR o.away_favorite = 1)
            AND LOWER(c.league) = 'ufc'
            AND f.fighter_1_winner IS NOT NULL
            AND o.home_moneyLine_odds_current_american IS NOT NULL
            AND o.away_moneyLine_odds_current_american IS NOT NULL
        )
        SELECT 
            CASE 
                WHEN favorite_odds >= -150 THEN 'Heavy Favorite (-150 or better)'
                WHEN favorite_odds >= -300 THEN 'Moderate Favorite (-151 to -300)'
                WHEN favorite_odds >= -500 THEN 'Strong Favorite (-301 to -500)'
                ELSE 'Overwhelming Favorite (-501 or worse)'
            END as odds_range,
            COUNT(*) as total_fights,
            SUM(favorite_won) as favorite_wins,
            ROUND(AVG(favorite_won) * 100, 1) as favorite_win_percentage,
            ROUND(AVG(CASE 
                WHEN favorite_won = 1 AND (result_display_name LIKE '%KO%' OR result_display_name LIKE '%TKO%' 
                                          OR result_display_name LIKE '%Submission%') THEN 1.0
                ELSE 0.0
            END) * 100, 1) as favorite_finish_rate_in_wins
        FROM favorite_odds
        WHERE favorite_odds IS NOT NULL
        GROUP BY 
            CASE 
                WHEN favorite_odds >= -150 THEN 'Heavy Favorite (-150 or better)'
                WHEN favorite_odds >= -300 THEN 'Moderate Favorite (-151 to -300)'
                WHEN favorite_odds >= -500 THEN 'Strong Favorite (-301 to -500)'
                ELSE 'Overwhelming Favorite (-501 or worse)'
            END
        HAVING COUNT(*) >= 10
        ORDER BY 
            CASE 
                WHEN odds_range LIKE 'Heavy%' THEN 1
                WHEN odds_range LIKE 'Moderate%' THEN 2
                WHEN odds_range LIKE 'Strong%' THEN 3
                ELSE 4
            END
    """)).fetchall()
    
    # 5. Enhanced Age vs Performance Analysis
    age_analysis = db_session.execute(text("""
        WITH age_performance AS (
            SELECT 
                CASE 
                    WHEN ABS(COALESCE(a1.age, 30) - COALESCE(a2.age, 30)) >= 8 THEN '8+ Years'
                    WHEN ABS(COALESCE(a1.age, 30) - COALESCE(a2.age, 30)) >= 5 THEN '5-7 Years'
                    WHEN ABS(COALESCE(a1.age, 30) - COALESCE(a2.age, 30)) >= 3 THEN '3-4 Years'
                    ELSE '0-2 Years'
                END as age_gap,
                COUNT(*) as total_fights,
                -- Younger fighter win rate
                ROUND(AVG(CASE 
                    WHEN a1.age > a2.age AND f.fighter_1_winner = 1 THEN 0
                    WHEN a1.age > a2.age AND f.fighter_2_winner = 1 THEN 1  
                    WHEN a2.age > a1.age AND f.fighter_1_winner = 1 THEN 1
                    WHEN a2.age > a1.age AND f.fighter_2_winner = 1 THEN 0
                    ELSE 0.5
                END) * 100, 1) as younger_fighter_win_rate,
                -- Average age of winners vs losers
                ROUND(AVG(CASE 
                    WHEN f.fighter_1_winner = 1 THEN a1.age
                    WHEN f.fighter_2_winner = 1 THEN a2.age
                END), 1) as avg_winner_age,
                ROUND(AVG(CASE 
                    WHEN f.fighter_1_winner = 0 THEN a1.age
                    WHEN f.fighter_2_winner = 0 THEN a2.age
                END), 1) as avg_loser_age,
                -- Finish rate by age gap
                ROUND(AVG(CASE 
                    WHEN f.result_display_name LIKE '%KO%' OR f.result_display_name LIKE '%TKO%' 
                         OR f.result_display_name LIKE '%Submission%' THEN 1.0
                    ELSE 0.0
                END) * 100, 1) as finish_rate
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            LEFT JOIN athletes a1 ON f.fighter_1_id = a1.id
            LEFT JOIN athletes a2 ON f.fighter_2_id = a2.id
            WHERE a1.age IS NOT NULL AND a2.age IS NOT NULL
            AND a1.age BETWEEN 18 AND 50 AND a2.age BETWEEN 18 AND 50
            AND LOWER(c.league) = 'ufc'
            AND f.fighter_1_winner IS NOT NULL
            GROUP BY age_gap
        )
        SELECT * FROM age_performance
        ORDER BY 
            CASE age_gap 
                WHEN '0-2 Years' THEN 1 
                WHEN '3-4 Years' THEN 2 
                WHEN '5-7 Years' THEN 3 
                WHEN '8+ Years' THEN 4 
            END
    """)).fetchall()
    
    # 6. Prime Age Performance Analysis  
    prime_age_analysis = db_session.execute(text("""
        SELECT 
            CASE 
                WHEN age BETWEEN 18 AND 25 THEN 'Young (18-25)'
                WHEN age BETWEEN 26 AND 30 THEN 'Prime (26-30)'
                WHEN age BETWEEN 31 AND 35 THEN 'Veteran (31-35)'
                WHEN age > 35 THEN 'Elder (35+)'
                ELSE 'Unknown'
            END as age_group,
            COUNT(*) as total_fights,
            ROUND(AVG(CASE WHEN won = 1 THEN 100.0 ELSE 0.0 END), 1) as win_percentage,
            ROUND(AVG(CASE 
                WHEN won = 1 AND result_type LIKE '%KO%' OR result_type LIKE '%TKO%' THEN 1.0
                ELSE 0.0
            END) * 100, 1) as ko_rate,
            ROUND(AVG(CASE 
                WHEN won = 1 AND result_type LIKE '%Submission%' THEN 1.0
                ELSE 0.0
            END) * 100, 1) as sub_rate
        FROM (
            SELECT 
                a1.age as age,
                f.fighter_1_winner as won,
                f.result_display_name as result_type
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            LEFT JOIN athletes a1 ON f.fighter_1_id = a1.id
            WHERE a1.age IS NOT NULL
            AND a1.age BETWEEN 18 AND 50
            AND LOWER(c.league) = 'ufc'
            AND f.fighter_1_winner IS NOT NULL
            UNION ALL
            SELECT 
                a2.age as age,
                f.fighter_2_winner as won,
                f.result_display_name as result_type
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            LEFT JOIN athletes a2 ON f.fighter_2_id = a2.id
            WHERE a2.age IS NOT NULL
            AND a2.age BETWEEN 18 AND 50
            AND LOWER(c.league) = 'ufc'
            AND f.fighter_2_winner IS NOT NULL
        ) age_results
        GROUP BY age_group
        HAVING COUNT(*) >= 50
        ORDER BY 
            CASE age_group 
                WHEN 'Young (18-25)' THEN 1
                WHEN 'Prime (26-30)' THEN 2
                WHEN 'Veteran (31-35)' THEN 3
                WHEN 'Elder (35+)' THEN 4
            END
    """)).fetchall()
    
    # 7. Round Finish Analysis
    round_analysis = db_session.execute(text("""
        SELECT 
            COALESCE(f.end_round, 'Decision') as finish_round,
            COUNT(*) as fights,
            ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fights f2 
                                       JOIN cards c2 ON f2.event_id = c2.event_id 
                                       WHERE LOWER(c2.league) = 'ufc')), 1) as percentage
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        WHERE LOWER(c.league) = 'ufc'
        GROUP BY f.end_round
        ORDER BY 
            CASE 
                WHEN f.end_round = 1 THEN 1
                WHEN f.end_round = 2 THEN 2  
                WHEN f.end_round = 3 THEN 3
                WHEN f.end_round = 4 THEN 4
                WHEN f.end_round = 5 THEN 5
                ELSE 6
            END
    """)).fetchall()
    
    return render_template('system_checker.html',
                         fighter_streaks=fighter_streaks,
                         weight_class_stats=weight_class_stats,
                         betting_favorites=betting_favorites,
                         odds_range_analysis=odds_range_analysis,
                         age_analysis=age_analysis,
                         prime_age_analysis=prime_age_analysis,
                         round_analysis=round_analysis)