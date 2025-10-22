from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from sqlalchemy import create_engine, text, func, desc
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
import httpx
from utils.helpers import process_next_event, get_odds_data
import secrets
import random
import unicodedata
import json
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
from collections import defaultdict

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a random secret key

# Get the absolute path to the database file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'mma.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database configuration
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def format_date(date_str):
    try:
        # Split on space to remove time component
        date_part = date_str.split()[0]
        date_obj = datetime.strptime(date_part, '%Y-%m-%d')
        return date_obj.strftime('%m-%d-%Y')
    except:
        return date_str

# Add format_date filter to Jinja2 environment
app.jinja_env.filters['format_date'] = format_date

def row_to_dict(row):
    return {key: value for key, value in row._mapping.items()}

def normalize_ascii(text):
    if text is None:
        return ""
    
    # First normalize using unicodedata
    text = unicodedata.normalize('NFKD', text)
    
    # Custom character mappings for common non-ASCII characters
    char_map = {
        'ł': 'l', 'Ł': 'L',  # Polish ł
        'ć': 'c', 'Ć': 'C',  # Polish ć
        'ś': 's', 'Ś': 'S',  # Polish ś
        'ź': 'z', 'Ź': 'Z',  # Polish ź
        'ż': 'z', 'Ż': 'Z',  # Polish ż
        'ą': 'a', 'Ą': 'A',  # Polish ą
        'ę': 'e', 'Ę': 'E',  # Polish ę
        'ó': 'o', 'Ó': 'O',  # Polish ó
        'ń': 'n', 'Ń': 'N',  # Polish ń
        'č': 'c', 'Č': 'C',  # Czech č
        'ć': 'c', 'Ć': 'C',  # Serbian ć
        'đ': 'd', 'Đ': 'D',  # Serbian đ
        'š': 's', 'Š': 'S',  # Serbian š
        'ž': 'z', 'Ž': 'Z',  # Serbian ž
    }
    
    # Replace special characters
    for special, ascii_char in char_map.items():
        text = text.replace(special, ascii_char)
    
    # Convert to ASCII and lowercase
    return text.encode('ascii', 'ignore').decode('ascii').lower()

