"""
MMA Query Service - Natural language to SQL query generation using Agno and Azure OpenAI
Enhanced version using the Agno framework for better agent capabilities
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import text
from mma_website import db
from mma_website.utils.text_utils import row_to_dict
from mma_website.services.query_cache import query_cache
from mma_website.services.live_data_service import live_data_service
from mma_website.services.conversation_memory import conversation_memory
from dotenv import load_dotenv
import uuid

# Load environment variables from .env file
load_dotenv()

# Agno integration
try:
    from agno.agent import Agent
    from agno.models.azure.openai_chat import AzureOpenAI
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    Agent = None
    AzureOpenAI = None

logger = logging.getLogger(__name__)

class MMAQueryService:
    """Enhanced MMA Query Service using multi-agent team with Agno framework"""
    
    def __init__(self):
        # Initialize all agents
        self.question_classifier_agent = None
        self.data_presentation_agent = None
        self.sql_agent = None
        self.mma_analyst_agent = None
        
        # Database schema context for the LLM - initialize this first
        self.schema_context = self._get_database_schema()
        
        # Now setup agents (which depend on schema_context)
        if AGNO_AVAILABLE:
            self.setup_agno_agents()
        
    def setup_agno_agents(self):
        """Initialize multi-agent team: Question Classifier, Data Presenter, SQL Expert, and MMA Analyst"""
        try:
            # Check for required environment variables
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            deployment = os.getenv('AZURE_DEPLOYMENT')
            
            if not all([api_key, endpoint, deployment]):
                logger.warning("Missing Azure OpenAI configuration for Agno agents")
                return
            
            # Create Azure OpenAI model configuration using pattern from user's sample
            azure_model = AzureOpenAI(
                api_key=api_key,
                api_version="2024-12-01-preview", 
                azure_endpoint=endpoint,
                azure_deployment=deployment
            )
            
            # 1. Question Classification Agent
            self.question_classifier_agent = Agent(
                model=azure_model,
                name="MMA Question Classifier",
                description="Analyzes user questions to determine optimal response format and data presentation strategy",
                instructions="""You are an expert MMA analyst and statistician. Analyze user questions to determine optimal data presentation and response strategy.

Return a JSON object with these fields:

{
    "question_type": "statistical|comparison|record_lookup|fight_history|ranking|predictions|techniques|events|betting|historical",
    "data_complexity": "simple|moderate|complex",
    "show_table": true|false,
    "show_summary_stats": true|false,
    "visual_elements": ["cards"|"list"|"comparison"|"timeline"|"chart"|"heatmap"],
    "follow_up_suggestions": ["suggestion1", "suggestion2"],
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of classification"
}

ENHANCED QUESTION TYPE CLASSIFICATIONS:

**CORE DATA TYPES:**
- **statistical**: Numbers, percentages, averages, counts ("How many knockouts?", "Average fight time", "Submission rate")
- **comparison**: Head-to-head analysis, fighter vs fighter ("Jones vs Cormier", "Who hits harder?", "Compare their records")
- **record_lookup**: Win/loss records, career stats ("Jon Jones UFC record", "What's his record?")
- **fight_history**: Recent fights, career timeline, opponent lists ("Recent fights", "Last 5 fights", "Career overview", "Who has he fought?")
- **ranking**: Best/worst lists, top performers ("Top 10 finishers", "Best heavyweights", "Most wins")

**ADVANCED TYPES:**
- **predictions**: Future fights, matchup analysis ("Who wins X vs Y?", "Next title shot", "Predictions")
- **techniques**: Fighting styles, techniques used ("Best strikers", "Submission specialists", "Wrestling heavy")
- **events**: Event information, cards, venues ("UFC 300 fights", "Next event", "Madison Square Garden events")
- **betting**: Odds analysis, upsets, favorites ("Biggest upsets", "Favorite vs underdog", "Betting trends")
- **historical**: Trends over time, evolution ("How has MMA changed?", "Title reign lengths", "Era comparisons")

**KEYWORD DETECTION:**
- Fight History: "recent", "last", "latest", "career", "opponents", "fought", "timeline", "history"
- Records: "record", "wins", "losses", "stats", "numbers"
- Comparisons: "vs", "versus", "compare", "better", "who", "which"
- Rankings: "best", "top", "greatest", "worst", "ranking", "list"
- Predictions: "predict", "who wins", "next", "future", "matchup"
- Statistics: "how many", "percentage", "average", "rate", "most", "least"

**FOLLOW-UP SUGGESTIONS:**
Always provide 2 relevant follow-up questions based on the query type.

**DATA PRESENTATION:**
- show_table: true for multi-row data (fight_history, comparisons, rankings, events)
- show_summary_stats: true for statistical analysis, false for simple lookups
- visual_elements: Match to data type (cards=records, timeline=history, chart=statistics)

