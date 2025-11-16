"""
Betting Analytics Service - Advanced betting intelligence and strategy analysis
Provides comprehensive betting insights including value bets, ROI calculations,
prop bet analysis, and betting system performance tracking
"""

from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import text
from mma_website import db
from mma_website.utils.text_utils import row_to_dict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BettingAnalyticsService:
    """
    Comprehensive betting analytics service for MMA betting intelligence
    """

    def __init__(self):
        self.db_session = db.session

    def get_value_bets(self, min_odds: int = -300, max_odds: int = 200,
                       min_sample_size: int = 10) -> List[Dict[str, Any]]:
        """
        Identify value betting opportunities based on historical performance

        Args:
            min_odds: Minimum odds to consider
            max_odds: Maximum odds to consider
            min_sample_size: Minimum number of fights in category

        Returns:
            List of value bet opportunities with expected value
        """
        query = text("""
            WITH historical_performance AS (
                SELECT
                    CASE
                        WHEN o.home_favorite = 1 THEN
                            CAST(o.home_moneyLine_odds_current_american AS INTEGER)
                        WHEN o.away_favorite = 1 THEN
                            CAST(o.away_moneyLine_odds_current_american AS INTEGER)
                    END as odds_range,
                    COUNT(*) as sample_size,
                    ROUND(AVG(CASE
                        WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1 THEN 1.0
                        WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1 THEN 1.0
                        ELSE 0.0
                    END) * 100, 1) as actual_win_rate,
                    -- Calculate implied probability from odds
                    ROUND(AVG(CASE
                        WHEN o.home_favorite = 1 THEN
                            CASE
                                WHEN CAST(o.home_moneyLine_odds_current_american AS INTEGER) < 0
                                THEN (ABS(CAST(o.home_moneyLine_odds_current_american AS INTEGER)) /
                                     (ABS(CAST(o.home_moneyLine_odds_current_american AS INTEGER)) + 100.0)) * 100
                                ELSE (100.0 / (CAST(o.home_moneyLine_odds_current_american AS INTEGER) + 100.0)) * 100
                            END
                        WHEN o.away_favorite = 1 THEN
                            CASE
                                WHEN CAST(o.away_moneyLine_odds_current_american AS INTEGER) < 0
                                THEN (ABS(CAST(o.away_moneyLine_odds_current_american AS INTEGER)) /
                                     (ABS(CAST(o.away_moneyLine_odds_current_american AS INTEGER)) + 100.0)) * 100
                                ELSE (100.0 / (CAST(o.away_moneyLine_odds_current_american AS INTEGER) + 100.0)) * 100
                            END
                    END), 1) as implied_probability
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                JOIN odds o ON f.fight_id = o.fight_id
                WHERE (o.home_favorite = 1 OR o.away_favorite = 1)
                AND LOWER(c.league) = 'ufc'
                AND f.fighter_1_winner IS NOT NULL
                AND o.home_moneyLine_odds_current_american IS NOT NULL
                AND o.away_moneyLine_odds_current_american IS NOT NULL
                GROUP BY odds_range
                HAVING COUNT(*) >= :min_sample
            )
            SELECT
                *,
                ROUND(actual_win_rate - implied_probability, 1) as edge,
                ROUND(((actual_win_rate / 100.0) *
                       (CASE WHEN odds_range < 0
                             THEN (100.0 / ABS(odds_range))
                             ELSE (odds_range / 100.0) END) - 1) * 100, 1) as expected_roi
            FROM historical_performance
            WHERE odds_range BETWEEN :min_odds AND :max_odds
            AND actual_win_rate > implied_probability
            ORDER BY edge DESC
            LIMIT 10
        """)

        results = self.db_session.execute(
            query,
            {"min_odds": min_odds, "max_odds": max_odds, "min_sample": min_sample_size}
        ).fetchall()

        return [row_to_dict(row) for row in results]

    def get_prop_bet_analysis(self) -> Dict[str, Any]:
        """
        Analyze method of victory (KO/TKO, Submission, Decision) betting performance
        """
        query = text("""
            WITH prop_analysis AS (
                SELECT
                    -- Analyze favorite's method of victory odds
                    f.result_display_name,
                    COUNT(*) as total_fights,

                    -- KO/TKO prop analysis
                    AVG(CASE
                        WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1
                            AND (f.result_display_name LIKE '%KO%' OR f.result_display_name LIKE '%TKO%')
                        THEN o.home_victoryMethod_koTkoDq_decimal
                        WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1
                            AND (f.result_display_name LIKE '%KO%' OR f.result_display_name LIKE '%TKO%')
                        THEN o.away_victoryMethod_koTkoDq_decimal
                    END) as avg_ko_odds_when_hit,

                    -- Submission prop analysis
                    AVG(CASE
                        WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1
                            AND f.result_display_name LIKE '%Submission%'
                        THEN o.home_victoryMethod_submission_decimal
                        WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1
                            AND f.result_display_name LIKE '%Submission%'
                        THEN o.away_victoryMethod_submission_decimal
                    END) as avg_sub_odds_when_hit,

                    -- Decision prop analysis
                    AVG(CASE
                        WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1
                            AND f.result_display_name LIKE '%Decision%'
                        THEN o.home_victoryMethod_points_decimal
                        WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1
                            AND f.result_display_name LIKE '%Decision%'
                        THEN o.away_victoryMethod_points_decimal
                    END) as avg_dec_odds_when_hit,

                    -- Actual frequencies
                    ROUND(SUM(CASE WHEN f.result_display_name LIKE '%KO%' OR f.result_display_name LIKE '%TKO%'
                                  THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 1) as actual_ko_rate,
                    ROUND(SUM(CASE WHEN f.result_display_name LIKE '%Submission%'
                                  THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 1) as actual_sub_rate,
                    ROUND(SUM(CASE WHEN f.result_display_name LIKE '%Decision%'
                                  THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 1) as actual_dec_rate

                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                JOIN odds o ON f.fight_id = o.fight_id
                WHERE (o.home_favorite = 1 OR o.away_favorite = 1)
                AND LOWER(c.league) = 'ufc'
                AND f.fighter_1_winner IS NOT NULL
            )
            SELECT * FROM prop_analysis
        """)

        result = self.db_session.execute(query).fetchone()
        return row_to_dict(result) if result else {}

    def get_betting_system_performance(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Analyze performance of various betting systems/strategies
        """
        systems = []

        # System 1: Always bet favorites
        systems.append(self._analyze_system(
            name="Always Bet Favorites",
            description="Bet the favorite in every fight",
            strategy_sql="""
                SELECT
                    f.fight_id,
                    CASE
                        WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1 THEN 'win'
                        WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1 THEN 'win'
                        ELSE 'loss'
                    END as outcome,
                    CASE
                        WHEN o.home_favorite = 1 THEN CAST(o.home_moneyLine_odds_current_american AS INTEGER)
                        WHEN o.away_favorite = 1 THEN CAST(o.away_moneyLine_odds_current_american AS INTEGER)
                    END as odds
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                JOIN odds o ON f.fight_id = o.fight_id
                WHERE (o.home_favorite = 1 OR o.away_favorite = 1)
                AND LOWER(c.league) = 'ufc'
                AND f.fighter_1_winner IS NOT NULL
                AND o.home_moneyLine_odds_current_american IS NOT NULL
            """
        ))

        # System 2: Bet underdogs (+150 or better)
        systems.append(self._analyze_system(
            name="Value Underdogs",
            description="Bet underdogs with odds of +150 or better",
            strategy_sql="""
                SELECT
                    f.fight_id,
                    CASE
                        WHEN o.home_underdog = 1 AND f.fighter_1_winner = 1 THEN 'win'
                        WHEN o.away_underdog = 1 AND f.fighter_2_winner = 1 THEN 'win'
                        ELSE 'loss'
                    END as outcome,
                    CASE
                        WHEN o.home_underdog = 1 THEN CAST(o.home_moneyLine_odds_current_american AS INTEGER)
                        WHEN o.away_underdog = 1 THEN CAST(o.away_moneyLine_odds_current_american AS INTEGER)
                    END as odds
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                JOIN odds o ON f.fight_id = o.fight_id
                WHERE ((o.home_underdog = 1 AND CAST(o.home_moneyLine_odds_current_american AS INTEGER) >= 150)
                   OR (o.away_underdog = 1 AND CAST(o.away_moneyLine_odds_current_american AS INTEGER) >= 150))
                AND LOWER(c.league) = 'ufc'
                AND f.fighter_1_winner IS NOT NULL
                AND o.home_moneyLine_odds_current_american IS NOT NULL
            """
        ))

        # System 3: Bet moderate favorites (-200 to -100)
        systems.append(self._analyze_system(
            name="Moderate Favorites",
            description="Bet favorites between -100 and -200",
            strategy_sql="""
                SELECT
                    f.fight_id,
                    CASE
                        WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1 THEN 'win'
                        WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1 THEN 'win'
                        ELSE 'loss'
                    END as outcome,
                    CASE
                        WHEN o.home_favorite = 1 THEN CAST(o.home_moneyLine_odds_current_american AS INTEGER)
                        WHEN o.away_favorite = 1 THEN CAST(o.away_moneyLine_odds_current_american AS INTEGER)
                    END as odds
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                JOIN odds o ON f.fight_id = o.fight_id
                WHERE ((o.home_favorite = 1 AND CAST(o.home_moneyLine_odds_current_american AS INTEGER) BETWEEN -200 AND -100)
                   OR (o.away_favorite = 1 AND CAST(o.away_moneyLine_odds_current_american AS INTEGER) BETWEEN -200 AND -100))
                AND LOWER(c.league) = 'ufc'
                AND f.fighter_1_winner IS NOT NULL
                AND o.home_moneyLine_odds_current_american IS NOT NULL
            """
        ))

        # System 4: Bet younger fighter when age gap >= 5 years
        systems.append(self._analyze_system(
            name="Youth Advantage",
            description="Bet the younger fighter when age gap is 5+ years",
            strategy_sql="""
                SELECT
                    f.fight_id,
                    CASE
                        WHEN a1.age < a2.age AND f.fighter_1_winner = 1 THEN 'win'
                        WHEN a2.age < a1.age AND f.fighter_2_winner = 1 THEN 'win'
                        ELSE 'loss'
                    END as outcome,
                    CASE
                        WHEN a1.age < a2.age THEN
                            CASE WHEN o.home_favorite = 1 AND f.fighter_1_id = o.home_athlete_id
                                 THEN CAST(o.home_moneyLine_odds_current_american AS INTEGER)
                                 ELSE CAST(o.away_moneyLine_odds_current_american AS INTEGER)
                            END
                        ELSE
                            CASE WHEN o.home_favorite = 1 AND f.fighter_2_id = o.home_athlete_id
                                 THEN CAST(o.home_moneyLine_odds_current_american AS INTEGER)
                                 ELSE CAST(o.away_moneyLine_odds_current_american AS INTEGER)
                            END
                    END as odds
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                JOIN odds o ON f.fight_id = o.fight_id
                JOIN athletes a1 ON f.fighter_1_id = a1.id
                JOIN athletes a2 ON f.fighter_2_id = a2.id
                WHERE ABS(COALESCE(a1.age, 30) - COALESCE(a2.age, 30)) >= 5
                AND LOWER(c.league) = 'ufc'
                AND f.fighter_1_winner IS NOT NULL
                AND o.home_moneyLine_odds_current_american IS NOT NULL
            """
        ))

        return systems

    def _analyze_system(self, name: str, description: str, strategy_sql: str) -> Dict[str, Any]:
        """Helper method to analyze a betting system's performance"""
        try:
            results = self.db_session.execute(text(strategy_sql)).fetchall()

            if not results:
                return {
                    'name': name,
                    'description': description,
                    'error': 'No data available'
                }

            total_bets = len(results)
            wins = sum(1 for r in results if r.outcome == 'win')
            losses = total_bets - wins
            win_rate = (wins / total_bets * 100) if total_bets > 0 else 0

            # Calculate profit/loss (assuming $100 bets)
            total_profit = 0
            for row in results:
                # Skip if odds are None
                if row.odds is None:
                    continue

                if row.outcome == 'win':
                    if row.odds < 0:
                        # Favorite odds: profit = 100 / (abs(odds) / 100)
                        total_profit += (100 / (abs(row.odds) / 100))
                    else:
                        # Underdog odds: profit = odds
                        total_profit += row.odds
                else:
                    total_profit -= 100

            roi = (total_profit / (total_bets * 100) * 100) if total_bets > 0 else 0

            return {
                'name': name,
                'description': description,
                'total_bets': total_bets,
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 1),
                'total_profit': round(total_profit, 2),
                'roi': round(roi, 1),
                'avg_bet_profit': round(total_profit / total_bets, 2) if total_bets > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error analyzing system '{name}': {e}")
            return {
                'name': name,
                'description': description,
                'error': str(e)
            }

    def get_bookmaker_comparison(self) -> List[Dict[str, Any]]:
        """Compare odds and accuracy across different bookmakers"""
        query = text("""
            SELECT
                o.provider_name,
                COUNT(*) as total_fights,
                ROUND(AVG(CASE
                    WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1 THEN 1.0
                    WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1 THEN 1.0
                    ELSE 0.0
                END) * 100, 1) as favorite_accuracy,
                ROUND(AVG(ABS(CAST(o.home_moneyLine_odds_current_american AS INTEGER))), 0) as avg_favorite_line,
                COUNT(DISTINCT f.fight_id) as fights_covered
            FROM fights f
            JOIN cards c ON f.event_id = c.event_id
            JOIN odds o ON f.fight_id = o.fight_id
            WHERE (o.home_favorite = 1 OR o.away_favorite = 1)
            AND LOWER(c.league) = 'ufc'
            AND f.fighter_1_winner IS NOT NULL
            AND o.provider_name IS NOT NULL
            AND o.home_moneyLine_odds_current_american IS NOT NULL
            GROUP BY o.provider_name
            HAVING COUNT(*) >= 100
            ORDER BY favorite_accuracy DESC
        """)

        results = self.db_session.execute(query).fetchall()
        return [row_to_dict(row) for row in results]

    def get_rounds_betting_analysis(self) -> Dict[str, Any]:
        """Analyze over/under rounds betting performance"""
        query = text("""
            WITH rounds_data AS (
                SELECT
                    f.fight_id,
                    f.end_round,
                    f.rounds_format,
                    o.rounds_over_under_value,
                    o.rounds_over_decimal,
                    o.rounds_under_decimal,
                    CASE
                        WHEN f.end_round IS NULL THEN f.rounds_format
                        ELSE CAST(f.end_round AS INTEGER)
                    END as actual_rounds,
                    CASE
                        WHEN o.rounds_over_under_value IS NOT NULL THEN
                            CAST(SUBSTR(o.rounds_over_under_value, 1, 3) AS FLOAT)
                    END as line
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                JOIN odds o ON f.fight_id = o.fight_id
                WHERE LOWER(c.league) = 'ufc'
                AND o.rounds_over_under_value IS NOT NULL
                AND f.rounds_format IS NOT NULL
            )
            SELECT
                COUNT(*) as total_bets_available,
                ROUND(AVG(CASE WHEN actual_rounds > line THEN 1.0 ELSE 0.0 END) * 100, 1) as over_hit_rate,
                ROUND(AVG(CASE WHEN actual_rounds < line THEN 1.0 ELSE 0.0 END) * 100, 1) as under_hit_rate,
                ROUND(AVG(CASE WHEN actual_rounds = line THEN 1.0 ELSE 0.0 END) * 100, 1) as push_rate,
                ROUND(AVG(line), 1) as avg_line,
                ROUND(AVG(actual_rounds), 1) as avg_actual_rounds,
                ROUND(AVG(rounds_over_decimal), 2) as avg_over_odds,
                ROUND(AVG(rounds_under_decimal), 2) as avg_under_odds
            FROM rounds_data
            WHERE line IS NOT NULL
        """)

        result = self.db_session.execute(query).fetchone()
        return row_to_dict(result) if result else {}

    def get_historical_trends(self, days_back: int = 365) -> Dict[str, Any]:
        """
        Analyze betting trends over time
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)

        query = text("""
            WITH monthly_stats AS (
                SELECT
                    strftime('%Y-%m', c.date) as month,
                    COUNT(*) as total_fights,
                    ROUND(AVG(CASE
                        WHEN o.home_favorite = 1 AND f.fighter_1_winner = 1 THEN 1.0
                        WHEN o.away_favorite = 1 AND f.fighter_2_winner = 1 THEN 1.0
                        ELSE 0.0
                    END) * 100, 1) as favorite_win_rate,
                    ROUND(AVG(ABS(CAST(o.home_moneyLine_odds_current_american AS INTEGER))), 0) as avg_favorite_line,
                    ROUND(AVG(CASE
                        WHEN f.result_display_name LIKE '%KO%' OR f.result_display_name LIKE '%TKO%'
                             OR f.result_display_name LIKE '%Submission%'
                        THEN 1.0 ELSE 0.0
                    END) * 100, 1) as finish_rate
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                JOIN odds o ON f.fight_id = o.fight_id
                WHERE (o.home_favorite = 1 OR o.away_favorite = 1)
                AND LOWER(c.league) = 'ufc'
                AND f.fighter_1_winner IS NOT NULL
                AND c.date >= date(:cutoff_date)
                GROUP BY month
                ORDER BY month DESC
                LIMIT 12
            )
            SELECT * FROM monthly_stats
            ORDER BY month ASC
        """)

        results = self.db_session.execute(query, {"cutoff_date": cutoff_date.strftime('%Y-%m-%d')}).fetchall()
        return [row_to_dict(row) for row in results]


# Global service instance
betting_analytics_service = BettingAnalyticsService()