@app.route('/')
def home():
    db = get_db()
    
    # Get recent UFC events
    recent_events = db.execute(text("""
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
    upcoming_events = db.execute(text("""
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
    top_fighters = db.execute(text("""
        SELECT a.full_name, a.weight_class, COUNT(*) as fight_count
        FROM athletes a
        JOIN fights f ON a.id IN (f.fighter_1_id, f.fighter_2_id)
        WHERE a.default_league = 'ufc'
        GROUP BY a.id
        ORDER BY fight_count DESC
        LIMIT 5
    """)).fetchall()
    
    # Convert top fighters to dictionaries
    top_fighters = [row_to_dict(row) for row in top_fighters]
    
    return render_template('index.html',
                         recent_events=recent_events,
                         upcoming_events=upcoming_events,
                         top_fighters=top_fighters)

@app.route('/fighters')
def fighters():
    db = get_db()
    
    # Get all UFC fighters
    fighters = db.execute(text("""
        SELECT id, full_name
        FROM athletes
        WHERE default_league LIKE 'ufc%'
        ORDER BY full_name
    """)).fetchall()
    
    fighters = [row_to_dict(row) for row in fighters]
    
    return render_template('fighters.html', fighters=fighters)

@app.route('/fighter/<int:fighter_id>/timeline')
def fighter_timeline(fighter_id):
    db = get_db()
    
    # Get fighter basic info
    fighter = db.execute(text("""
        SELECT *
        FROM athletes
        WHERE id = :fighter_id
    """), {"fighter_id": fighter_id}).fetchone()
    
    if not fighter:
        return redirect(url_for('fighters'))

    fighter_dict = row_to_dict(fighter)

    # Get all fights for the fighter
    fights = db.execute(text("""
        SELECT f.*, c.date, c.event_name
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        WHERE f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id
        ORDER BY c.date DESC
    """), {"fighter_id": fighter_id}).fetchall()

    # Get fighter's rankings history
    rankings = db.execute(text("""
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
        
        # Get opponent details
        opponent = db.execute(text("""
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
    fighter_dict['record'] = f"{wins}-{losses}"

    return render_template('career_timeline.html', 
                         fighter=fighter_dict,
                         timeline_events=timeline_events)

@app.route('/fighter/<int:fighter_id>')
def fighter_page(fighter_id):
    db = get_db()
    
    # Get filter parameters
    promotion = request.args.get('promotion', 'all')
    rounds_format = request.args.get('rounds_format', 'all')
    fight_type = request.args.get('fight_type', 'all')
    weight_class = request.args.get('weight_class', 'all')
    odds_type = request.args.get('odds_type', 'all')
    
    # Get fighter details
    fighter = db.execute(text("""
        SELECT *
        FROM athletes
        WHERE id = :fighter_id
    """), {"fighter_id": fighter_id}).fetchone()
    
    if fighter:
        fighter_dict = row_to_dict(fighter)
        
        # Get fighter's record
        wins = db.execute(text("""
            SELECT COUNT(*) as wins
            FROM fights
            WHERE (fighter_1_id = :fighter_id AND fighter_1_winner = 1)
            OR (fighter_2_id = :fighter_id AND fighter_2_winner = 1)
        """), {"fighter_id": fighter_id}).scalar()
        
        losses = db.execute(text("""
            SELECT COUNT(*) as losses
            FROM fights
            WHERE (fighter_1_id = :fighter_id AND fighter_1_winner = 0)
            OR (fighter_2_id = :fighter_id AND fighter_2_winner = 0)
            AND NOT (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
        """), {"fighter_id": fighter_id}).scalar()
        
        draws = db.execute(text("""
            SELECT COUNT(*) as draws
            FROM fights
            WHERE (fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id)
            AND (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
        """), {"fighter_id": fighter_id}).scalar()
        
        fighter_dict['record'] = f"{wins}-{losses}-{draws}"
        
        # Build the filter conditions
        filter_conditions = []
        filter_params = {"fighter_id": fighter_id}
        
        if promotion != 'all':
            filter_conditions.append("c.league = :promotion")
            filter_params['promotion'] = promotion
        
        if rounds_format != 'all':
            filter_conditions.append("CAST(f.rounds_format AS INTEGER) = :rounds_format")
            filter_params['rounds_format'] = int(rounds_format)
        
        if fight_type != 'all':
            if fight_type == 'title':
                filter_conditions.append("f.fight_title LIKE '%Championship%'")
            elif fight_type == 'main':
                filter_conditions.append("f.card_segment = 'Main Event'")
            elif fight_type == 'co-main':
                filter_conditions.append("f.card_segment = 'Co-Main Event'")
        
        if weight_class != 'all':
            filter_conditions.append("f.weight_class = :weight_class")
            filter_params['weight_class'] = weight_class
        
        if odds_type != 'all':
            if odds_type == 'favorite':
                filter_conditions.append("""
                    CASE 
                        WHEN f.fighter_1_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american < 0
                        WHEN f.fighter_1_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american < 0
                        WHEN f.fighter_2_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american < 0
                        WHEN f.fighter_2_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american < 0
                    END
                """)
            elif odds_type == 'underdog':
                filter_conditions.append("""
                    CASE 
                        WHEN f.fighter_1_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american > 0
                        WHEN f.fighter_1_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american > 0
                        WHEN f.fighter_2_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american > 0
                        WHEN f.fighter_2_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american > 0
                    END
                """)
        
        filter_sql = " AND ".join(filter_conditions) if filter_conditions else "1=1"
        
        # Calculate filtered record
        filtered_record = db.execute(text(f"""
            WITH latest_odds AS (
                SELECT 
                    CAST(fight_id AS INTEGER) as fight_id,
                    home_athlete_id,
                    away_athlete_id,
                    home_moneyLine_odds_current_american,
                    away_moneyLine_odds_current_american,
                    ROW_NUMBER() OVER (PARTITION BY fight_id ORDER BY provider_id) as rn
                FROM odds
                WHERE provider_id != 59
            ),
            filtered_fights AS (
                SELECT 
                    CASE 
                        WHEN f.fighter_1_id = :fighter_id THEN f.fighter_1_winner
                        ELSE f.fighter_2_winner
                    END as won,
                    f.result_display_name,
                    f.fighter_1_id,
                    f.fighter_2_id
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                LEFT JOIN latest_odds o ON f.fight_id = o.fight_id AND o.rn = 1
                WHERE (f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id)
                AND {filter_sql}
            )
            SELECT 
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN won = 0 AND result_display_name NOT LIKE '%Draw%' AND result_display_name NOT LIKE '%No Contest%' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%' THEN 1 ELSE 0 END) as draws,
                SUM(CASE WHEN result_display_name LIKE '%Decision%' THEN 1 ELSE 0 END) as decisions,
                COUNT(*) as total_fights,
                SUM(CASE 
                    WHEN (fighter_1_id = :fighter_id AND won = 1 AND result_display_name LIKE '%KO%') OR 
                         (fighter_2_id = :fighter_id AND won = 1 AND result_display_name LIKE '%KO%')
                    THEN 1 ELSE 0 END) as ko_wins,
                SUM(CASE 
                    WHEN (fighter_1_id = :fighter_id AND won = 0 AND result_display_name LIKE '%KO%') OR 
                         (fighter_2_id = :fighter_id AND won = 0 AND result_display_name LIKE '%KO%')
                    THEN 1 ELSE 0 END) as ko_losses,
                SUM(CASE 
                    WHEN (fighter_1_id = :fighter_id AND won = 1 AND result_display_name LIKE '%Submission%') OR 
                         (fighter_2_id = :fighter_id AND won = 1 AND result_display_name LIKE '%Submission%')
                    THEN 1 ELSE 0 END) as sub_wins,
                SUM(CASE 
                    WHEN (fighter_1_id = :fighter_id AND won = 0 AND result_display_name LIKE '%Submission%') OR 
                         (fighter_2_id = :fighter_id AND won = 0 AND result_display_name LIKE '%Submission%')
                    THEN 1 ELSE 0 END) as sub_losses
            FROM filtered_fights
        """), filter_params).fetchone()
        
        fighter_dict['filtered_record'] = f"{filtered_record.wins}-{filtered_record.losses}-{filtered_record.draws}"
        fighter_dict['filtered_decisions'] = filtered_record.decisions
        fighter_dict['filtered_total_fights'] = filtered_record.total_fights
        fighter_dict['filtered_ko_record'] = f"{filtered_record.ko_wins}-{filtered_record.ko_losses}"
        fighter_dict['filtered_sub_record'] = f"{filtered_record.sub_wins}-{filtered_record.sub_losses}"
        
        # Get fighter's fight history with filters
        fight_history = db.execute(text(f"""
            WITH latest_odds AS (
                SELECT 
                    CAST(fight_id AS INTEGER) as fight_id,
                    home_athlete_id,
                    away_athlete_id,
                    home_moneyLine_odds_current_american,
                    away_moneyLine_odds_current_american,
                    ROW_NUMBER() OVER (PARTITION BY fight_id ORDER BY provider_id) as rn
                FROM odds
                WHERE provider_id != 59
            )
            SELECT 
                f.event_id_fight_id,
                c.date,
                c.event_name,
                c.event_id as event_id,
                c.league as league_name,
                CAST(f.rounds_format AS INTEGER) as rounds_format,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN a2.full_name
                    ELSE a1.full_name
                END as opponent,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN a2.id
                    ELSE a1.id
                END as opponent_id,
                CASE 
                    WHEN f.result_display_name LIKE '%Draw%' OR f.result_display_name LIKE '%No Contest%' THEN NULL
                    WHEN f.fighter_1_id = :fighter_id THEN f.fighter_1_winner
                    ELSE f.fighter_2_winner
                END as won,
                f.weight_class,
                f.rounds_format,
                f.result_display_name,
                f.end_round,
                f.end_time,
                f.fight_title,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american
                    WHEN f.fighter_1_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american
                    WHEN f.fighter_2_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american
                    WHEN f.fighter_2_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american
                    ELSE NULL
                END as fighter_odds,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN s1.sigStrikesLanded
                    ELSE s2.sigStrikesLanded
                END as sig_strikes_landed,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN s1.sigStrikesAttempted
                    ELSE s2.sigStrikesAttempted
                END as sig_strikes_attempted,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN s1.takedownsLanded
                    ELSE s2.takedownsLanded
                END as takedowns_landed,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN s1.takedownsAttempted
                    ELSE s2.takedownsAttempted
                END as takedowns_attempted
            FROM fights f
            JOIN athletes a1 ON f.fighter_1_id = a1.id
            JOIN athletes a2 ON f.fighter_2_id = a2.id
            JOIN cards c ON f.event_id = c.event_id
            LEFT JOIN latest_odds o ON f.fight_id = o.fight_id AND o.rn = 1
            LEFT JOIN statistics_for_fights s1 ON f.event_id = s1.event_id AND f.fighter_1_id = s1.athlete_id
            LEFT JOIN statistics_for_fights s2 ON f.event_id = s2.event_id AND f.fighter_2_id = s2.athlete_id
            WHERE (f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id)
            AND {filter_sql}
            ORDER BY c.date DESC
        """), filter_params).fetchall()
        
        fighter_dict['fight_history'] = [row_to_dict(fight) for fight in fight_history]
        
        # Get available promotions for filter
        promotions = db.execute(text("""
            SELECT DISTINCT league
            FROM cards
            WHERE event_id IN (
                SELECT event_id
                FROM fights
                WHERE fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id
            )
            ORDER BY league
        """), {"fighter_id": fighter_id}).fetchall()
        fighter_dict['promotions'] = [row[0] for row in promotions]
        
        # Get available rounds formats for filter
        rounds_formats = db.execute(text("""
            SELECT DISTINCT CAST(rounds_format AS INTEGER) as rounds
            FROM fights
            WHERE (fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id)
            AND rounds_format IS NOT NULL
            ORDER BY rounds
        """), {"fighter_id": fighter_id}).fetchall()
        fighter_dict['rounds_formats'] = [row[0] for row in rounds_formats]
        
        # Get available weight classes for filter
        weight_classes = db.execute(text("""
            SELECT DISTINCT weight_class
            FROM fights
            WHERE (fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id)
            AND weight_class IS NOT NULL
            ORDER BY weight_class
        """), {"fighter_id": fighter_id}).fetchall()
        fighter_dict['weight_classes'] = [row[0] for row in weight_classes]
        
        # Add current filter values
        fighter_dict['current_filters'] = {
            'promotion': promotion,
            'rounds_format': rounds_format,
            'fight_type': fight_type,
            'weight_class': weight_class,
            'odds_type': odds_type
        }
        
        return render_template('fighter.html', fighter=fighter_dict)
    
    return render_template('404.html'), 404

@app.route('/api/fighter/<int:fighter_id>')
def get_fighter(fighter_id):
    db = get_db()
    
    # Get fighter details
    fighter = db.execute(text("""
        SELECT *
        FROM athletes
        WHERE id = :fighter_id
    """), {"fighter_id": fighter_id}).fetchone()
    
    if fighter:
        fighter_dict = row_to_dict(fighter)
        
        # Get fighter's record
        wins = db.execute(text("""
            SELECT COUNT(*) as wins
            FROM fights
            WHERE (fighter_1_id = :fighter_id AND fighter_1_winner = 1)
            OR (fighter_2_id = :fighter_id AND fighter_2_winner = 1)
        """), {"fighter_id": fighter_id}).scalar()
        
        losses = db.execute(text("""
            SELECT COUNT(*) as losses
            FROM fights
            WHERE (fighter_1_id = :fighter_id AND fighter_1_winner = 0)
            OR (fighter_2_id = :fighter_id AND fighter_2_winner = 0)
            AND NOT (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
        """), {"fighter_id": fighter_id}).scalar()
        
        draws = db.execute(text("""
            SELECT COUNT(*) as draws
            FROM fights
            WHERE (fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id)
            AND (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
        """), {"fighter_id": fighter_id}).scalar()
        
        fighter_dict['record'] = f"{wins}-{losses}-{draws}"
        
        # Get fighter's fight history
        fight_history = db.execute(text("""
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
                f.event_id_fight_id,
                c.date,
                c.event_name,
                c.event_id as event_id,
                c.league as league_name,
                CAST(f.rounds_format AS INTEGER) as rounds_format,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN a2.full_name
                    ELSE a1.full_name
                END as opponent,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN a2.id
                    ELSE a1.id
                END as opponent_id,
                CASE 
                    WHEN f.result_display_name LIKE '%Draw%' OR f.result_display_name LIKE '%No Contest%' THEN NULL
                    WHEN f.fighter_1_id = :fighter_id THEN f.fighter_1_winner
                    ELSE f.fighter_2_winner
                END as won,
                f.weight_class,
                f.rounds_format,
                f.result_display_name,
                f.end_round,
                f.end_time,
                f.fight_title,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american
                    WHEN f.fighter_1_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american
                    WHEN f.fighter_2_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american
                    WHEN f.fighter_2_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american
                    ELSE NULL
                END as fighter_odds
            FROM fights f
            JOIN athletes a1 ON f.fighter_1_id = a1.id
            JOIN athletes a2 ON f.fighter_2_id = a2.id
            JOIN cards c ON f.event_id = c.event_id
            LEFT JOIN latest_odds o ON f.fight_id = o.fight_id AND o.rn = 1
            WHERE f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id
            ORDER BY c.date DESC
        """), {"fighter_id": fighter_id}).fetchall()
        
        fighter_dict['fight_history'] = [row_to_dict(fight) for fight in fight_history]
        
        return jsonify(fighter_dict)
    
    return jsonify({"error": "Fighter not found"}), 404

@app.route('/api/fighters/search')
def search_fighters():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    db = get_db()
    
    # Normalize the search query
    normalized_query = normalize_ascii(query)
    
    # Fetch all fighters and filter in Python to allow normalized comparison
    fighters = db.execute(text("""
        SELECT id, full_name
        FROM athletes
        WHERE default_league LIKE '%'
        ORDER BY full_name
    """)).fetchall()
    
    # Filter fighters by normalized name
    results = [
        row_to_dict(row)
        for row in fighters
        if normalized_query in normalize_ascii(row.full_name)
    ][:10]  # Limit to 10 results
    
    return jsonify(results)

@app.route('/events')
def events():
    selected_year = request.args.get('year')
    selected_event_id = request.args.get('event_id')
    
    db = get_db()
    
    # Get distinct years from cards table
    years = db.execute(text("""
        SELECT DISTINCT strftime('%Y', date) as year
        FROM cards
        ORDER BY year DESC
    """)).fetchall()
    years = [row[0] for row in years]
    
    # If we have an event_id but no year, get the year from the event
    if selected_event_id and not selected_year:
        event = db.execute(text("""
            SELECT strftime('%Y', date) as year
            FROM cards
            WHERE event_id = :event_id
        """), {"event_id": selected_event_id}).fetchone()
        if event:
            selected_year = event[0]
    
    # Get events for the selected year
    events_list = []
    if selected_year:
        events_list = db.execute(text("""
            SELECT *
            FROM cards
            WHERE strftime('%Y', date) = :year
            ORDER BY date DESC
        """), {"year": selected_year}).fetchall()
        events_list = [row_to_dict(row) for row in events_list]
    
    # Get selected event details if an event is selected
    selected_event = None
    if selected_event_id:
        selected_event = db.execute(text("""
            SELECT *
            FROM cards
            WHERE event_id = :event_id
        """), {"event_id": selected_event_id}).fetchone()
        
        if selected_event:
            selected_event = row_to_dict(selected_event)
            
            # Get all fights for this event with fighter details and odds
            fights = db.execute(text("""
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
                ORDER BY f.match_number
            """), {"event_id": selected_event_id}).fetchall()
            
            # Convert fights to dictionaries and add stats availability
            selected_event['fights'] = []
            for fight in fights:
                fight_dict = row_to_dict(fight)
                # Check if stats are available
                stats = db.execute(text("""
                    SELECT COUNT(*) as count
                    FROM statistics_for_fights
                    WHERE event_id = :event_id
                    AND (athlete_id = :fighter_1_id OR athlete_id = :fighter_2_id)
                """), {
                    "event_id": selected_event_id,
                    "fighter_1_id": fight.fighter_1_id,
                    "fighter_2_id": fight.fighter_2_id
                }).scalar()
                
                fight_dict['has_stats'] = stats > 0
                selected_event['fights'].append(fight_dict)
    
    return render_template('events.html',
                         years=years,
                         selected_year=selected_year,
                         events_list=events_list,
                         selected_event=selected_event)

@app.route('/api/fight-stats/<fight_id>')
def get_fight_stats(fight_id):
    db = get_db()
    
    # Get fight details to get fighter IDs and event_id
    fight = db.execute(text("""
        SELECT f.fighter_1_id, f.fighter_2_id, c.event_id
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id
        WHERE f.event_id_fight_id = :fight_id
    """), {"fight_id": fight_id}).fetchone()
    
    if not fight:
        return jsonify({"error": "Fight not found"}), 404
    
    # Get stats for both fighters for this specific fight
    fighter1_stats = db.execute(text("""
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
    
    fighter2_stats = db.execute(text("""
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
    
    return jsonify({
        "fighter1_stats": row_to_dict(fighter1_stats) if fighter1_stats else None,
        "fighter2_stats": row_to_dict(fighter2_stats) if fighter2_stats else None
    })

@app.route('/rankings')
def rankings():
    db = get_db()
    
    # Get all rankings grouped by type
    rankings_query = text("""
        WITH RankedFighters AS (
            SELECT 
                CASE 
                    WHEN ranking_type LIKE '%Pound for Pound%' THEN 'Pound for Pound'
                    ELSE 'Division Rankings'
                END as ranking_type,
                division,
                fighter_name,
                rank,
                is_champion,
                is_interim_champion,
                is_p4p,
                p4p_rank,
                r.gender,
                last_updated,
                a.headshot_url,
                a.id as athlete_id
            FROM ufc_rankings r
            LEFT JOIN athletes a ON LOWER(a.full_name) = LOWER(r.fighter_name)
        )
        SELECT * FROM RankedFighters
        ORDER BY 
            CASE 
                WHEN ranking_type = 'Pound for Pound' THEN 1
                ELSE 2
            END,
            CASE 
                WHEN ranking_type = 'Pound for Pound' THEN p4p_rank
                ELSE NULL
            END,
            CASE 
                WHEN ranking_type != 'Pound for Pound' THEN division
                ELSE NULL
            END,
            CASE 
                WHEN ranking_type != 'Pound for Pound' THEN
                    CASE 
                        WHEN is_champion = 1 THEN 0
                        WHEN is_interim_champion = 1 THEN 1
                        ELSE rank
                    END
                ELSE NULL
            END NULLS LAST
    """)
    
    rankings = db.execute(rankings_query).fetchall()
    
    # Group rankings by type and division
    grouped_rankings = {}
    for row in rankings:
        # Convert SQLAlchemy Row to dictionary
        row_dict = dict(row._mapping)
        ranking_type = row_dict['ranking_type']
        
        if ranking_type not in grouped_rankings:
            grouped_rankings[ranking_type] = {}
            
        # For P4P rankings, use a single division to group all fighters
        if ranking_type == 'Pound for Pound':
            division = 'Pound for Pound'
        else:
            division = row_dict['division']
            
        if division not in grouped_rankings[ranking_type]:
            grouped_rankings[ranking_type][division] = []
            
        grouped_rankings[ranking_type][division].append(row_dict)
    
    # Get the last updated timestamp
    last_updated = rankings[0]._mapping['last_updated'] if rankings else None
    
    return render_template('rankings.html', 
                         rankings=grouped_rankings,
                         last_updated=last_updated)

@app.route('/next-event')
def next_event():
    # Get the next UFC event URL
    ufc_events_url = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/events/?lang=en&region=us"
    ufc_event_response = httpx.get(ufc_events_url)
    ufc_event_response.raise_for_status()
    ufc_event_data = ufc_event_response.json()
    
    next_ufc_event_url = ufc_event_data['items'][0]['$ref']
    
    # Process the next event data
    card, fights = process_next_event(next_ufc_event_url)
    
    if card:
        # Always show the event if we have card data
        if fights:
            db = get_db()
            
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
                    fighters = db.execute(text(f"""
                        SELECT id, full_name, headshot_url
                        FROM athletes
                        WHERE id IN ({fighter_ids_str})
                    """)).fetchall()
                    
                    # Create a lookup dictionary for fighter details
                    fighter_lookup = {str(f.id): f for f in fighters}
                    
                    # Get all fighter records in one query
                    fighter_records = db.execute(text(f"""
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

@app.route('/fighter-wordle')
def fighter_wordle():
    return render_template('fighter_wordle.html')

@app.route('/api/fighter-wordle/new-game')
def new_fighter_wordle_game():
    db = get_db()
    # Select all UFC fighters who have fought since 2023
    eligible_fighters = db.execute(text("""
        SELECT DISTINCT a.full_name
        FROM athletes a
        JOIN fights f ON (a.id = f.fighter_1_id OR a.id = f.fighter_2_id)
        JOIN cards c ON f.event_id = c.event_id
        WHERE a.default_league LIKE 'ufc%'
        AND c.date >= '2023-01-01'
    """)).fetchall()
    if not eligible_fighters:
        return jsonify({'error': 'No eligible fighters found'}), 404
    fighter_name = random.choice([row[0] for row in eligible_fighters])
    # Get the random fighter's details
    fighter = db.execute(text("""
        SELECT 
            a.id,
            a.full_name as name,
            a.weight_class,
            a.height,
            a.headshot_url,
            a.flag_url,
            a.gender,
            a.age,
            (
                SELECT COUNT(*) 
                FROM fights 
                WHERE (fighter_1_id = a.id AND fighter_1_winner = 1)
                OR (fighter_2_id = a.id AND fighter_2_winner = 1)
            ) as wins,
            (
                SELECT COUNT(*) 
                FROM fights 
                WHERE (fighter_1_id = a.id AND fighter_1_winner = 0)
                OR (fighter_2_id = a.id AND fighter_2_winner = 0)
                AND NOT (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
            ) as losses,
            (
                SELECT COUNT(*) 
                FROM fights 
                WHERE (fighter_1_id = a.id OR fighter_2_id = a.id)
                AND (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
            ) as draws,
            (
                SELECT COUNT(*) 
                FROM fights 
                WHERE fighter_1_id = a.id OR fighter_2_id = a.id
            ) as total_fights
        FROM athletes a
        WHERE LOWER(a.full_name) = LOWER(:fighter)
        AND a.default_league LIKE 'ufc%'
    """), {'fighter': fighter_name}).fetchone()
    if fighter:
        fighter_dict = row_to_dict(fighter)
        # Format record
        fighter_dict['record'] = f"{fighter_dict['wins']}-{fighter_dict['losses']}-{fighter_dict['draws']}"
        # Remove unnecessary fields
        fighter_dict.pop('wins', None)
        fighter_dict.pop('losses', None)
        fighter_dict.pop('draws', None)
        # Store the target fighter in the session
        session['target_fighter'] = fighter_dict
        return jsonify({'fighter': fighter_dict})
    return jsonify({'error': 'Fighter not found'}), 404

@app.route('/api/fighter-wordle/check-guess', methods=['POST'])
def check_fighter_wordle_guess():
    data = request.get_json()
    guess = data.get('guess', '').strip()
    
    if not guess:
        return jsonify({'error': 'No guess provided'}), 400
    
    db = get_db()
    
    # Get the guessed fighter's details
    guessed_fighter = db.execute(text("""
        SELECT 
            a.id,
            a.full_name as name,
            a.weight_class,
            a.height,
            a.headshot_url,
            a.flag_url,
            a.gender,
            a.age,
            (
                SELECT COUNT(*) 
                FROM fights 
                WHERE (fighter_1_id = a.id AND fighter_1_winner = 1)
                OR (fighter_2_id = a.id AND fighter_2_winner = 1)
            ) as wins,
            (
                SELECT COUNT(*) 
                FROM fights 
                WHERE (fighter_1_id = a.id AND fighter_1_winner = 0)
                OR (fighter_2_id = a.id AND fighter_2_winner = 0)
                AND NOT (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
            ) as losses,
            (
                SELECT COUNT(*) 
                FROM fights 
                WHERE (fighter_1_id = a.id OR fighter_2_id = a.id)
                AND (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
            ) as draws,
            (
                SELECT COUNT(*) 
                FROM fights 
                WHERE fighter_1_id = a.id OR fighter_2_id = a.id
            ) as total_fights
        FROM athletes a
        WHERE LOWER(a.full_name) = LOWER(:guess)
        AND a.default_league LIKE 'ufc%'
    """), {'guess': guess}).fetchone()
    
    if not guessed_fighter:
        return jsonify({'error': 'Fighter not found'}), 404
    
    guessed_fighter_dict = row_to_dict(guessed_fighter)
    
    # Format record
    guessed_fighter_dict['record'] = f"{guessed_fighter_dict['wins']}-{guessed_fighter_dict['losses']}-{guessed_fighter_dict['draws']}"
    
    # Remove unnecessary fields
    guessed_fighter_dict.pop('wins', None)
    guessed_fighter_dict.pop('losses', None)
    guessed_fighter_dict.pop('draws', None)
    
    # Get the target fighter from the session
    target_fighter = session.get('target_fighter')
    if not target_fighter:
        return jsonify({'error': 'No active game'}), 400
    
    # Define weight class order for proximity check
    weight_classes = [
        'Strawweight', 'Flyweight', 'Bantamweight', 'Featherweight', 
        'Lightweight', 'Welterweight', 'Middleweight', 'Light Heavyweight', 
        'Heavyweight'
    ]
    
    # Get weight class indices for proximity check
    target_weight_index = weight_classes.index(target_fighter['weight_class']) if target_fighter['weight_class'] in weight_classes else -1
    guess_weight_index = weight_classes.index(guessed_fighter_dict['weight_class']) if guessed_fighter_dict['weight_class'] in weight_classes else -1
    
    # Compare height
    target_height = float(target_fighter['height'].replace('"', '')) if target_fighter['height'] else 0
    guess_height = float(guessed_fighter_dict['height'].replace('"', '')) if guessed_fighter_dict['height'] else 0
    height_diff = abs(target_height - guess_height)
    
    # Compare age
    target_age = target_fighter['age']
    guess_age = guessed_fighter_dict['age']
    age_diff = abs(target_age - guess_age) if target_age is not None and guess_age is not None else float('inf')
    
    # Compare total fights
    target_fights = target_fighter['total_fights']
    guess_fights = guessed_fighter_dict['total_fights']
    fights_diff = abs(target_fights - guess_fights) if target_fights is not None and guess_fights is not None else float('inf')
    
    # Compare the guess with the target fighter
    result = {
        'name': guessed_fighter_dict['name'],
        'headshot_url': guessed_fighter_dict['headshot_url'],
        'flag_url': {
            'url': guessed_fighter_dict['flag_url'],
            'status': 'correct' if guessed_fighter_dict['flag_url'] == target_fighter['flag_url'] else 'incorrect'
        },
        'weight_class': {
            'value': guessed_fighter_dict['weight_class'],
            'status': 'correct' if guessed_fighter_dict['weight_class'] == target_fighter['weight_class'] else 
                     'close' if abs(target_weight_index - guess_weight_index) == 1 else 'incorrect'
        },
        'gender': {
            'value': guessed_fighter_dict['gender'],
            'status': 'correct' if guessed_fighter_dict['gender'] == target_fighter['gender'] else 'incorrect'
        },
        'height': {
            'value': guessed_fighter_dict['height'],
            'status': 'correct' if height_diff == 0 else 
                     'close' if height_diff <= 2 else 'incorrect',
            'direction': 'up' if guess_height < target_height else 'down' if guess_height > target_height else None
        },
        'age': {
            'value': guess_age,
            'status': 'correct' if age_diff == 0 else 
                     'close' if age_diff <= 2 else 'incorrect',
            'direction': 'up' if guess_age is not None and target_age is not None and guess_age < target_age else 
                        'down' if guess_age is not None and target_age is not None and guess_age > target_age else None
        },
        'total_fights': {
            'value': guess_fights,
            'status': 'correct' if fights_diff == 0 else 
                     'close' if fights_diff <= 2 else 'incorrect',
            'direction': 'up' if guess_fights is not None and target_fights is not None and guess_fights < target_fights else 
                        'down' if guess_fights is not None and target_fights is not None and guess_fights > target_fights else None
        },
        'correct': guessed_fighter_dict['id'] == target_fighter['id']
    }
    
    return jsonify(result)

@app.route('/tale-of-tape')
def tale_of_tape():
    db = get_db()
    
    # Get all UFC fighters for the dropdown
    fighters = db.execute(text("""
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
        selected_fighter1 = get_fighter_data(db, fighter1_id, fighter1_filters)
    
    if fighter2_id:
        selected_fighter2 = get_fighter_data(db, fighter2_id, fighter2_filters)
    
    return render_template('tale_of_tape.html',
                         fighters=fighters,
                         selected_fighter1=selected_fighter1,
                         selected_fighter2=selected_fighter2,
                         fighter1_filters=fighter1_filters,
                         fighter2_filters=fighter2_filters)

def get_fighter_data(db, fighter_id, filters=None):
    if filters is None:
        filters = {
            'promotion': 'all',
            'rounds_format': 'all',
            'fight_type': 'all',
            'weight_class': 'all',
            'odds_type': 'all'
        }
    
    # Get fighter details
    fighter = db.execute(text("""
        SELECT *
        FROM athletes
        WHERE id = :fighter_id
    """), {"fighter_id": fighter_id}).fetchone()
    
    if fighter:
        fighter_dict = row_to_dict(fighter)
        
        # Get fighter's record
        wins = db.execute(text("""
            SELECT COUNT(*) as wins
            FROM fights
            WHERE (fighter_1_id = :fighter_id AND fighter_1_winner = 1)
            OR (fighter_2_id = :fighter_id AND fighter_2_winner = 1)
        """), {"fighter_id": fighter_id}).scalar()
        
        losses = db.execute(text("""
            SELECT COUNT(*) as losses
            FROM fights
            WHERE (fighter_1_id = :fighter_id AND fighter_1_winner = 0)
            OR (fighter_2_id = :fighter_id AND fighter_2_winner = 0)
            AND NOT (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
        """), {"fighter_id": fighter_id}).scalar()
        
        draws = db.execute(text("""
            SELECT COUNT(*) as draws
            FROM fights
            WHERE (fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id)
            AND (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
        """), {"fighter_id": fighter_id}).scalar()
        
        fighter_dict['record'] = f"{wins}-{losses}-{draws}"
        
        # Build the filter conditions
        filter_conditions = []
        filter_params = {"fighter_id": fighter_id}
        
        if filters['promotion'] != 'all':
            filter_conditions.append("c.league = :promotion")
            filter_params['promotion'] = filters['promotion']
        
        if filters['rounds_format'] != 'all':
            filter_conditions.append("CAST(f.rounds_format AS INTEGER) = :rounds_format")
            filter_params['rounds_format'] = int(filters['rounds_format'])
        
        if filters['weight_class'] != 'all':
            filter_conditions.append("f.weight_class = :weight_class")
            filter_params['weight_class'] = filters['weight_class']
        
        if filters['odds_type'] != 'all':
            if filters['odds_type'] == 'favorite':
                filter_conditions.append("""
                    CASE 
                        WHEN f.fighter_1_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american < 0
                        WHEN f.fighter_1_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american < 0
                        WHEN f.fighter_2_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american < 0
                        WHEN f.fighter_2_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american < 0
                    END
                """)
            elif filters['odds_type'] == 'underdog':
                filter_conditions.append("""
                    CASE 
                        WHEN f.fighter_1_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american > 0
                        WHEN f.fighter_1_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american > 0
                        WHEN f.fighter_2_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american > 0
                        WHEN f.fighter_2_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american > 0
                    END
                """)
        
        filter_sql = " AND ".join(filter_conditions) if filter_conditions else "1=1"
        
        # Get fighter's fight history with filters
        fight_history = db.execute(text(f"""
            WITH latest_odds AS (
                SELECT 
                    CAST(fight_id AS INTEGER) as fight_id,
                    home_athlete_id,
                    away_athlete_id,
                    home_moneyLine_odds_current_american,
                    away_moneyLine_odds_current_american,
                    ROW_NUMBER() OVER (PARTITION BY fight_id ORDER BY provider_id) as rn
                FROM odds
                WHERE provider_id != 59
            )
            SELECT 
                f.event_id_fight_id,
                c.date,
                c.event_name,
                c.event_id as event_id,
                c.league as league_name,
                CAST(f.rounds_format AS INTEGER) as rounds_format,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN a2.full_name
                    ELSE a1.full_name
                END as opponent,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN a2.id
                    ELSE a1.id
                END as opponent_id,
                CASE 
                    WHEN f.result_display_name LIKE '%Draw%' OR f.result_display_name LIKE '%No Contest%' THEN NULL
                    WHEN f.fighter_1_id = :fighter_id THEN f.fighter_1_winner
                    ELSE f.fighter_2_winner
                END as won,
                f.weight_class,
                f.rounds_format,
                f.result_display_name,
                f.end_round,
                f.end_time,
                f.fight_title,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american
                    WHEN f.fighter_1_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american
                    WHEN f.fighter_2_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american
                    WHEN f.fighter_2_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american
                    ELSE NULL
                END as fighter_odds,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN s1.sigStrikesLanded
                    ELSE s2.sigStrikesLanded
                END as sig_strikes_landed,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN s1.sigStrikesAttempted
                    ELSE s2.sigStrikesAttempted
                END as sig_strikes_attempted,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN s1.takedownsLanded
                    ELSE s2.takedownsLanded
                END as takedowns_landed,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN s1.takedownsAttempted
                    ELSE s2.takedownsAttempted
                END as takedowns_attempted
            FROM fights f
            JOIN athletes a1 ON f.fighter_1_id = a1.id
            JOIN athletes a2 ON f.fighter_2_id = a2.id
            JOIN cards c ON f.event_id = c.event_id
            LEFT JOIN latest_odds o ON f.fight_id = o.fight_id AND o.rn = 1
            LEFT JOIN statistics_for_fights s1 ON f.event_id = s1.event_id AND f.fighter_1_id = s1.athlete_id
            LEFT JOIN statistics_for_fights s2 ON f.event_id = s2.event_id AND f.fighter_2_id = s2.athlete_id
            WHERE (f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id)
            AND {filter_sql}
            ORDER BY c.date DESC
        """), filter_params).fetchall()
        
        fighter_dict['fight_history'] = [row_to_dict(fight) for fight in fight_history]
        
        # Calculate filtered stats
        filtered_stats = db.execute(text(f"""
            WITH latest_odds AS (
                SELECT 
                    CAST(fight_id AS INTEGER) as fight_id,
                    home_athlete_id,
                    away_athlete_id,
                    home_moneyLine_odds_current_american,
                    away_moneyLine_odds_current_american,
                    ROW_NUMBER() OVER (PARTITION BY fight_id ORDER BY provider_id) as rn
                FROM odds
                WHERE provider_id != 59
            ),
            filtered_fights AS (
                SELECT 
                    CASE 
                        WHEN f.fighter_1_id = :fighter_id THEN f.fighter_1_winner
                        ELSE f.fighter_2_winner
                    END as won,
                    f.result_display_name,
                    f.fighter_1_id,
                    f.fighter_2_id
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                LEFT JOIN latest_odds o ON f.fight_id = o.fight_id AND o.rn = 1
                WHERE (f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id)
                AND {filter_sql}
            )
            SELECT 
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN won = 0 AND result_display_name NOT LIKE '%Draw%' AND result_display_name NOT LIKE '%No Contest%' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%' THEN 1 ELSE 0 END) as draws,
                SUM(CASE WHEN result_display_name LIKE '%Decision%' THEN 1 ELSE 0 END) as decisions,
                COUNT(*) as total_fights,
                SUM(CASE 
                    WHEN (fighter_1_id = :fighter_id AND won = 1 AND result_display_name LIKE '%KO%') OR 
                         (fighter_2_id = :fighter_id AND won = 1 AND result_display_name LIKE '%KO%')
                    THEN 1 ELSE 0 END) as ko_wins,
                SUM(CASE 
                    WHEN (fighter_1_id = :fighter_id AND won = 0 AND result_display_name LIKE '%KO%') OR 
                         (fighter_2_id = :fighter_id AND won = 0 AND result_display_name LIKE '%KO%')
                    THEN 1 ELSE 0 END) as ko_losses,
                SUM(CASE 
                    WHEN (fighter_1_id = :fighter_id AND won = 1 AND result_display_name LIKE '%Submission%') OR 
                         (fighter_2_id = :fighter_id AND won = 1 AND result_display_name LIKE '%Submission%')
                    THEN 1 ELSE 0 END) as sub_wins,
                SUM(CASE 
                    WHEN (fighter_1_id = :fighter_id AND won = 0 AND result_display_name LIKE '%Submission%') OR 
                         (fighter_2_id = :fighter_id AND won = 0 AND result_display_name LIKE '%Submission%')
                    THEN 1 ELSE 0 END) as sub_losses
            FROM filtered_fights
        """), filter_params).fetchone()
        
        fighter_dict['filtered_record'] = f"{filtered_stats.wins}-{filtered_stats.losses}-{filtered_stats.draws}"
        fighter_dict['filtered_decisions'] = filtered_stats.decisions
        fighter_dict['filtered_total_fights'] = filtered_stats.total_fights
        fighter_dict['filtered_ko_record'] = f"{filtered_stats.ko_wins}-{filtered_stats.ko_losses}"
        fighter_dict['filtered_sub_record'] = f"{filtered_stats.sub_wins}-{filtered_stats.sub_losses}"
        
        # Get available promotions for filter
        promotions = db.execute(text("""
            SELECT DISTINCT league
            FROM cards
            WHERE event_id IN (
                SELECT event_id
                FROM fights
                WHERE fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id
            )
            ORDER BY league
        """), {"fighter_id": fighter_id}).fetchall()
        fighter_dict['promotions'] = [row[0] for row in promotions]
        
        # Get available rounds formats for filter
        rounds_formats = db.execute(text("""
            SELECT DISTINCT CAST(rounds_format AS INTEGER) as rounds
            FROM fights
            WHERE (fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id)
            AND rounds_format IS NOT NULL
            ORDER BY rounds
        """), {"fighter_id": fighter_id}).fetchall()
        fighter_dict['rounds_formats'] = [row[0] for row in rounds_formats]
        
        # Get available weight classes for filter
        weight_classes = db.execute(text("""
            SELECT DISTINCT weight_class
            FROM fights
            WHERE (fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id)
            AND weight_class IS NOT NULL
            ORDER BY weight_class
        """), {"fighter_id": fighter_id}).fetchall()
        fighter_dict['weight_classes'] = [row[0] for row in weight_classes]
        
        return fighter_dict
    
    return None

@app.route('/career-timeline')
def career_timeline():
    db = get_db()
    # Get all fighters with their basic info
    fighters = db.execute(text("""
        SELECT id, full_name
        FROM athletes
        WHERE default_league LIKE 'ufc%'
        ORDER BY full_name
    """)).fetchall()
    
    fighters = [row_to_dict(row) for row in fighters]
    
    return render_template('career_timeline_landing.html', fighters=fighters)

@app.route('/system-checker')
def system_checker():
    
    # Get filter parameters from request
    ufc_only = request.args.get('ufc_only', 'false').lower() == 'true'
    min_age_diff = int(request.args.get('min_age_diff', '6'))  # Default to 6 years if not specified
    betting_status = request.args.get('betting_status', 'any')  # Default to 'any' if not specified
    selected_weight_classes = request.args.getlist('weight_classes')  # Get list of selected weight classes
    
    # Base filter condition
    filter_condition = "c.league = 'ufc'" if ufc_only else "1=1"
    
    # Weight class filter condition for age difference analysis
    weight_class_condition = "1=1"  # Default to no filter
    if selected_weight_classes:
        # Create placeholders for each weight class
        placeholders = ', '.join([':weight_class_' + str(i) for i in range(len(selected_weight_classes))])
        weight_class_condition = f"f.weight_class IN ({placeholders})"
    
    # Betting status filter condition
    betting_condition = {
        'any': "1=1",
        'favorite': "o.home_moneyLine_odds_current_value < o.away_moneyLine_odds_current_value",
        'underdog': "o.home_moneyLine_odds_current_value > o.away_moneyLine_odds_current_value"
    }[betting_status]
    
    # Calculate younger fighter win rate and get detailed fight data (with all filters)
    younger_fighter_query = f"""
        WITH age_differences AS (
            SELECT 
                f1.id as younger_fighter_id,
                f2.id as older_fighter_id,
                f1.full_name as younger_fighter_name,
                f2.full_name as older_fighter_name,
                f1.date_of_birth as younger_dob,
                f2.date_of_birth as older_dob,
                CASE 
                    WHEN f.fighter_1_winner THEN f.fighter_1_id
                    ELSE f.fighter_2_id
                END as winner_id,
                f.fight_id,
                f.result_display_name,
                f.end_round,
                f.end_time,
                c.event_name,
                c.date as fight_date,
                o.home_moneyLine_odds_current_american as fighter1_odds,
                o.away_moneyLine_odds_current_american as fighter2_odds,
                ROUND((JULIANDAY(c.date) - JULIANDAY(f1.date_of_birth)) / 365.25, 1) as younger_age,
                ROUND((JULIANDAY(c.date) - JULIANDAY(f2.date_of_birth)) / 365.25, 1) as older_age,
                ROUND((JULIANDAY(c.date) - JULIANDAY(f2.date_of_birth)) / 365.25 - (JULIANDAY(c.date) - JULIANDAY(f1.date_of_birth)) / 365.25, 1) as age_diff,
                CASE 
                    WHEN o.home_moneyLine_odds_current_value < o.away_moneyLine_odds_current_value THEN 'favorite'
                    WHEN o.home_moneyLine_odds_current_value > o.away_moneyLine_odds_current_value THEN 'underdog'
                    ELSE NULL
                END as younger_fighter_betting_status,
                f.weight_class
            FROM fights f
            JOIN athletes f1 ON f.fighter_1_id = f1.id
            JOIN athletes f2 ON f.fighter_2_id = f2.id
            JOIN cards c ON f.event_id = c.event_id
            LEFT JOIN (
                SELECT 
                    fight_id,
                    home_moneyLine_odds_current_american,
                    away_moneyLine_odds_current_american,
                    home_moneyLine_odds_current_value,
                    away_moneyLine_odds_current_value,
                    ROW_NUMBER() OVER (PARTITION BY fight_id ORDER BY provider_id) as rn
                FROM odds
                WHERE provider_id != 59
            ) o ON f.fight_id = o.fight_id AND o.rn = 1
            WHERE ROUND((JULIANDAY(c.date) - JULIANDAY(f2.date_of_birth)) / 365.25 - (JULIANDAY(c.date) - JULIANDAY(f1.date_of_birth)) / 365.25, 1) >= :min_age_diff
            AND {filter_condition}
            AND ({betting_condition} OR o.fight_id IS NULL)
            AND {weight_class_condition}
        )
        SELECT 
            COUNT(*) as total_fights,
            SUM(CASE WHEN winner_id = younger_fighter_id THEN 1 ELSE 0 END) as younger_wins,
            json_group_array(
                json_object(
                    'younger_fighter', younger_fighter_name,
                    'older_fighter', older_fighter_name,
                    'younger_age', younger_age,
                    'older_age', older_age,
                    'age_diff', age_diff,
                    'winner', CASE WHEN winner_id = younger_fighter_id THEN younger_fighter_name ELSE older_fighter_name END,
                    'result', result_display_name,
                    'end_round', end_round,
                    'end_time', end_time,
                    'event', event_name,
                    'date', fight_date,
                    'fighter1_odds', fighter1_odds,
                    'fighter2_odds', fighter2_odds,
                    'younger_fighter_betting_status', younger_fighter_betting_status,
                    'weight_class', weight_class
                )
            ) as fight_details
        FROM age_differences
    """
    
    # Prepare parameters for the query
    params = {"min_age_diff": min_age_diff}
    if selected_weight_classes:
        # Add each weight class as a separate parameter
        for i, weight_class in enumerate(selected_weight_classes):
            params[f"weight_class_{i}"] = weight_class
    
    younger_fighter_stats = db.session.execute(
        text(younger_fighter_query),
        params
    ).fetchone()
    
    # Parse the JSON fight details
    fight_details = json.loads(younger_fighter_stats.fight_details) if younger_fighter_stats.fight_details else []
    
    # Sort fight details by date (most recent first)
    fight_details.sort(key=lambda x: x['date'], reverse=True)
    
    younger_fighter_win_rate = round((younger_fighter_stats.younger_wins / younger_fighter_stats.total_fights) * 100, 1) if younger_fighter_stats.total_fights > 0 else 0

    # Calculate favorite win rates by weight class (without age difference filters)
    weight_class_query = f"""
        WITH fight_favorites AS (
            SELECT 
                f.fight_id,
                f.weight_class,
                CASE 
                    WHEN o.home_moneyLine_odds_current_value < o.away_moneyLine_odds_current_value THEN f.fighter_1_id
                    ELSE f.fighter_2_id
                END as favorite_id,
                CASE 
                    WHEN f.fighter_1_winner THEN f.fighter_1_id
                    ELSE f.fighter_2_id
                END as winner_id
            FROM fights f
            JOIN odds o ON f.fight_id = o.fight_id
            JOIN cards c ON f.event_id = c.event_id
            WHERE o.home_moneyLine_odds_current_value IS NOT NULL 
            AND o.away_moneyLine_odds_current_value IS NOT NULL
            AND {filter_condition}
        )
        SELECT 
            weight_class,
            COUNT(*) as total_fights,
            SUM(CASE WHEN winner_id = favorite_id THEN 1 ELSE 0 END) as favorite_wins
        FROM fight_favorites
        GROUP BY weight_class
    """
    weight_class_stats = {}
    for row in db.session.execute(text(weight_class_query)):
        win_rate = round((row.favorite_wins / row.total_fights) * 100, 1) if row.total_fights > 0 else 0
        weight_class_stats[row.weight_class] = {
            'favorite_win_rate': win_rate,
            'total_fights': row.total_fights
        }

    # Calculate women's fights going the distance (without age difference filters)
    womens_distance_query = f"""
        SELECT 
            COUNT(*) as total_fights,
            SUM(CASE WHEN f.end_round = 3 OR f.end_round = 5 THEN 1 ELSE 0 END) as decisions
        FROM fights f
        JOIN athletes f1 ON f.fighter_1_id = f1.id
        JOIN athletes f2 ON f.fighter_2_id = f2.id
        JOIN cards c ON f.event_id = c.event_id
        WHERE f1.gender = 'F' AND f2.gender = 'F'
        AND {filter_condition}
    """
    womens_stats = db.session.execute(text(womens_distance_query)).fetchone()
    womens_distance_rate = round((womens_stats.decisions / womens_stats.total_fights) * 100, 1) if womens_stats.total_fights > 0 else 0

    return render_template('system_checker.html',
                         younger_fighter_win_rate=younger_fighter_win_rate,
                         younger_fighter_stats=younger_fighter_stats,
                         weight_class_stats=weight_class_stats,
                         womens_distance_rate=womens_distance_rate,
                         ufc_only=ufc_only,
                         min_age_diff=min_age_diff,
                         betting_status=betting_status,
                         selected_weight_classes=selected_weight_classes,
                         fight_details=fight_details)

if __name__ == '__main__':
    app.run(debug=True) 