**CONFIDENCE SCORING:**
Rate your classification confidence (0.0-1.0) based on keyword clarity and context.

CRITICAL: Return ONLY the JSON object, no explanations or markdown.""",
                markdown=False,
            )
            
            # 2. Data Presentation Agent
            self.data_presentation_agent = Agent(
                model=azure_model,
                name="MMA Data Presenter",
                description="Formats query results optimally based on question classification",
                instructions="""You are an expert at formatting MMA data for optimal user experience.

Given the question classification and raw SQL results, you format the data structure that will be used by the frontend.

Return a JSON object with this structure:
{
    "format_type": "table|cards|list|summary",
    "primary_data": [...],  // Main data to display
    "summary_stats": {...}, // Key statistics (if needed)
    "table_headers": [...], // Column names (if table format)
    "visual_layout": "side_by_side|vertical|grid|single",
    "highlight_fields": [...] // Important fields to emphasize
}

Format Guidelines:
- **table**: For comparisons, rankings, statistical breakdowns, fight_history
- **cards**: For fighter profiles, individual win/loss records
- **list**: For simple enumerations only
- **summary**: For factual questions, counts

Always optimize for readability and user experience.
CRITICAL: Return ONLY the JSON object.""",
                markdown=False,
            )
            
            # 3. Enhanced SQL Expert Agent
            self.sql_agent = Agent(
                model=azure_model,
                name="MMA SQL Expert",
                description="Expert at converting natural language questions about MMA into SQL queries",
                instructions=f"""You are an expert SQL query generator for an MMA (Mixed Martial Arts) database.

{self.schema_context}

Generate SQL queries based on the question AND the presentation requirements provided by the question classifier.

CRITICAL RULES:
1. ONLY return ONE SINGLE SQL query, no explanations, no markdown, no code blocks, no semicolons
2. Use proper SQLite syntax
3. Always use JOIN operations when accessing multiple tables
4. For fighter records, use UNION to combine fighter_1 and fighter_2 perspectives
5. Use LIKE with LOWER() for partial string matching (case insensitive)
6. Adjust LIMIT based on question type (comparisons: 10-20, rankings: 10-50, records: 1-5)
7. For fighter vs fighter queries, check both fighter_1_id/fighter_2_id combinations
8. For statistical queries, include aggregate functions (COUNT, AVG, etc.)
9. Never use dangerous SQL keywords like DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, TRUNCATE
10. NEVER include multiple SQL statements separated by semicolons - return ONLY ONE query

QUERY PATTERNS BY TYPE:

1. FIGHTER RECORDS (wins/losses/draws):
SELECT 
  a.full_name,
  a.id as fighter_id,
  a.headshot_url as fighter_photo,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 1) OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 1) THEN 1 ELSE 0 END) as wins,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 0) OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 0) THEN 1 ELSE 0 END) as losses,
  SUM(CASE WHEN (f.fighter_1_id = a.id OR f.fighter_2_id = a.id) AND f.fighter_1_winner IS NULL AND f.fighter_2_winner IS NULL THEN 1 ELSE 0 END) as draws
FROM athletes a
JOIN fights f ON (f.fighter_1_id = a.id OR f.fighter_2_id = a.id)
WHERE LOWER(a.full_name) LIKE '%fighter_name%'
GROUP BY a.id, a.full_name, a.headshot_url

2. FIGHT HISTORY (recent fights, opponent lists):
SELECT 
  c.date,
  c.event_name as event,
  c.event_id as event_id,
  CASE WHEN f.fighter_1_id = target.id THEN a2.full_name ELSE a1.full_name END as opponent,
  CASE WHEN f.fighter_1_id = target.id THEN a2.id ELSE a1.id END as opponent_id,
  CASE WHEN f.fighter_1_id = target.id THEN a2.headshot_url ELSE a1.headshot_url END as opponent_photo,
  CASE WHEN f.fighter_1_id = target.id AND f.fighter_1_winner = 1 THEN 'Win'
       WHEN f.fighter_2_id = target.id AND f.fighter_2_winner = 1 THEN 'Win'
       WHEN f.fighter_1_winner IS NULL AND f.fighter_2_winner IS NULL THEN 'Draw'
       ELSE 'Loss' END as result,
  f.result_display_name as method,
  CASE WHEN f.end_round IS NOT NULL AND f.end_time IS NOT NULL 
       THEN 'R' || f.end_round || ' ' || f.end_time 
       ELSE 'Decision' END as finish,
  target.headshot_url as fighter_photo,
  target.id as fighter_id
FROM fights f
JOIN athletes target ON LOWER(target.full_name) LIKE '%fighter_name%'
JOIN athletes a1 ON f.fighter_1_id = a1.id  
JOIN athletes a2 ON f.fighter_2_id = a2.id
JOIN cards c ON f.event_id = c.event_id
WHERE (f.fighter_1_id = target.id OR f.fighter_2_id = target.id)
ORDER BY c.date DESC

