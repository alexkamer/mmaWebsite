from sqlalchemy import text
from mma_website import db
from mma_website.utils.text_utils import row_to_dict

def get_fighter_data(fighter_id, filters=None):
    """Get fighter data with filters for tale of the tape"""
    if filters is None:
        filters = {
            'promotion': 'all',
            'rounds_format': 'all',
            'fight_type': 'all',
            'weight_class': 'all',
            'odds_type': 'all'
        }
    
    db_session = db.session
    
    # Get fighter details
    fighter = db_session.execute(text("""
        SELECT *
        FROM athletes
        WHERE id = :fighter_id
    """), {"fighter_id": fighter_id}).fetchone()
    
    if fighter:
        fighter_dict = row_to_dict(fighter)
        
        # Get fighter's record
        wins = db_session.execute(text("""
            SELECT COUNT(*) as wins
            FROM fights
            WHERE (fighter_1_id = :fighter_id AND fighter_1_winner = 1)
            OR (fighter_2_id = :fighter_id AND fighter_2_winner = 1)
        """), {"fighter_id": fighter_id}).scalar()
        
        losses = db_session.execute(text("""
            SELECT COUNT(*) as losses
            FROM fights
            WHERE (fighter_1_id = :fighter_id AND fighter_1_winner = 0)
            OR (fighter_2_id = :fighter_id AND fighter_2_winner = 0)
            AND NOT (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
        """), {"fighter_id": fighter_id}).scalar()
        
        draws = db_session.execute(text("""
            SELECT COUNT(*) as draws
            FROM fights
            WHERE (fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id)
            AND (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
        """), {"fighter_id": fighter_id}).scalar()
        
        fighter_dict['record'] = f"{wins}-{losses}-{draws}"
        
        # Build query parameters
        filter_params = {"fighter_id": fighter_id}
        
        # Define the base query for fight history
        base_fight_history_query = """
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
                END as takedowns_attempted,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN l1.score_value
                    ELSE l2.score_value
                END as fighter_score,
                CASE 
                    WHEN f.fighter_1_id = :fighter_id THEN l2.score_value
                    ELSE l1.score_value
                END as opponent_score
            FROM fights f
            JOIN athletes a1 ON f.fighter_1_id = a1.id
            JOIN athletes a2 ON f.fighter_2_id = a2.id
            JOIN cards c ON f.event_id = c.event_id
            LEFT JOIN latest_odds o ON f.fight_id = o.fight_id AND o.rn = 1
            LEFT JOIN statistics_for_fights s1 ON f.event_id = s1.event_id AND f.fighter_1_id = s1.athlete_id
            LEFT JOIN statistics_for_fights s2 ON f.event_id = s2.event_id AND f.fighter_2_id = s2.athlete_id
            LEFT JOIN linescores l1 ON f.fight_id = l1.fight_id AND f.fighter_1_id = l1.fighter_id
            LEFT JOIN linescores l2 ON f.fight_id = l2.fight_id AND f.fighter_2_id = l2.fighter_id
            WHERE (f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id)
        """
        
        # Define the base query for filtered stats
        base_filtered_stats_query = """
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
        """
        
        # Conditionally add filter clauses
        additional_conditions = []
        
        if filters['promotion'] != 'all':
            additional_conditions.append("c.league = :promotion")
            filter_params['promotion'] = filters['promotion']
        
        if filters['rounds_format'] != 'all':
            additional_conditions.append("CAST(f.rounds_format AS INTEGER) = :rounds_format")
            filter_params['rounds_format'] = int(filters['rounds_format'])
        
        if filters['weight_class'] != 'all':
            additional_conditions.append("f.weight_class = :weight_class")
            filter_params['weight_class'] = filters['weight_class']
        
        if filters['odds_type'] != 'all':
            if filters['odds_type'] == 'favorite':
                additional_conditions.append("""
                    CASE 
                        WHEN f.fighter_1_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american < 0
                        WHEN f.fighter_1_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american < 0
                        WHEN f.fighter_2_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american < 0
                        WHEN f.fighter_2_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american < 0
                    END
                """)
            elif filters['odds_type'] == 'underdog':
                additional_conditions.append("""
                    CASE 
                        WHEN f.fighter_1_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american > 0
                        WHEN f.fighter_1_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_1_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american > 0
                        WHEN f.fighter_2_id = :fighter_id AND o.home_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.home_moneyLine_odds_current_american > 0
                        WHEN f.fighter_2_id = :fighter_id AND o.away_athlete_id = CAST(f.fighter_2_id AS VARCHAR) THEN o.away_moneyLine_odds_current_american > 0
                    END
                """)
        
        # Build complete queries with conditions
        fight_history_query = base_fight_history_query
        filtered_stats_query = base_filtered_stats_query
        
        # Add conditions if they exist
        if additional_conditions:
            condition_clause = " AND " + " AND ".join(additional_conditions)
            fight_history_query += condition_clause
            filtered_stats_query += condition_clause
        
        # Complete the filtered stats query with the closing part
        filtered_stats_query += """
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
        """
        
        # Add ORDER BY clause to fight history query
        fight_history_query += " ORDER BY c.date DESC"
        
        # Execute the safe parameterized queries
        fight_history = db_session.execute(text(fight_history_query), filter_params).fetchall()
        fighter_dict['fight_history'] = [row_to_dict(fight) for fight in fight_history]
        
        filtered_stats = db_session.execute(text(filtered_stats_query), filter_params).fetchone()
        
        if filtered_stats:
            filtered_record = row_to_dict(filtered_stats)
            fighter_dict['filtered_record'] = f"{filtered_record['wins']}-{filtered_record['losses']}-{filtered_record['draws']}"
            fighter_dict['filtered_decisions'] = filtered_record['decisions']
            fighter_dict['filtered_total_fights'] = filtered_record['total_fights']
            fighter_dict['filtered_ko_record'] = f"{filtered_record['ko_wins']}-{filtered_record['ko_losses']}"
            fighter_dict['filtered_sub_record'] = f"{filtered_record['sub_wins']}-{filtered_record['sub_losses']}"
        
        # Get unique promotions, weight classes, and rounds formats for filters
        promotions = db_session.execute(text("""
            SELECT DISTINCT c.league
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            WHERE f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id
            ORDER BY c.league
        """), {"fighter_id": fighter_id}).fetchall()
        fighter_dict['promotions'] = [row[0] for row in promotions]
        
        weight_classes = db_session.execute(text("""
            SELECT DISTINCT weight_class
            FROM fights
            WHERE fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id
            ORDER BY weight_class
        """), {"fighter_id": fighter_id}).fetchall()
        fighter_dict['weight_classes'] = [row[0] for row in weight_classes]
        
        rounds_formats = db_session.execute(text("""
            SELECT DISTINCT rounds_format
            FROM fights
            WHERE fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id
            ORDER BY rounds_format
        """), {"fighter_id": fighter_id}).fetchall()
        fighter_dict['rounds_formats'] = [row[0] for row in rounds_formats]
        
        # Store the current filters
        fighter_dict['current_filters'] = filters
        
        return fighter_dict
    
    return None