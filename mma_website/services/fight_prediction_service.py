"""
Fight Prediction Service - AI-powered fight analysis and predictions
Analyzes fighter data comprehensively including weight class performance,
physical attributes, opponent skill levels, and career trends
"""

from typing import Dict, List, Any, Optional
from sqlalchemy import text
from mma_website import db
from mma_website.utils.text_utils import row_to_dict
import logging

logger = logging.getLogger(__name__)

class FightPredictionService:
    """Comprehensive AI-powered fight prediction and analysis service"""
    
    def __init__(self):
        pass
    
    def generate_fight_prediction(self, fighter1_id: str, fighter2_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive AI fight prediction based on multiple analytical factors
        
        Args:
            fighter1_id: First fighter's ID
            fighter2_id: Second fighter's ID
            
        Returns:
            Dict containing detailed fight prediction and analysis
        """
        try:
            print(f"\n🔍 PREDICTION DEBUG: Starting prediction for Fighter {fighter1_id} vs Fighter {fighter2_id}")
            
            # Get comprehensive fighter data
            print(f"📊 PREDICTION DEBUG: Fetching comprehensive data for both fighters...")
            fighter1_data = self._get_comprehensive_fighter_data(fighter1_id)
            fighter2_data = self._get_comprehensive_fighter_data(fighter2_id)
            
            if not fighter1_data or not fighter2_data:
                print(f"❌ PREDICTION DEBUG: Missing fighter data - F1: {bool(fighter1_data)}, F2: {bool(fighter2_data)}")
                return {
                    'success': False,
                    'error': 'Unable to retrieve comprehensive fighter data'
                }
            
            print(f"✅ PREDICTION DEBUG: Fighter data retrieved successfully")
            print(f"   Fighter 1: {fighter1_data['basic'].get('full_name', 'Unknown')}")
            print(f"   Fighter 2: {fighter2_data['basic'].get('full_name', 'Unknown')}")
            print(f"   F1 Career Fights: {fighter1_data['career_stats'].get('total_fights', 0)}")
            print(f"   F2 Career Fights: {fighter2_data['career_stats'].get('total_fights', 0)}")
            
            # Analyze all key factors
            analysis = {
                'weight_class_analysis': self._analyze_weight_class_performance(fighter1_data, fighter2_data),
                'physical_analysis': self._analyze_physical_attributes(fighter1_data, fighter2_data),
                'opponent_quality_analysis': self._analyze_opponent_quality(fighter1_data, fighter2_data),
                'career_trends_analysis': self._analyze_career_trends(fighter1_data, fighter2_data),
                'finishing_ability_analysis': self._analyze_finishing_ability(fighter1_data, fighter2_data),
                'recent_form_analysis': self._analyze_recent_form(fighter1_data, fighter2_data),
                'experience_analysis': self._analyze_experience_factors(fighter1_data, fighter2_data)
            }
            
            # Generate tactical prediction
            prediction = self._generate_tactical_prediction(fighter1_data, fighter2_data, analysis)
            
            # Calculate confidence score
            confidence = self._calculate_prediction_confidence(analysis)
            
            print(f"\n🏁 PREDICTION SUMMARY DEBUG:")
            print(f"   ✅ Prediction Generation: SUCCESSFUL")
            print(f"   🎯 Winner: {prediction['predicted_winner']}")
            print(f"   📊 Confidence: {confidence['level']} ({confidence['score']:.1%})")
            print(f"   🔧 Key Factors: {len(self._extract_key_factors(analysis))} identified")
            print(f"   📈 Data Quality: {confidence['factors_considered']} factors analyzed")
            print(f"\n" + "="*80)
            
            return {
                'success': True,
                'fighter1': fighter1_data['basic'],
                'fighter2': fighter2_data['basic'],
                'analysis': analysis,
                'prediction': prediction,
                'confidence': confidence,
                'key_factors': self._extract_key_factors(analysis)
            }
            
        except Exception as e:
            logger.error(f"Error generating fight prediction: {e}")
            return {
                'success': False,
                'error': f'Prediction analysis failed: {str(e)}'
            }
    
    def _get_comprehensive_fighter_data(self, fighter_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive fighter data including all performance metrics"""
        db_session = db.session
        
        try:
            # Basic fighter info
            basic_info = db_session.execute(text("""
                SELECT id, full_name, nickname, weight_class, height, weight, reach, 
                       age, stance, association, headshot_url
                FROM athletes
                WHERE id = :fighter_id
            """), {"fighter_id": fighter_id}).fetchone()
            
            if not basic_info:
                return None
                
            basic_data = row_to_dict(basic_info)
            
            # Career statistics across all promotions
            career_stats = db_session.execute(text("""
                WITH fighter_stats AS (
                    SELECT 
                        COUNT(*) as total_fights,
                        SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN won = 0 AND result_type NOT IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as losses,
                        SUM(CASE WHEN result_type IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as draws,
                        SUM(CASE WHEN won = 1 AND (result_type LIKE '%KO%' OR result_type LIKE '%TKO%') THEN 1 ELSE 0 END) as ko_wins,
                        SUM(CASE WHEN won = 1 AND result_type LIKE '%Submission%' THEN 1 ELSE 0 END) as sub_wins,
                        SUM(CASE WHEN won = 1 AND result_type LIKE '%Decision%' THEN 1 ELSE 0 END) as dec_wins,
                        SUM(CASE WHEN won = 0 AND (result_type LIKE '%KO%' OR result_type LIKE '%TKO%') THEN 1 ELSE 0 END) as kod_losses,
                        SUM(CASE WHEN won = 0 AND result_type LIKE '%Submission%' THEN 1 ELSE 0 END) as sub_losses,
                        AVG(CASE WHEN f.end_round IS NOT NULL THEN f.end_round ELSE 3.0 END) as avg_fight_duration
                    FROM (
                        SELECT 
                            fighter_1_winner as won,
                            result_display_name as result_type,
                            end_round
                        FROM fights f
                        WHERE fighter_1_id = :fighter_id
                        UNION ALL
                        SELECT 
                            fighter_2_winner as won,
                            result_display_name as result_type,
                            end_round
                        FROM fights f
                        WHERE fighter_2_id = :fighter_id
                    ) combined
                    JOIN fights f ON 1=1
                )
                SELECT * FROM fighter_stats
            """), {"fighter_id": fighter_id}).fetchone()
            
            # UFC-specific performance
            ufc_stats = db_session.execute(text("""
                WITH ufc_stats AS (
                    SELECT 
                        COUNT(*) as ufc_fights,
                        SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as ufc_wins,
                        SUM(CASE WHEN won = 0 AND result_type NOT IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as ufc_losses,
                        SUM(CASE WHEN won = 1 AND (result_type LIKE '%KO%' OR result_type LIKE '%TKO%') THEN 1 ELSE 0 END) as ufc_ko_wins,
                        SUM(CASE WHEN won = 1 AND result_type LIKE '%Submission%' THEN 1 ELSE 0 END) as ufc_sub_wins
                    FROM (
                        SELECT 
                            fighter_1_winner as won,
                            result_display_name as result_type
                        FROM fights f
                        JOIN cards c ON f.event_id = c.event_id
                        WHERE fighter_1_id = :fighter_id AND LOWER(c.league) = 'ufc'
                        UNION ALL
                        SELECT 
                            fighter_2_winner as won,
                            result_display_name as result_type
                        FROM fights f
                        JOIN cards c ON f.event_id = c.event_id
                        WHERE fighter_2_id = :fighter_id AND LOWER(c.league) = 'ufc'
                    ) combined
                )
                SELECT * FROM ufc_stats
            """), {"fighter_id": fighter_id}).fetchone()
            
            # Weight class performance
            weight_class_stats = db_session.execute(text("""
                WITH wc_stats AS (
                    SELECT 
                        weight_class,
                        COUNT(*) as wc_fights,
                        SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wc_wins,
                        SUM(CASE WHEN won = 0 THEN 1 ELSE 0 END) as wc_losses
                    FROM (
                        SELECT 
                            fighter_1_winner as won,
                            f.weight_class
                        FROM fights f
                        WHERE fighter_1_id = :fighter_id
                        UNION ALL
                        SELECT 
                            fighter_2_winner as won,
                            f.weight_class
                        FROM fights f
                        WHERE fighter_2_id = :fighter_id
                    ) combined
                    WHERE weight_class IS NOT NULL
                    GROUP BY weight_class
                )
                SELECT * FROM wc_stats ORDER BY wc_fights DESC
            """), {"fighter_id": fighter_id}).fetchall()
            
            # Recent fights (last 5)
            recent_fights = db_session.execute(text("""
                SELECT 
                    c.date,
                    c.event_name,
                    c.league,
                    CASE WHEN f.fighter_1_id = :fighter_id THEN f.fighter_1_winner ELSE f.fighter_2_winner END as won,
                    CASE WHEN f.fighter_1_id = :fighter_id THEN a2.full_name ELSE a1.full_name END as opponent_name,
                    f.result_display_name,
                    f.end_round,
                    f.end_time,
                    f.weight_class
                FROM fights f
                JOIN cards c ON f.event_id = c.event_id
                JOIN athletes a1 ON f.fighter_1_id = a1.id
                JOIN athletes a2 ON f.fighter_2_id = a2.id
                WHERE (f.fighter_1_id = :fighter_id OR f.fighter_2_id = :fighter_id)
                ORDER BY c.date DESC
                LIMIT 5
            """), {"fighter_id": fighter_id}).fetchall()
            
            # Opponent analysis - get quality of opponents
            opponent_quality = db_session.execute(text("""
                WITH opponent_records AS (
                    SELECT 
                        opponent_id,
                        opponent_name,
                        SUM(opp_wins) as opponent_career_wins,
                        SUM(opp_losses) as opponent_career_losses,
                        COUNT(*) as fights_count
                    FROM (
                        -- When fighter was fighter_1
                        SELECT 
                            a2.id as opponent_id,
                            a2.full_name as opponent_name,
                            opp_stats.wins as opp_wins,
                            opp_stats.losses as opp_losses
                        FROM fights f
                        JOIN athletes a2 ON f.fighter_2_id = a2.id
                        JOIN (
                            SELECT 
                                fighter_id,
                                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                                SUM(CASE WHEN won = 0 THEN 1 ELSE 0 END) as losses
                            FROM (
                                SELECT fighter_1_id as fighter_id, fighter_1_winner as won FROM fights
                                UNION ALL
                                SELECT fighter_2_id as fighter_id, fighter_2_winner as won FROM fights
                            ) all_fights
                            GROUP BY fighter_id
                        ) opp_stats ON a2.id = opp_stats.fighter_id
                        WHERE f.fighter_1_id = :fighter_id
                        
                        UNION ALL
                        
                        -- When fighter was fighter_2
                        SELECT 
                            a1.id as opponent_id,
                            a1.full_name as opponent_name,
                            opp_stats.wins as opp_wins,
                            opp_stats.losses as opp_losses
                        FROM fights f
                        JOIN athletes a1 ON f.fighter_1_id = a1.id
                        JOIN (
                            SELECT 
                                fighter_id,
                                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                                SUM(CASE WHEN won = 0 THEN 1 ELSE 0 END) as losses
                            FROM (
                                SELECT fighter_1_id as fighter_id, fighter_1_winner as won FROM fights
                                UNION ALL
                                SELECT fighter_2_id as fighter_id, fighter_2_winner as won FROM fights
                            ) all_fights
                            GROUP BY fighter_id
                        ) opp_stats ON a1.id = opp_stats.fighter_id
                        WHERE f.fighter_2_id = :fighter_id
                    ) combined
                    GROUP BY opponent_id, opponent_name
                )
                SELECT 
                    AVG(CASE WHEN opponent_career_wins + opponent_career_losses > 0 
                        THEN CAST(opponent_career_wins AS FLOAT) / (opponent_career_wins + opponent_career_losses) 
                        ELSE 0 END) as avg_opponent_win_rate,
                    AVG(opponent_career_wins + opponent_career_losses) as avg_opponent_experience,
                    COUNT(*) as total_unique_opponents
                FROM opponent_records
            """), {"fighter_id": fighter_id}).fetchone()
            
            return {
                'basic': basic_data,
                'career_stats': row_to_dict(career_stats) if career_stats else {},
                'ufc_stats': row_to_dict(ufc_stats) if ufc_stats else {},
                'weight_class_stats': [row_to_dict(wcs) for wcs in weight_class_stats],
                'recent_fights': [row_to_dict(rf) for rf in recent_fights],
                'opponent_quality': row_to_dict(opponent_quality) if opponent_quality else {}
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive fighter data for {fighter_id}: {e}")
            return None
    
    def _analyze_weight_class_performance(self, fighter1_data: Dict, fighter2_data: Dict) -> Dict[str, Any]:
        """Analyze performance in specific weight classes"""
        print(f"\n📊 WEIGHT CLASS ANALYSIS DEBUG:")
        
        f1_wc_stats = fighter1_data.get('weight_class_stats', [])
        f2_wc_stats = fighter2_data.get('weight_class_stats', [])
        
        print(f"   Fighter 1 Weight Class Stats: {len(f1_wc_stats)} divisions")
        print(f"   Fighter 2 Weight Class Stats: {len(f2_wc_stats)} divisions")
        
        # Get primary weight class for each fighter
        f1_primary_wc = f1_wc_stats[0] if f1_wc_stats else {}
        f2_primary_wc = f2_wc_stats[0] if f2_wc_stats else {}
        
        if f1_primary_wc:
            print(f"   F1 Primary Division: {f1_primary_wc.get('weight_class', 'N/A')} ({f1_primary_wc.get('wc_fights', 0)} fights)")
        if f2_primary_wc:
            print(f"   F2 Primary Division: {f2_primary_wc.get('weight_class', 'N/A')} ({f2_primary_wc.get('wc_fights', 0)} fights)")
        
        f1_wc_win_rate = 0
        if f1_primary_wc.get('wc_fights', 0) > 0:
            f1_wc_win_rate = f1_primary_wc.get('wc_wins', 0) / f1_primary_wc.get('wc_fights', 1)
        
        f2_wc_win_rate = 0
        if f2_primary_wc.get('wc_fights', 0) > 0:
            f2_wc_win_rate = f2_primary_wc.get('wc_wins', 0) / f2_primary_wc.get('wc_fights', 1)
        
        print(f"   F1 Weight Class Win Rate: {f1_wc_win_rate:.1%} ({f1_primary_wc.get('wc_wins', 0)}-{f1_primary_wc.get('wc_losses', 0)})")
        print(f"   F2 Weight Class Win Rate: {f2_wc_win_rate:.1%} ({f2_primary_wc.get('wc_wins', 0)}-{f2_primary_wc.get('wc_losses', 0)})")
        
        advantage = 'fighter1' if f1_wc_win_rate > f2_wc_win_rate else 'fighter2' if f2_wc_win_rate > f1_wc_win_rate else 'even'
        print(f"   🏆 Weight Class Advantage: {advantage}")
        
        return {
            'fighter1_weight_class_record': f"{f1_primary_wc.get('wc_wins', 0)}-{f1_primary_wc.get('wc_losses', 0)}",
            'fighter2_weight_class_record': f"{f2_primary_wc.get('wc_wins', 0)}-{f2_primary_wc.get('wc_losses', 0)}",
            'fighter1_wc_win_rate': f1_wc_win_rate,
            'fighter2_wc_win_rate': f2_wc_win_rate,
            'weight_class_advantage': advantage,
            'fighter1_wc_experience': f1_primary_wc.get('wc_fights', 0),
            'fighter2_wc_experience': f2_primary_wc.get('wc_fights', 0)
        }
    
    def _analyze_physical_attributes(self, fighter1_data: Dict, fighter2_data: Dict) -> Dict[str, Any]:
        """Analyze physical matchup including reach, height, age factors"""
        print(f"\n🥊 PHYSICAL ATTRIBUTES ANALYSIS DEBUG:")
        
        f1_basic = fighter1_data.get('basic', {})
        f2_basic = fighter2_data.get('basic', {})
        
        # Parse physical attributes safely
        f1_height = self._parse_height(f1_basic.get('height'))
        f2_height = self._parse_height(f2_basic.get('height'))
        f1_reach = self._parse_reach(f1_basic.get('reach'))
        f2_reach = self._parse_reach(f2_basic.get('reach'))
        f1_age = f1_basic.get('age', 0) or 0
        f2_age = f2_basic.get('age', 0) or 0
        
        print(f"   F1 Physical: Height={f1_basic.get('height', 'N/A')} ({f1_height}in), Reach={f1_basic.get('reach', 'N/A')} ({f1_reach}in), Age={f1_age}")
        print(f"   F2 Physical: Height={f2_basic.get('height', 'N/A')} ({f2_height}in), Reach={f2_basic.get('reach', 'N/A')} ({f2_reach}in), Age={f2_age}")
        
        height_diff = f1_height - f2_height if f1_height and f2_height else 0
        reach_diff = f1_reach - f2_reach if f1_reach and f2_reach else 0
        age_diff = f1_age - f2_age
        
        print(f"   Differences: Height={height_diff:+.1f}in, Reach={reach_diff:+.1f}in, Age={age_diff:+.1f}yrs")
        
        height_adv = 'fighter1' if height_diff > 2 else 'fighter2' if height_diff < -2 else 'even'
        reach_adv = 'fighter1' if reach_diff > 2 else 'fighter2' if reach_diff < -2 else 'even'
        age_adv = 'fighter2' if age_diff > 3 else 'fighter1' if age_diff < -3 else 'even'
        
        f1_prime = 25 <= f1_age <= 33
        f2_prime = 25 <= f2_age <= 33
        
        print(f"   Physical Prime: F1={f1_prime}, F2={f2_prime}")
        print(f"   🏆 Advantages - Height: {height_adv}, Reach: {reach_adv}, Age: {age_adv}")
        
        return {
            'height_advantage': height_adv,
            'reach_advantage': reach_adv,
            'age_advantage': age_adv,
            'height_difference_inches': height_diff,
            'reach_difference_inches': reach_diff,
            'age_difference_years': age_diff,
            'fighter1_physical_prime': f1_prime,
            'fighter2_physical_prime': f2_prime
        }
    
    def _analyze_opponent_quality(self, fighter1_data: Dict, fighter2_data: Dict) -> Dict[str, Any]:
        """Analyze the quality of opponents each fighter has faced"""
        print(f"\n🎯 OPPONENT QUALITY ANALYSIS DEBUG:")
        
        f1_opp = fighter1_data.get('opponent_quality', {})
        f2_opp = fighter2_data.get('opponent_quality', {})
        
        f1_avg_opp_rate = f1_opp.get('avg_opponent_win_rate', 0) or 0
        f2_avg_opp_rate = f2_opp.get('avg_opponent_win_rate', 0) or 0
        f1_avg_opp_exp = f1_opp.get('avg_opponent_experience', 0) or 0
        f2_avg_opp_exp = f2_opp.get('avg_opponent_experience', 0) or 0
        f1_total_opps = f1_opp.get('total_unique_opponents', 0) or 0
        f2_total_opps = f2_opp.get('total_unique_opponents', 0) or 0
        
        print(f"   F1 Opponent Quality: Win Rate={f1_avg_opp_rate:.1%}, Avg Experience={f1_avg_opp_exp:.1f} fights, Total Opponents={f1_total_opps}")
        print(f"   F2 Opponent Quality: Win Rate={f2_avg_opp_rate:.1%}, Avg Experience={f2_avg_opp_exp:.1f} fights, Total Opponents={f2_total_opps}")
        
        sos_diff = abs(f1_avg_opp_rate - f2_avg_opp_rate)
        opp_advantage = 'fighter1' if f1_avg_opp_rate > f2_avg_opp_rate else 'fighter2' if f2_avg_opp_rate > f1_avg_opp_rate else 'even'
        
        print(f"   Strength of Schedule Difference: {sos_diff:.1%}")
        print(f"   🏆 Opponent Quality Advantage: {opp_advantage}")
        
        return {
            'fighter1_avg_opponent_win_rate': f1_avg_opp_rate,
            'fighter2_avg_opponent_win_rate': f2_avg_opp_rate,
            'fighter1_avg_opponent_experience': f1_avg_opp_exp,
            'fighter2_avg_opponent_experience': f2_avg_opp_exp,
            'opponent_quality_advantage': opp_advantage,
            'strength_of_schedule_difference': sos_diff
        }
    
    def _analyze_career_trends(self, fighter1_data: Dict, fighter2_data: Dict) -> Dict[str, Any]:
        """Analyze career trajectory and trends"""
        print(f"\n📈 CAREER TRENDS ANALYSIS DEBUG:")
        
        f1_recent = fighter1_data.get('recent_fights', [])
        f2_recent = fighter2_data.get('recent_fights', [])
        
        print(f"   F1 Recent Fights Available: {len(f1_recent)}")
        print(f"   F2 Recent Fights Available: {len(f2_recent)}")
        
        # Calculate recent form (last 3 fights)
        f1_recent_record = sum(1 for f in f1_recent[:3] if f.get('won'))
        f2_recent_record = sum(1 for f in f2_recent[:3] if f.get('won'))
        
        print(f"   F1 Last 3 Fights: {f1_recent_record}-{3-f1_recent_record}")
        print(f"   F2 Last 3 Fights: {f2_recent_record}-{3-f2_recent_record}")
        
        # Calculate win streaks
        f1_streak = self._calculate_streak(f1_recent)
        f2_streak = self._calculate_streak(f2_recent)
        
        print(f"   F1 Current Streak: {f1_streak['count']} {f1_streak['type']}{'s' if f1_streak['count'] != 1 else ''}")
        print(f"   F2 Current Streak: {f2_streak['count']} {f2_streak['type']}{'s' if f2_streak['count'] != 1 else ''}")
        
        momentum_advantage = 'fighter1' if f1_recent_record > f2_recent_record else 'fighter2' if f2_recent_record > f1_recent_record else 'even'
        print(f"   🏆 Momentum Advantage: {momentum_advantage}")
        
        return {
            'fighter1_recent_record': f"{f1_recent_record}-{3-f1_recent_record}",
            'fighter2_recent_record': f"{f2_recent_record}-{3-f2_recent_record}",
            'fighter1_current_streak': f1_streak,
            'fighter2_current_streak': f2_streak,
            'momentum_advantage': momentum_advantage
        }
    
    def _analyze_finishing_ability(self, fighter1_data: Dict, fighter2_data: Dict) -> Dict[str, Any]:
        """Analyze finishing rates and defensive vulnerabilities"""
        print(f"\n💥 FINISHING ABILITY ANALYSIS DEBUG:")
        
        f1_career = fighter1_data.get('career_stats', {})
        f2_career = fighter2_data.get('career_stats', {})
        
        # Finishing rates (finishes per win)
        f1_finish_rate = 0
        f2_finish_rate = 0
        f1_finished_rate = 0
        f2_finished_rate = 0
        
        f1_ko_wins = f1_career.get('ko_wins', 0)
        f1_sub_wins = f1_career.get('sub_wins', 0)
        f1_wins = f1_career.get('wins', 0)
        f1_losses = f1_career.get('losses', 0)
        f1_kod_losses = f1_career.get('kod_losses', 0)
        f1_sub_losses = f1_career.get('sub_losses', 0)
        
        f2_ko_wins = f2_career.get('ko_wins', 0)
        f2_sub_wins = f2_career.get('sub_wins', 0)
        f2_wins = f2_career.get('wins', 0)
        f2_losses = f2_career.get('losses', 0)
        f2_kod_losses = f2_career.get('kod_losses', 0)
        f2_sub_losses = f2_career.get('sub_losses', 0)
        
        if f1_wins > 0:
            f1_finish_rate = (f1_ko_wins + f1_sub_wins) / f1_wins
        
        if f2_wins > 0:
            f2_finish_rate = (f2_ko_wins + f2_sub_wins) / f2_wins
        
        if f1_losses > 0:
            f1_finished_rate = (f1_kod_losses + f1_sub_losses) / f1_losses
        
        if f2_losses > 0:
            f2_finished_rate = (f2_kod_losses + f2_sub_losses) / f2_losses
        
        print(f"   F1 Finish Stats: {f1_ko_wins} KOs + {f1_sub_wins} Subs = {f1_ko_wins + f1_sub_wins}/{f1_wins} wins ({f1_finish_rate:.1%})")
        print(f"   F2 Finish Stats: {f2_ko_wins} KOs + {f2_sub_wins} Subs = {f2_ko_wins + f2_sub_wins}/{f2_wins} wins ({f2_finish_rate:.1%})")
        print(f"   F1 Finished Rate: {f1_kod_losses} KO/TKOs + {f1_sub_losses} Sub losses = {f1_kod_losses + f1_sub_losses}/{f1_losses} losses ({f1_finished_rate:.1%})")
        print(f"   F2 Finished Rate: {f2_kod_losses} KO/TKOs + {f2_sub_losses} Sub losses = {f2_kod_losses + f2_sub_losses}/{f2_losses} losses ({f2_finished_rate:.1%})")
        
        finishing_advantage = 'fighter1' if f1_finish_rate > f2_finish_rate else 'fighter2' if f2_finish_rate > f1_finish_rate else 'even'
        defensive_vulnerability = 'fighter1' if f1_finished_rate > f2_finished_rate else 'fighter2' if f2_finished_rate > f1_finished_rate else 'even'
        
        print(f"   🏆 Finishing Advantage: {finishing_advantage}")
        print(f"   🛡️  Defensive Vulnerability: {defensive_vulnerability}")
        
        return {
            'fighter1_finish_rate': f1_finish_rate,
            'fighter2_finish_rate': f2_finish_rate,
            'fighter1_finished_rate': f1_finished_rate,
            'fighter2_finished_rate': f2_finished_rate,
            'finishing_advantage': finishing_advantage,
            'defensive_vulnerability': defensive_vulnerability
        }
    
    def _analyze_recent_form(self, fighter1_data: Dict, fighter2_data: Dict) -> Dict[str, Any]:
        """Analyze recent performance and activity levels"""
        f1_recent = fighter1_data.get('recent_fights', [])
        f2_recent = fighter2_data.get('recent_fights', [])
        
        # Get most recent fight dates
        f1_last_fight = f1_recent[0].get('date') if f1_recent else None
        f2_last_fight = f2_recent[0].get('date') if f2_recent else None
        
        # Analyze recent opposition level
        f1_recent_opposition = [f.get('opponent_name') for f in f1_recent[:3]]
        f2_recent_opposition = [f.get('opponent_name') for f in f2_recent[:3]]
        
        return {
            'fighter1_last_fight_date': f1_last_fight,
            'fighter2_last_fight_date': f2_last_fight,
            'fighter1_recent_activity': len(f1_recent),
            'fighter2_recent_activity': len(f2_recent),
            'fighter1_recent_opposition': f1_recent_opposition,
            'fighter2_recent_opposition': f2_recent_opposition
        }
    
    def _analyze_experience_factors(self, fighter1_data: Dict, fighter2_data: Dict) -> Dict[str, Any]:
        """Analyze experience and career longevity factors"""
        print(f"\n🥋 EXPERIENCE ANALYSIS DEBUG:")
        
        f1_career = fighter1_data.get('career_stats', {})
        f2_career = fighter2_data.get('career_stats', {})
        f1_ufc = fighter1_data.get('ufc_stats', {})
        f2_ufc = fighter2_data.get('ufc_stats', {})
        
        f1_total_fights = f1_career.get('total_fights', 0)
        f2_total_fights = f2_career.get('total_fights', 0)
        f1_ufc_fights = f1_ufc.get('ufc_fights', 0)
        f2_ufc_fights = f2_ufc.get('ufc_fights', 0)
        
        print(f"   F1 Experience: {f1_total_fights} total fights, {f1_ufc_fights} UFC fights")
        print(f"   F2 Experience: {f2_total_fights} total fights, {f2_ufc_fights} UFC fights")
        
        exp_advantage = 'fighter1' if f1_total_fights > f2_total_fights else 'fighter2' if f2_total_fights > f1_total_fights else 'even'
        ufc_exp_advantage = 'fighter1' if f1_ufc_fights > f2_ufc_fights else 'fighter2' if f2_ufc_fights > f1_ufc_fights else 'even'
        
        print(f"   🏆 Experience Advantage: {exp_advantage}")
        print(f"   🏆 UFC Experience Advantage: {ufc_exp_advantage}")
        
        return {
            'fighter1_total_fights': f1_total_fights,
            'fighter2_total_fights': f2_total_fights,
            'fighter1_ufc_fights': f1_ufc_fights,
            'fighter2_ufc_fights': f2_ufc_fights,
            'experience_advantage': exp_advantage,
            'ufc_experience_advantage': ufc_exp_advantage
        }
    
    def _generate_tactical_prediction(self, fighter1_data: Dict, fighter2_data: Dict, analysis: Dict) -> Dict[str, Any]:
        """Generate tactical fight prediction based on all analysis"""
        print(f"\n🎯 TACTICAL PREDICTION GENERATION DEBUG:")
        
        # Extract key factors for prediction
        wc_analysis = analysis['weight_class_analysis']
        physical_analysis = analysis['physical_analysis']
        finishing_analysis = analysis['finishing_ability_analysis']
        trends_analysis = analysis['career_trends_analysis']
        
        # Calculate advantage scores
        f1_advantages = 0
        f2_advantages = 0
        
        advantage_categories = [
            'weight_class_advantage',
            'height_advantage', 
            'reach_advantage',
            'finishing_advantage',
            'momentum_advantage',
            'experience_advantage'
        ]
        
        print(f"   Scoring advantages across {len(advantage_categories)} categories:")
        
        for category in advantage_categories:
            for analysis_name, analysis_dict in analysis.items():
                if category in analysis_dict:
                    advantage_holder = analysis_dict[category]
                    print(f"   - {category}: {advantage_holder}")
                    if advantage_holder == 'fighter1':
                        f1_advantages += 1
                    elif advantage_holder == 'fighter2':
                        f2_advantages += 1
                    break
        
        print(f"\n   📊 FINAL ADVANTAGE TALLY:")
        print(f"   Fighter 1 Advantages: {f1_advantages}")
        print(f"   Fighter 2 Advantages: {f2_advantages}")
        
        # Determine predicted winner
        predicted_winner = 'fighter1' if f1_advantages > f2_advantages else 'fighter2' if f2_advantages > f1_advantages else 'even'
        print(f"   🏆 PREDICTED WINNER: {predicted_winner}")
        
        # Generate tactical analysis
        f1_path_to_victory = self._generate_path_to_victory(fighter1_data, analysis, 'fighter1')
        f2_path_to_victory = self._generate_path_to_victory(fighter2_data, analysis, 'fighter2')
        
        print(f"   F1 Path to Victory: {f1_path_to_victory}")
        print(f"   F2 Path to Victory: {f2_path_to_victory}")
        
        # Predict method and timing
        method_prediction = self._predict_fight_method(fighter1_data, fighter2_data, finishing_analysis)
        print(f"   Predicted Method: {method_prediction['method']} in {method_prediction['round']} ({method_prediction['probability']} probability)")
        
        return {
            'predicted_winner': predicted_winner,
            'fighter1_advantages_count': f1_advantages,
            'fighter2_advantages_count': f2_advantages,
            'fighter1_path_to_victory': f1_path_to_victory,
            'fighter2_path_to_victory': f2_path_to_victory,
            'predicted_method': method_prediction,
            'tactical_summary': self._generate_tactical_summary(analysis, predicted_winner)
        }
    
    def _generate_path_to_victory(self, fighter_data: Dict, analysis: Dict, fighter_num: str) -> str:
        """Generate specific path to victory for a fighter"""
        paths = []
        
        # Check finishing ability
        finishing_analysis = analysis['finishing_ability_analysis']
        if finishing_analysis.get(f'{fighter_num}_finish_rate', 0) > 0.6:
            if fighter_data.get('career_stats', {}).get('ko_wins', 0) > fighter_data.get('career_stats', {}).get('sub_wins', 0):
                paths.append("early striking exchanges and knockout power")
            else:
                paths.append("grappling dominance and submission opportunities")
        
        # Check physical advantages
        physical_analysis = analysis['physical_analysis']
        if physical_analysis.get('reach_advantage') == fighter_num:
            paths.append("maintaining distance and utilizing reach advantage")
        
        # Check recent form
        trends_analysis = analysis['career_trends_analysis']
        if trends_analysis.get('momentum_advantage') == fighter_num:
            paths.append("riding current momentum and confidence")
        
        if not paths:
            paths.append("capitalizing on experience and well-rounded skillset")
        
        return ". ".join(paths).capitalize()
    
    def _predict_fight_method(self, fighter1_data: Dict, fighter2_data: Dict, finishing_analysis: Dict) -> Dict[str, Any]:
        """Predict how the fight will end"""
        f1_finish_rate = finishing_analysis.get('fighter1_finish_rate', 0)
        f2_finish_rate = finishing_analysis.get('fighter2_finish_rate', 0)
        
        avg_finish_rate = (f1_finish_rate + f2_finish_rate) / 2
        
        if avg_finish_rate > 0.6:
            if fighter1_data.get('career_stats', {}).get('ko_wins', 0) + fighter2_data.get('career_stats', {}).get('ko_wins', 0) > \
               fighter1_data.get('career_stats', {}).get('sub_wins', 0) + fighter2_data.get('career_stats', {}).get('sub_wins', 0):
                return {'method': 'KO/TKO', 'round': 'Round 1-2', 'probability': 'High'}
            else:
                return {'method': 'Submission', 'round': 'Round 1-3', 'probability': 'High'}
        elif avg_finish_rate > 0.3:
            return {'method': 'KO/TKO or Decision', 'round': 'Round 2-3', 'probability': 'Moderate'}
        else:
            return {'method': 'Decision', 'round': 'Round 3', 'probability': 'High'}
    
    def _generate_tactical_summary(self, analysis: Dict, predicted_winner: str) -> str:
        """Generate overall tactical fight summary"""
        key_factors = []
        
        # Weight class performance
        wc_analysis = analysis['weight_class_analysis']
        if wc_analysis.get('weight_class_advantage') != 'even':
            winner = wc_analysis['weight_class_advantage']
            key_factors.append(f"{winner} has superior weight class performance")
        
        # Physical matchup
        physical_analysis = analysis['physical_analysis']
        if physical_analysis.get('reach_advantage') != 'even':
            winner = physical_analysis['reach_advantage']
            key_factors.append(f"{winner} holds significant reach advantage")
        
        # Finishing ability
        finishing_analysis = analysis['finishing_ability_analysis']
        if finishing_analysis.get('finishing_advantage') != 'even':
            winner = finishing_analysis['finishing_advantage']
            key_factors.append(f"{winner} demonstrates superior finishing ability")
        
        if not key_factors:
            key_factors.append("Both fighters present evenly matched skillsets")
        
        summary = "Key tactical factors: " + "; ".join(key_factors[:3]) + "."
        
        if predicted_winner != 'even':
            summary += f" Prediction favors {predicted_winner} based on cumulative advantages."
        else:
            summary += " Extremely close matchup with no clear favorite."
        
        return summary
    
    def _calculate_prediction_confidence(self, analysis: Dict) -> Dict[str, Any]:
        """Calculate confidence score based on data quality and consistency"""
        confidence_factors = []
        
        # Check data completeness
        wc_analysis = analysis['weight_class_analysis']
        if wc_analysis.get('fighter1_wc_experience', 0) > 3 and wc_analysis.get('fighter2_wc_experience', 0) > 3:
            confidence_factors.append(0.2)  # Good weight class data
        
        # Check opponent quality data
        opp_analysis = analysis['opponent_quality_analysis']
        if opp_analysis.get('fighter1_avg_opponent_win_rate', 0) > 0 and opp_analysis.get('fighter2_avg_opponent_win_rate', 0) > 0:
            confidence_factors.append(0.2)  # Good opponent quality data
        
        # Check recent form data
        trends_analysis = analysis['career_trends_analysis']
        if trends_analysis.get('fighter1_current_streak', {}) and trends_analysis.get('fighter2_current_streak', {}):
            confidence_factors.append(0.15)  # Good recent form data
        
        # Check experience levels
        exp_analysis = analysis['experience_analysis']
        if exp_analysis.get('fighter1_total_fights', 0) > 10 and exp_analysis.get('fighter2_total_fights', 0) > 10:
            confidence_factors.append(0.15)  # Both fighters experienced
        
        # Base confidence
        confidence_factors.append(0.3)
        
        total_confidence = min(sum(confidence_factors), 0.95)
        
        confidence_level = 'High' if total_confidence > 0.8 else 'Moderate' if total_confidence > 0.6 else 'Low'
        
        return {
            'score': total_confidence,
            'level': confidence_level,
            'factors_considered': len(confidence_factors)
        }
    
    def _extract_key_factors(self, analysis: Dict) -> List[str]:
        """Extract the most important factors for the prediction"""
        factors = []
        
        # Weight class dominance
        wc_analysis = analysis['weight_class_analysis']
        if wc_analysis.get('weight_class_advantage') != 'even':
            winner = wc_analysis['weight_class_advantage']
            rate = wc_analysis.get(f'{winner}_wc_win_rate', 0)
            factors.append(f"Weight class performance: {winner} ({rate:.1%} win rate)")
        
        # Physical advantages
        physical_analysis = analysis['physical_analysis']
        if physical_analysis.get('reach_advantage') != 'even':
            winner = physical_analysis['reach_advantage']
            diff = abs(physical_analysis.get('reach_difference_inches', 0))
            factors.append(f"Reach advantage: {winner} (+{diff}\" reach)")
        
        # Finishing ability
        finishing_analysis = analysis['finishing_ability_analysis']
        if finishing_analysis.get('finishing_advantage') != 'even':
            winner = finishing_analysis['finishing_advantage']
            rate = finishing_analysis.get(f'{winner}_finish_rate', 0)
            factors.append(f"Finishing ability: {winner} ({rate:.1%} finish rate)")
        
        # Opponent quality
        opp_analysis = analysis['opponent_quality_analysis']
        if opp_analysis.get('opponent_quality_advantage') != 'even':
            winner = opp_analysis['opponent_quality_advantage']
            factors.append(f"Strength of schedule: {winner} faced stronger opposition")
        
        return factors[:4]  # Return top 4 factors
    
    def _parse_height(self, height_str: Optional[str]) -> Optional[float]:
        """Parse height string into inches"""
        if not height_str:
            return None
        try:
            if "'" in height_str:
                parts = height_str.replace('"', '').split("'")
                feet = int(parts[0])
                inches = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                return feet * 12 + inches
            elif '"' in height_str:
                return float(height_str.replace('"', ''))
            else:
                return float(height_str)
        except:
            return None
    
    def _parse_reach(self, reach_str: Optional[str]) -> Optional[float]:
        """Parse reach string into inches"""
        if not reach_str:
            return None
        try:
            return float(reach_str.replace('"', '').replace(' in', ''))
        except:
            return None
    
    def _calculate_streak(self, recent_fights: List[Dict]) -> Dict[str, Any]:
        """Calculate current win/loss streak"""
        if not recent_fights:
            return {'type': 'none', 'count': 0}
        
        current_result = recent_fights[0].get('won')
        streak_count = 1
        
        for fight in recent_fights[1:]:
            if fight.get('won') == current_result:
                streak_count += 1
            else:
                break
        
        return {
            'type': 'win' if current_result else 'loss',
            'count': streak_count
        }

# Global service instance
fight_prediction_service = FightPredictionService()