3. HEAD-TO-HEAD (fighter vs fighter):
SELECT 
  c.date,
  c.event_name,
  a1.full_name as fighter_1,
  a2.full_name as fighter_2,
  CASE WHEN f.fighter_1_winner = 1 THEN a1.full_name
       WHEN f.fighter_2_winner = 1 THEN a2.full_name
       ELSE 'Draw' END as winner,
  f.result_display_name as method,
  CASE WHEN f.end_round IS NOT NULL THEN 'R' || f.end_round || ' ' || f.end_time ELSE 'Decision' END as finish
FROM fights f
JOIN athletes a1 ON f.fighter_1_id = a1.id
JOIN athletes a2 ON f.fighter_2_id = a2.id
JOIN cards c ON f.event_id = c.event_id
WHERE (LOWER(a1.full_name) LIKE '%fighter1%' AND LOWER(a2.full_name) LIKE '%fighter2%')
   OR (LOWER(a1.full_name) LIKE '%fighter2%' AND LOWER(a2.full_name) LIKE '%fighter1%')
ORDER BY c.date DESC

4. EVENT FIGHTS (fights on specific events):
SELECT 
  a1.full_name as fighter_1,
  a2.full_name as fighter_2,
  f.weight_class,
  CASE WHEN f.fighter_1_winner = 1 THEN a1.full_name
       WHEN f.fighter_2_winner = 1 THEN a2.full_name
       ELSE 'Draw' END as winner,
  f.result_display_name as method,
  f.card_segment
FROM fights f
JOIN athletes a1 ON f.fighter_1_id = a1.id
JOIN athletes a2 ON f.fighter_2_id = a2.id
JOIN cards c ON f.event_id = c.event_id
WHERE LOWER(c.event_name) LIKE '%event_name%'
ORDER BY 
  CASE f.card_segment 
    WHEN 'Main Card' THEN 1
    WHEN 'Preliminary Card' THEN 2
    WHEN 'Early Preliminary Card' THEN 3
    ELSE 4 END

5. STATISTICAL QUERIES (performance metrics):
Always join statistics_for_fights when asking about strikes, takedowns, etc.:
SELECT 
  a.full_name,
  AVG(s.sigStrikesLanded) as avg_sig_strikes,
  AVG(s.takedownsLanded) as avg_takedowns,
  COUNT(f.fight_id) as total_fights
FROM athletes a
JOIN fights f ON (f.fighter_1_id = a.id OR f.fighter_2_id = a.id)
JOIN statistics_for_fights s ON s.athlete_id = a.id AND s.competition_id = f.fight_id
WHERE LOWER(a.full_name) LIKE '%fighter_name%'
GROUP BY a.id, a.full_name

6. UPSET ANALYSIS (biggest upsets, controversial results):
SELECT 
  c.date,
  c.event_name,
  a1.full_name as fighter_1,
  a2.full_name as fighter_2,
  CASE WHEN f.fighter_1_winner = 1 THEN a1.full_name
       WHEN f.fighter_2_winner = 1 THEN a2.full_name
       ELSE 'Draw' END as winner,
  f.result_display_name as method,
  ABS(o.home_moneyLine_odds_current_american - o.away_moneyLine_odds_current_american) as odds_difference
FROM fights f
JOIN athletes a1 ON f.fighter_1_id = a1.id
JOIN athletes a2 ON f.fighter_2_id = a2.id
JOIN cards c ON f.event_id = c.event_id
LEFT JOIN odds o ON f.fight_id = o.fight_id
WHERE o.home_moneyLine_odds_current_american > 200 OR o.away_moneyLine_odds_current_american > 200
ORDER BY odds_difference DESC

7. PHYSICAL ATTRIBUTES (reach, height, weight analysis):
SELECT 
  a.full_name,
  a.height,
  a.weight,
  a.reach,
  a.weight_class,
  a.age,
  a.stance
FROM athletes a
WHERE a.height IS NOT NULL AND a.reach IS NOT NULL
ORDER BY a.reach DESC

8. KNOCKOUT/FINISHING ANALYSIS:
SELECT 
  a.full_name,
  a.weight_class,
  COUNT(f.fight_id) as total_fights,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 1 AND f.result_display_name LIKE '%KO%') OR 
               (f.fighter_2_id = a.id AND f.fighter_2_winner = 1 AND f.result_display_name LIKE '%KO%') 
           THEN 1 ELSE 0 END) as ko_wins,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 0 AND f.result_display_name LIKE '%KO%') OR 
               (f.fighter_2_id = a.id AND f.fighter_2_winner = 0 AND f.result_display_name LIKE '%KO%') 
           THEN 1 ELSE 0 END) as times_kod
FROM athletes a
JOIN fights f ON (f.fighter_1_id = a.id OR f.fighter_2_id = a.id)
GROUP BY a.id, a.full_name, a.weight_class
HAVING total_fights >= 3
ORDER BY ko_wins DESC

9. PREDICTION/COMPARISON QUERIES ("who would win", "X vs Y"):
For fighter vs fighter predictions, get comprehensive comparison data:
SELECT 
  a.full_name,
  a.weight_class,
  a.age,
  a.height,
  a.reach,
  a.stance,
  a.headshot_url as fighter_photo,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 1) OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 1) THEN 1 ELSE 0 END) as wins,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 0) OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 0) THEN 1 ELSE 0 END) as losses,
  COUNT(f.fight_id) as total_fights,
  AVG(s.sigStrikesLanded) as avg_sig_strikes_landed,
  AVG(s.sigStrikesAttempted) as avg_sig_strikes_attempted,
  AVG(s.takedownsLanded) as avg_takedowns_landed,  
  AVG(s.takedownsAttempted) as avg_takedowns_attempted,
  AVG(s.knockDowns) as avg_knockdowns,
  AVG(s.submissions) as avg_sub_attempts,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 1 AND f.end_round = 1) OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 1 AND f.end_round = 1) THEN 1 ELSE 0 END) as first_round_finishes,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 1 AND f.result_display_name LIKE '%KO%') OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 1 AND f.result_display_name LIKE '%KO%') THEN 1 ELSE 0 END) as ko_wins,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 1 AND f.result_display_name LIKE '%Submission%') OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 1 AND f.result_display_name LIKE '%Submission%') THEN 1 ELSE 0 END) as sub_wins
FROM athletes a
JOIN fights f ON (f.fighter_1_id = a.id OR f.fighter_2_id = a.id)
LEFT JOIN statistics_for_fights s ON s.athlete_id = a.id AND s.competition_id = f.fight_id
WHERE LOWER(a.full_name) LIKE '%fighter1%' OR LOWER(a.full_name) LIKE '%fighter2%'
GROUP BY a.id, a.full_name, a.weight_class, a.age, a.height, a.reach, a.stance, a.headshot_url
HAVING total_fights >= 1
ORDER BY a.full_name

IMPORTANT: Always replace placeholder names like '%fighter_name%', '%fighter1%', '%event_name%' with actual extracted names from the user's question.""",
                markdown=False,
            )
            
            # 4. Enhanced MMA Analyst Agent
            self.mma_analyst_agent = Agent(
                model=azure_model,
                name="MMA Data Analyst",
                description="Expert MMA analyst providing tactical fight breakdowns and data-driven predictions",
                instructions="""You are an expert MMA analyst specializing in data-driven fight predictions and tactical breakdowns.

**ANALYSIS TYPES:**

**For PREDICTIONS ("who would win", "X vs Y"):**
Provide specific tactical analysis based on the data:

1. **Key Advantages**: What each fighter's data shows they excel at
2. **Tactical Matchup**: How their styles/stats interact 
3. **Path to Victory**: Specific ways each could win based on their numbers
4. **Critical Factors**: What the data suggests will decide the fight

**Example GOOD prediction analysis:**
"Jones averages 4.2 takedowns per fight vs Aspinall's 85% takedown defense rate - a key tactical battle. Aspinall's 1.3 knockdowns per fight and 92% first-round finish rate favor early aggression, while Jones' 6.8 significant strikes per minute and 78% control time suggest later-round dominance. Jones' path: clinch work and late-round pressure. Aspinall's path: early striking before Jones establishes grappling control."

**For RECORDS/COMPARISONS:**
- Point out key numerical differences
- Explain what the stats mean tactically
- Keep concise (1-2 sentences for simple, 3-4 for complex)

**AVOID:**
- Generic phrases like "experience advantage", "higher volume", "demonstrates"  
- Repeating data already in tables/cards
- Vague analysis without specific tactical insights
- Subjective language not backed by numbers

**CRITICAL**: For predictions, focus on HOW the fight plays out tactically based on the data, not just WHO has better numbers.""",
                markdown=True,
            )
            
            logger.info("Agno agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Agno agents: {e}")
            self.question_classifier_agent = None
            self.data_presentation_agent = None
            self.sql_agent = None
            self.mma_analyst_agent = None
    
    def _get_database_schema(self) -> str:
        """Get comprehensive database schema information for the LLM"""
        schema_info = """
# MMA Database Schema (73,000+ fights, 36,000+ fighters)

## Core Tables:

### athletes (Fighter Information)
- id: Fighter unique identifier
- full_name: Fighter's full name (use for searches)
- nickname: Fighter's nickname
- weight_class: Fighter's primary weight class
- height: Fighter's height in inches
- weight: Fighter's weight in pounds
- reach: Fighter's reach in inches
- age: Fighter's current age
- stance: Fighting stance (Orthodox, Southpaw, Switch, etc.)
- association: Fighter's gym/team
- default_league: Primary promotion (ufc, bellator, etc.)
- headshot_url: Fighter photo URL

### fights (Fight Results)
- fight_id: Unique fight identifier
- event_id: Event identifier (join with cards table)
- fighter_1_id: First fighter ID (join with athletes)
- fighter_2_id: Second fighter ID (join with athletes)
- fighter_1_winner: 1 if fighter 1 won, 0 if lost, NULL if draw/NC
- fighter_2_winner: 1 if fighter 2 won, 0 if lost, NULL if draw/NC
- weight_class: Fight weight class
- result_display_name: Fight result method (KO, TKO, Submission, Decision, etc.)
- end_round: Round the fight ended (NULL for decisions)
- end_time: Time in round when fight ended
- card_segment: Position on card (Main Card, Preliminary Card, etc.)

### cards (Events)
- event_id: Unique event identifier
- event_name: Name of the event (e.g., "UFC 300")
- date: Event date (YYYY-MM-DD format)
- venue_name: Venue name
- city: Event city
- country: Event country
- league: Promotion (ufc, bellator, etc.)

### odds (Betting Information)
- fight_id: Fight identifier
- home_athlete_id: Home fighter ID
- away_athlete_id: Away fighter ID
- home_moneyLine_odds_current_american: Home fighter odds
- away_moneyLine_odds_current_american: Away fighter odds
- home_favorite: 1 if home fighter is favorite
- away_favorite: 1 if away fighter is favorite

### statistics_for_fights (Detailed Fight Stats)
- athlete_id: Fighter ID
- competition_id: Fight ID (same as fight_id)
- event_id: Event ID
- sigStrikesLanded: Significant strikes landed
- sigStrikesAttempted: Significant strikes attempted
- totalStrikesLanded: Total strikes landed
- totalStrikesAttempted: Total strikes attempted
- takedownsLanded: Successful takedowns
- takedownsAttempted: Takedown attempts
- knockDowns: Knockdowns scored
- submissions: Submission attempts

### ufc_rankings (Current Rankings)
- fighter_id: Fighter ID
- division: Weight class division
- rank: Current ranking (1-15, or 'C' for champion)
- fighter_name: Fighter name

## Weight Classes:
**Men's:** Heavyweight, Light Heavyweight, Middleweight, Welterweight, Lightweight, Featherweight, Bantamweight, Flyweight
**Women's:** Women's Featherweight, Women's Bantamweight, Women's Flyweight, Women's Strawweight, Women's Atomweight

## Common Query Patterns:
- **Fighter records:** Use UNION to combine fighter_1_id and fighter_2_id results
- **Fight finishes:** Look for result_display_name containing 'KO', 'TKO', 'Submission'
- **Recent activity:** Order by cards.date DESC
- **Head-to-head:** Match fighter IDs in both positions
- **Rankings:** Use ufc_rankings table for current standings
- **Statistics:** Join with statistics_for_fights for detailed metrics
"""
        return schema_info
    
    def process_query(self, user_question: str, session_id: str = None) -> Dict[str, Any]:
        """
        Process a natural language MMA question using multi-agent team with caching and conversation memory
        
        Args:
            user_question: User's natural language question
            session_id: Optional session ID for conversation tracking
            
        Returns:
            Dict containing enhanced query results with intelligent formatting
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get conversation context for better AI responses
        context_prompt = conversation_memory.generate_context_prompt(session_id, user_question)
        # Check cache first
        cached_result = query_cache.get(user_question)
        if cached_result:
            logger.info(f"Returning cached result for: {user_question[:50]}...")
            # Add cache indicator to the result
            cached_result['cached'] = True
            return cached_result
        
        # Check if all agents are available
        required_agents = [self.question_classifier_agent, self.data_presentation_agent, 
                          self.sql_agent, self.mma_analyst_agent]
        
        if not all(required_agents):
            # Provide detailed debugging info for configuration issues
            import os
            config_status = {
                'agno_available': AGNO_AVAILABLE,
                'api_key_set': bool(os.getenv('AZURE_OPENAI_API_KEY')),
                'endpoint_set': bool(os.getenv('AZURE_OPENAI_ENDPOINT')),
                'deployment_set': bool(os.getenv('AZURE_DEPLOYMENT')),
            }
            
            error_details = []
            if not AGNO_AVAILABLE:
                error_details.append("Agno package not installed")
            if not config_status['api_key_set']:
                error_details.append("AZURE_OPENAI_API_KEY not set")
            if not config_status['endpoint_set']:
                error_details.append("AZURE_OPENAI_ENDPOINT not set") 
            if not config_status['deployment_set']:
                error_details.append("AZURE_DEPLOYMENT not set")
                
            if not error_details:
                error_details.append("Authentication failed - check Azure credentials")
            
            return {
                'error': f'Multi-agent team not configured: {", ".join(error_details)}. Please check your Azure OpenAI settings.',
                'success': False,
                'debug_info': config_status
            }
        
        try:
            # Step 1: Classify the question to determine presentation strategy
            logger.info(f"Step 1: Classifying question: {user_question}")
            classification = self._classify_question(user_question)
            
            if not classification:
                return {
                    'error': 'Could not classify your question for optimal presentation.',
                    'success': False
                }
            
            # Step 2: Check if this is a real-time/current events question
            if self._is_current_events_question(user_question, classification):
                logger.info(f"Step 2: Detected current events question, using live data")
                return self._handle_current_events_question(user_question, classification)
            
            # Step 2: Generate SQL query for historical data
            logger.info(f"Step 2: Generating SQL query with classification: {classification}")
            sql_query = self._generate_enhanced_sql_query(user_question, classification)
            
            if not sql_query:
                return {
                    'error': 'Could not generate a valid SQL query from your question.',
                    'success': False
                }
            
            # Step 3: Execute the query
            logger.info(f"Step 3: Executing SQL query")
            query_results = self._execute_query(sql_query)
            
            if 'error' in query_results:
                return query_results
            
            # Step 4: Format the data optimally based on classification
            logger.info(f"Step 4: Formatting data presentation")
            data_presentation = self._format_data_presentation(
                query_results['data'], classification
            )
            
            # Step 5: Generate intelligent analysis that complements the data presentation
            logger.info(f"Step 5: Generating expert analysis")
            analysis_text = self._generate_expert_analysis(
                user_question, classification, query_results['data'], data_presentation
            )
            
            result = {
                'success': True,
                'question': user_question,
                'classification': classification,
                'sql_query': sql_query,
                'data': query_results['data'],
                'presentation': data_presentation,
                'analysis': analysis_text,
                'row_count': len(query_results['data']) if query_results['data'] else 0,
                'cached': False,
                'session_id': session_id
            }
            
            # Add conversation memory context and enhance follow-up suggestions
            context_suggestions = conversation_memory.suggest_follow_ups(session_id, classification)
            if context_suggestions:
                if 'follow_up_suggestions' not in classification:
                    classification['follow_up_suggestions'] = []
                classification['follow_up_suggestions'].extend(context_suggestions)
                # Keep unique suggestions and limit to 3
                classification['follow_up_suggestions'] = list(set(classification['follow_up_suggestions']))[:3]
            
            # Store this interaction in conversation memory
            conversation_memory.add_interaction(session_id, user_question, result)
            
            # Cache the result for future queries
            query_cache.put(user_question, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query with multi-agent team: {e}")
            return {
                'error': f'An error occurred while processing your question: {str(e)}',
                'success': False
            }
    
    def _is_current_events_question(self, user_question: str, classification: Dict) -> bool:
        """Determine if a question requires real-time/live data"""
        question_lower = user_question.lower()
        
        # Current events keywords
        current_keywords = [
            'this weekend', 'next event', 'upcoming', 'current', 'latest', 'recent news',
            'today', 'tomorrow', 'next week', 'coming up', 'scheduled', 'live',
            'current rankings', 'who\'s fighting', 'next ufc', 'this saturday',
            'breaking news', 'just announced', 'latest rankings', 'now', 'currently'
        ]
        
        # Check for current events keywords
        if any(keyword in question_lower for keyword in current_keywords):
            return True
            
        # Check classification type
        if classification.get('question_type') in ['current_events', 'events']:
            return True
            
        return False
    
    def _handle_current_events_question(self, user_question: str, classification: Dict) -> Dict[str, Any]:
        """Handle questions requiring real-time data"""
        question_lower = user_question.lower()
        
        try:
            # Determine which type of current events data is needed
            if any(keyword in question_lower for keyword in ['next event', 'this weekend', 'upcoming', 'scheduled']):
                # Get upcoming UFC events
                live_data = live_data_service.get_upcoming_events()
                
                if live_data.get('success') and live_data.get('events'):
                    events = live_data['events'][:3]  # Next 3 events
                    
                    # Format as table data
                    formatted_data = []
                    for event in events:
                        main_fights = event.get('fights', [])[:3]  # Top 3 fights per event
                        
                        for fight in main_fights:
                            formatted_data.append({
                                'event': event.get('name', 'Unknown Event'),
                                'date': event.get('date', ''),
                                'fighter_1': fight.get('fighter1', {}).get('name', ''),
                                'fighter_2': fight.get('fighter2', {}).get('name', ''),
                                'weight_class': fight.get('weight_class', ''),
                                'venue': event.get('venue', ''),
                                'location': event.get('location', '')
                            })
                    
                    # Generate analysis
                    analysis = f"Found {len(events)} upcoming UFC events with {len(formatted_data)} featured fights. "
                    if events:
                        next_event = events[0]
                        analysis += f"The next event is {next_event.get('name', '')} with {len(next_event.get('fights', []))} fights scheduled."
                    
                    return {
                        'success': True,
                        'question': user_question,
                        'classification': classification,
                        'data': formatted_data,
                        'analysis': analysis,
                        'presentation': {
                            'format_type': 'table',
                            'table_headers': ['Event', 'Date', 'Fighter 1', 'Fighter 2', 'Weight Class', 'Venue'],
                            'visual_layout': 'single'
                        },
                        'row_count': len(formatted_data),
                        'cached': False,
                        'live_data': True
                    }
                
            elif any(keyword in question_lower for keyword in ['current rankings', 'rankings', 'who\'s ranked']):
                # Get current UFC rankings
                live_data = live_data_service.get_current_rankings()
                
                if live_data.get('success') and live_data.get('divisions'):
                    # Format rankings data
                    formatted_data = []
                    divisions = live_data['divisions']
                    
                    for division, fighters in list(divisions.items())[:3]:  # Top 3 divisions
                        for fighter in fighters[:5]:  # Top 5 per division
                            formatted_data.append({
                                'division': division,
                                'rank': fighter.get('rank', ''),
                                'fighter': fighter.get('name', ''),
                                'record': fighter.get('record', ''),
                                'champion': '👑' if fighter.get('is_champion') else ''
                            })
                    
                    analysis = f"Current UFC rankings across {len(divisions)} divisions. Data includes champions and top contenders with their current records."
                    
                    return {
                        'success': True,
                        'question': user_question,
                        'classification': classification,
                        'data': formatted_data,
                        'analysis': analysis,
                        'presentation': {
                            'format_type': 'table',
                            'table_headers': ['Division', 'Rank', 'Fighter', 'Record', 'Status'],
                            'visual_layout': 'single'
                        },
                        'row_count': len(formatted_data),
                        'cached': False,
                        'live_data': True
                    }
            
            elif any(keyword in question_lower for keyword in ['recent results', 'latest fights', 'recent news']):
                # Get recent fight results
                live_data = live_data_service.get_recent_results()
                
                if live_data.get('success') and live_data.get('recent_fights'):
                    formatted_data = []
                    recent_events = live_data['recent_fights'][:2]  # Last 2 events
                    
                    for event in recent_events:
                        main_fights = event.get('fights', [])[:5]  # Top 5 fights per event
                        
                        for fight in main_fights:
                            formatted_data.append({
                                'event': event.get('event_name', ''),
                                'date': event.get('date', ''),
                                'fighter_1': fight.get('fighter1', ''),
                                'fighter_2': fight.get('fighter2', ''),
                                'winner': fight.get('winner', ''),
                                'method': fight.get('method', ''),
                                'weight_class': fight.get('weight_class', '')
                            })
                    
                    analysis = f"Recent UFC fight results from the last {len(recent_events)} events, showing {len(formatted_data)} completed fights."
                    
                    return {
                        'success': True,
                        'question': user_question,
                        'classification': classification,
                        'data': formatted_data,
                        'analysis': analysis,
                        'presentation': {
                            'format_type': 'table',
                            'table_headers': ['Event', 'Date', 'Fighter 1', 'Fighter 2', 'Winner', 'Method', 'Weight Class'],
                            'visual_layout': 'single'
                        },
                        'row_count': len(formatted_data),
                        'cached': False,
                        'live_data': True
                    }
            
            # Default fallback for current events
            return {
                'success': True,
                'question': user_question,
                'classification': classification,
                'data': [],
                'analysis': f"I recognize this as a current events question about '{user_question}'. While I have access to live UFC data, I may need more specific information to provide the exact details you're looking for. Try asking about 'next UFC event', 'current rankings', or 'recent fight results'.",
                'presentation': {'format_type': 'summary'},
                'row_count': 0,
                'cached': False,
                'live_data': True
            }
            
        except Exception as e:
            logger.error(f"Error handling current events question: {e}")
            return {
                'success': False,
                'error': f'Error fetching live data: {str(e)}',
                'question': user_question,
                'cached': False
            }
    
    def _classify_question(self, user_question: str) -> Optional[Dict]:
        """Classify the user question to determine optimal presentation strategy"""
        import json
        
        try:
            prompt = f"""Analyze this MMA question and classify it: "{user_question}"

Return the classification as a JSON object."""
            
            response = self.question_classifier_agent.run(prompt)
            classification_text = response.content.strip()
            
            print(f"🔍 DEBUG: Raw classification response: {repr(classification_text)}")
            
            # Parse JSON response
            classification = json.loads(classification_text)
            
            print(f"🔍 DEBUG: Question classified as: {classification}")
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying question: {e}")
            return None
    
    def _generate_enhanced_sql_query(self, user_question: str, classification: Dict) -> Optional[str]:
        """Generate SQL query enhanced with presentation requirements"""
        import json
        
        try:
            prompt = f"""Convert this MMA question to a SQL query: "{user_question}"

Question Classification: {json.dumps(classification)}

Adapt the query based on the classification:
- Question type: {classification.get('question_type')}
- Show table: {classification.get('show_table')}
- Data complexity: {classification.get('data_complexity')}

Remember: Return ONLY the SQL query, no explanations or formatting."""
            
            response = self.sql_agent.run(prompt)
            sql_query = response.content.strip()
            
            print(f"🔍 DEBUG: Raw SQL response from agent: {repr(sql_query)}")
            
            # Clean up the response (remove any markdown if present)
            if sql_query.startswith('```'):
                lines = sql_query.split('\n')
                sql_query = '\n'.join(lines[1:-1])
            
            # Remove any remaining formatting
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            
            print(f"🔍 DEBUG: Generated enhanced SQL after cleanup: {sql_query}")
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating enhanced SQL query: {e}")
            return None
    
    def _format_data_presentation(self, data: list[dict], classification: Dict) -> Dict:
        """Format the data optimally based on question classification"""
        import json
        
        if not data:
            return {
                'format_type': 'summary',
                'primary_data': [],
                'message': 'No data found'
            }
        
        try:
            prompt = f"""Format this MMA data for optimal presentation:

Question Classification: {json.dumps(classification)}
Data: {json.dumps(data[:5], indent=2, default=str)}  # Sample of data

Return formatting instructions as JSON."""
            
            response = self.data_presentation_agent.run(prompt)
            presentation_text = response.content.strip()
            
            # Parse JSON response
            presentation = json.loads(presentation_text)
            
            # Add the actual data
            presentation['primary_data'] = data
            
            logger.info(f"Data formatted as: {presentation.get('format_type')}")
            return presentation
            
        except Exception as e:
            logger.error(f"Error formatting data presentation: {e}")
            # Fallback formatting
            return {
                'format_type': 'table' if classification.get('show_table') else 'summary',
                'primary_data': data,
                'table_headers': list(data[0].keys()) if data else [],
                'visual_layout': 'single'
            }
    
    def _generate_expert_analysis(self, question: str, classification: Dict, 
                                 data: list[dict], presentation: Dict) -> str:
        """Generate expert analysis that complements the data presentation"""
        import json
        
        if not data:
            return "I couldn't find any data matching your question. Try rephrasing or asking about different fighters, events, or statistics."
        
        try:
            # Create context for the analyst
            context = {
                'question_type': classification.get('question_type'),
                'data_summary': {
                    'row_count': len(data),
                    'sample': data[:3]  # Just a small sample for context
                },
                'presentation_type': presentation.get('format_type')
            }
            
            prompt = f"""Provide expert MMA analysis for this question: "{question}"

Context:
- Question type: {classification.get('question_type')}
- Data presentation: {presentation.get('format_type')}
- Results found: {len(data)} entries

Sample data: {json.dumps(data[:2], indent=2, default=str)}

Focus on insights, context, and analysis that complement the data presentation.
Don't repeat the raw numbers - provide the "why this matters" perspective."""

            response = self.mma_analyst_agent.run(prompt)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating expert analysis: {e}")
            return f"Found {len(data)} results. The data shows interesting patterns in MMA statistics and fighter performance."
    
    def _execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query safely and return results"""
        
        # Enhanced SQL injection prevention
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE']
        query_upper = sql_query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return {
                    'error': f'Query contains dangerous keyword: {keyword}',
                    'success': False
                }
        
        # Prevent multiple statements
        if ';' in sql_query.rstrip('; \t\n'):
            return {
                'error': 'Multiple SQL statements not allowed',
                'success': False
            }
        
        # Clean and normalize the query
        sql_query = sql_query.strip().rstrip(';')
        
        # Check for reasonable limits
        if 'LIMIT' not in query_upper and 'TOP' not in query_upper:
            sql_query += ' LIMIT 50'
        
        try:
            print(f"🔍 DEBUG: Attempting to execute SQL: {sql_query}")
            
            db_session = db.session
            print(f"🔍 DEBUG: Got database session: {type(db_session)}")
            
            # Execute query
            result = db_session.execute(text(sql_query))
            print(f"🔍 DEBUG: Query executed, getting results...")
            
            rows = result.fetchall()
            print(f"🔍 DEBUG: Fetched {len(rows)} raw rows")
            
            # Convert to dictionaries for easier handling
            data = [row_to_dict(row) for row in rows]
            
            print(f"🔍 DEBUG: Query executed successfully, returned {len(data)} rows")
            print(f"🔍 DEBUG: First row sample: {data[0] if data else 'No data'}")
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            print(f"❌ ERROR: Database query error: {e}")
            print(f"❌ ERROR: Error type: {type(e)}")
            import traceback
            print(f"❌ ERROR: Full traceback: {traceback.format_exc()}")
            return {
                'error': f'Database error: {str(e)}',
                'success': False
            }

# Global service instance
mma_query_service = MMAQueryService()