"""
MMA Query Service V2 - Streamlined 2-agent architecture
Simplified workflow: Query Router → Unified SQL+Analysis Agent
Performance: ~60% faster, better output consistency
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

class MMAQueryServiceV2:
    """Enhanced MMA Query Service using streamlined 2-agent architecture"""

    def __init__(self):
        # Initialize agents
        self.router_agent = None
        self.unified_agent = None

        # Database schema context
        self.schema_context = self._get_database_schema()

        # Setup agents
        if AGNO_AVAILABLE:
            self.setup_agents()

    def setup_agents(self):
        """Initialize streamlined 2-agent team: Router + Unified SQL/Analysis Agent"""
        try:
            # Check for required environment variables
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            deployment = os.getenv('AZURE_DEPLOYMENT')

            if not all([api_key, endpoint, deployment]):
                logger.warning("Missing Azure OpenAI configuration for agents")
                return

            # Create Azure OpenAI model configuration
            azure_model = AzureOpenAI(
                api_key=api_key,
                api_version="2024-12-01-preview",
                azure_endpoint=endpoint,
                azure_deployment=deployment
            )

            # 1. Quick Router Agent - classifies query type and determines if live data needed
            self.router_agent = Agent(
                model=azure_model,
                name="MMA Query Router",
                description="Fast classifier to route queries to appropriate data source",
                instructions="""You are a quick query router for MMA questions. Analyze the question and return ONLY a JSON object:

{
    "query_type": "record|history|comparison|prediction|ranking|statistics|current_events",
    "needs_live_data": true|false,
    "requires_stats_join": true|false
}

**Query Types:**
- **record**: Win/loss records ("What's X's record?")
- **history**: Fight history, recent fights ("Show X's last 5 fights")
- **comparison**: Head-to-head stats ("X vs Y")
- **prediction**: Who would win questions ("Who wins X vs Y?")
- **ranking**: Top performers, best of lists ("Top 10 finishers")
- **statistics**: Aggregate stats ("Average fight time", "KO rate")
- **current_events**: Live/current data ("Next UFC event", "current rankings", "this weekend")

**Live Data Keywords:** "next", "upcoming", "current", "this weekend", "now", "latest rankings", "scheduled"
**Stats Join Needed:** When asking about strikes, takedowns, knockdowns, submissions

Return ONLY the JSON, no explanation.""",
                markdown=False,
            )

            # 2. Unified SQL + Analysis Agent - generates SQL and analyzes results in one call
            self.unified_agent = Agent(
                model=azure_model,
                name="MMA Unified SQL and Analysis Expert",
                description="Generates SQL queries and provides tactical analysis based on results",
                instructions=f"""You are an expert MMA analyst and SQL query generator. You will receive a question and must return a JSON object with SQL query AND analysis structure.

{self.schema_context}

Return a JSON object with this EXACT structure:

{{
    "sql_query": "YOUR SQL QUERY HERE (no markdown, single line)",
    "presentation_format": "table|cards|comparison|summary",
    "visual_layout": "single|side_by_side|grid|vertical",
    "table_headers": ["column1", "column2", ...],  // For table format
    "highlight_fields": ["field1", "field2", ...],  // Important fields to emphasize
    "analysis_template": "Brief analysis template with {{{{placeholder}}}} for dynamic data insertion"
}}

**SQL GENERATION RULES:**

1. CRITICAL: Return ONLY valid SQL - no markdown, no code blocks, no semicolons
2. For **predictions** ("who would win"), ALWAYS fetch comprehensive comparison data for BOTH fighters:
   - Physical: age, height, reach, stance
   - Record: wins, losses, total fights
   - Performance: avg strikes, takedowns, knockdowns, sub attempts
   - Finishing: KO wins, submission wins, first round finishes
3. Use proper SQLite syntax with CASE statements for records
4. Always LOWER() and LIKE for name matching
5. Add LIMIT based on question (predictions: 2-10, rankings: 10-50, records: 1-5)
6. Never use dangerous keywords (DROP, DELETE, INSERT, UPDATE, etc.)

**QUERY PATTERNS:**

**1. FIGHTER RECORDS:**
```sql
SELECT a.full_name, a.id as fighter_id, a.headshot_url as fighter_photo,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 1) OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 1) THEN 1 ELSE 0 END) as wins,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 0) OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 0) THEN 1 ELSE 0 END) as losses
FROM athletes a
JOIN fights f ON (f.fighter_1_id = a.id OR f.fighter_2_id = a.id)
WHERE LOWER(a.full_name) LIKE '%name%'
GROUP BY a.id, a.full_name, a.headshot_url
```

**2. PREDICTIONS/COMPARISONS (CRITICAL - USE THIS PATTERN):**
```sql
SELECT a.full_name, a.id as fighter_id, a.headshot_url as fighter_photo,
  a.weight_class, a.age, a.height, a.reach, a.stance,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 1) OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 1) THEN 1 ELSE 0 END) as wins,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 0) OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 0) THEN 1 ELSE 0 END) as losses,
  COUNT(f.fight_id) as total_fights,
  AVG(s.sigStrikesLanded) as avg_sig_strikes,
  AVG(s.takedownsLanded) as avg_takedowns,
  AVG(s.knockDowns) as avg_knockdowns,
  SUM(CASE WHEN (f.fighter_1_id = a.id AND f.fighter_1_winner = 1 AND f.end_round = 1) OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 1 AND f.end_round = 1) THEN 1 ELSE 0 END) as rd1_finishes,
  SUM(CASE WHEN f.result_display_name LIKE '%KO%' AND ((f.fighter_1_id = a.id AND f.fighter_1_winner = 1) OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 1)) THEN 1 ELSE 0 END) as ko_wins
FROM athletes a
JOIN fights f ON (f.fighter_1_id = a.id OR f.fighter_2_id = a.id)
LEFT JOIN statistics_for_fights s ON s.athlete_id = a.id AND s.competition_id = f.fight_id
WHERE LOWER(a.full_name) LIKE '%fighter1%' OR LOWER(a.full_name) LIKE '%fighter2%'
GROUP BY a.id, a.full_name, a.weight_class, a.age, a.height, a.reach, a.stance, a.headshot_url
ORDER BY a.full_name
```

**3. FIGHT HISTORY:**
```sql
SELECT c.date, c.event_name,
  CASE WHEN f.fighter_1_id = target.id THEN a2.full_name ELSE a1.full_name END as opponent,
  CASE WHEN f.fighter_1_id = target.id THEN a2.id ELSE a1.id END as opponent_id,
  CASE WHEN (f.fighter_1_id = target.id AND f.fighter_1_winner = 1) OR (f.fighter_2_id = target.id AND f.fighter_2_winner = 1) THEN 'Win' ELSE 'Loss' END as result,
  f.result_display_name as method
FROM fights f
JOIN athletes target ON LOWER(target.full_name) LIKE '%name%'
JOIN athletes a1 ON f.fighter_1_id = a1.id
JOIN athletes a2 ON f.fighter_2_id = a2.id
JOIN cards c ON f.event_id = c.event_id
WHERE f.fighter_1_id = target.id OR f.fighter_2_id = target.id
ORDER BY c.date DESC
LIMIT 10
```

**PRESENTATION FORMAT RULES:**

- **predictions**: presentation_format="comparison", visual_layout="side_by_side", include ALL stats in table_headers
- **records**: presentation_format="cards", visual_layout="single"
- **history**: presentation_format="table", visual_layout="vertical"
- **rankings/statistics**: presentation_format="table", visual_layout="single"

**ANALYSIS TEMPLATE RULES:**

For **predictions**, provide detailed tactical analysis:
- Use actual column names in {{{{double braces}}}} for dynamic insertion
- Mention specific advantages for each fighter based on stats
- Describe tactical matchup and paths to victory
- Reference numbers like "{{{{fighter1_name}}}}'s {{{{avg_takedowns}}}} takedowns vs {{{{fighter2_name}}}}'s defense"

For **records/history**, keep analysis brief and factual.

**CRITICAL:** Return ONLY the JSON object, no markdown, no explanations.""",
                markdown=False,
            )

            logger.info("V2 agents initialized successfully (2-agent architecture)")

        except Exception as e:
            logger.error(f"Failed to initialize V2 agents: {e}")
            self.router_agent = None
            self.unified_agent = None

    def _get_database_schema(self) -> str:
        """Get comprehensive database schema information for the LLM"""
        schema_info = """
# MMA Database Schema (73,000+ fights, 36,000+ fighters)

## Core Tables:

### athletes (Fighter Information)
- id, full_name, nickname, weight_class, height, weight, reach, age, stance, headshot_url

### fights (Fight Results)
- fight_id, event_id, fighter_1_id, fighter_2_id, fighter_1_winner, fighter_2_winner
- weight_class, result_display_name, end_round, end_time, card_segment

### cards (Events)
- event_id, event_name, date, venue_name, city, country, league

### statistics_for_fights (Detailed Stats)
- athlete_id, competition_id, sigStrikesLanded, sigStrikesAttempted
- takedownsLanded, takedownsAttempted, knockDowns, submissions

### odds (Betting Information)
- fight_id, home_moneyLine_odds_current_american, away_moneyLine_odds_current_american
"""
        return schema_info

    def process_query(self, user_question: str, session_id: str = None) -> Dict[str, Any]:
        """
        Process MMA question using streamlined 2-agent workflow

        Performance: ~5-7 seconds (vs 10-15 seconds for 5-agent workflow)
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        # Check cache first
        cached_result = query_cache.get(user_question)
        if cached_result:
            logger.info(f"✅ Returning cached result for: {user_question[:50]}...")
            cached_result['cached'] = True
            return cached_result

        # Check if agents are available
        if not self.router_agent or not self.unified_agent:
            return {
                'error': 'V2 agents not configured. Check Azure OpenAI settings.',
                'success': False
            }

        try:
            # Step 1: Quick routing (1-2 seconds)
            logger.info(f"🚀 V2 Step 1: Routing query: {user_question}")
            route_info = self._route_query(user_question)

            if not route_info:
                return {'error': 'Could not route your question.', 'success': False}

            # Step 2: Check if live data needed
            if route_info.get('needs_live_data'):
                logger.info(f"🔴 V2 Step 2: Using live data service")
                return self._handle_live_data_query(user_question, route_info, session_id)

            # Step 3: Generate SQL + Analysis in ONE call (3-5 seconds)
            logger.info(f"⚡ V2 Step 2: Unified SQL + Analysis generation")
            unified_response = self._generate_unified_response(user_question, route_info)

            if not unified_response or 'sql_query' not in unified_response:
                return {'error': 'Could not generate query.', 'success': False}

            # Step 4: Execute SQL
            logger.info(f"💾 V2 Step 3: Executing SQL")
            query_results = self._execute_query(unified_response['sql_query'])

            if 'error' in query_results:
                return query_results

            # Step 5: Format final response with dynamic analysis
            logger.info(f"✨ V2 Step 4: Formatting final response")
            analysis = self._render_analysis(
                unified_response.get('analysis_template', ''),
                query_results['data'],
                user_question,
                route_info
            )

            result = {
                'success': True,
                'question': user_question,
                'sql_query': unified_response['sql_query'],
                'data': query_results['data'],
                'presentation': {
                    'format_type': unified_response.get('presentation_format', 'table'),
                    'visual_layout': unified_response.get('visual_layout', 'single'),
                    'table_headers': unified_response.get('table_headers', []),
                    'highlight_fields': unified_response.get('highlight_fields', []),
                    'primary_data': query_results['data']
                },
                'analysis': analysis,
                'row_count': len(query_results['data']),
                'cached': False,
                'session_id': session_id,
                'version': 'v2',
                'classification': {
                    'question_type': route_info.get('query_type'),
                    'confidence': 0.95
                }
            }

            # Cache and store
            query_cache.put(user_question, result)
            conversation_memory.add_interaction(session_id, user_question, result)

            logger.info(f"✅ V2 Query completed successfully")
            return result

        except Exception as e:
            logger.error(f"❌ V2 Error processing query: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'error': f'An error occurred: {str(e)}',
                'success': False
            }

    def _route_query(self, user_question: str) -> Optional[Dict]:
        """Quick routing to determine query type and data source"""
        try:
            prompt = f"""Route this MMA question: "{user_question}"

Return ONLY the JSON routing object."""

            response = self.router_agent.run(prompt)
            route_text = response.content.strip()

            logger.info(f"🔍 V2 Router response: {route_text[:200]}")

            return json.loads(route_text)

        except Exception as e:
            logger.error(f"❌ V2 Routing error: {e}")
            return None

    def _generate_unified_response(self, user_question: str, route_info: Dict) -> Optional[Dict]:
        """Generate SQL query AND analysis structure in one call"""
        try:
            prompt = f"""Generate SQL and analysis for this MMA question: "{user_question}"

Query Type: {route_info.get('query_type')}
Requires Stats: {route_info.get('requires_stats_join', False)}

Return ONLY the JSON object with sql_query, presentation_format, and analysis_template."""

            response = self.unified_agent.run(prompt)
            unified_text = response.content.strip()

            # Clean up any markdown
            if unified_text.startswith('```'):
                lines = unified_text.split('\n')
                unified_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else unified_text
            unified_text = unified_text.replace('```json', '').replace('```', '').strip()

            logger.info(f"🔍 V2 Unified response (first 300 chars): {unified_text[:300]}")

            unified_response = json.loads(unified_text)

            # Clean SQL query
            sql_query = unified_response.get('sql_query', '')
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            unified_response['sql_query'] = sql_query

            return unified_response

        except Exception as e:
            logger.error(f"❌ V2 Unified generation error: {e}")
            logger.error(f"Raw response: {unified_text if 'unified_text' in locals() else 'N/A'}")
            return None

    def _render_analysis(self, template: str, data: List[Dict], question: str, route_info: Dict) -> str:
        """Render analysis template with actual data"""
        if not data:
            return "I couldn't find any data matching your question. Try rephrasing or asking about different fighters, events, or statistics."

        try:
            # For predictions with 2 fighters, create detailed comparison
            if route_info.get('query_type') == 'prediction' and len(data) == 2:
                fighter1 = data[0]
                fighter2 = data[1]

                # Build tactical analysis
                analysis = f"""**{fighter1['full_name']} vs {fighter2['full_name']}: Tactical Breakdown**

**Physical Comparison:**
- **{fighter1['full_name']}**: {fighter1.get('height', 'N/A')}" tall, {fighter1.get('reach', 'N/A')}" reach, {fighter1.get('age', 'N/A')} years old ({fighter1.get('stance', 'N/A')})
- **{fighter2['full_name']}**: {fighter2.get('height', 'N/A')}" tall, {fighter2.get('reach', 'N/A')}" reach, {fighter2.get('age', 'N/A')} years old ({fighter2.get('stance', 'N/A')})

**Record & Experience:**
- **{fighter1['full_name']}**: {fighter1.get('wins', 0)}-{fighter1.get('losses', 0)} ({fighter1.get('total_fights', 0)} fights)
- **{fighter2['full_name']}**: {fighter2.get('wins', 0)}-{fighter2.get('losses', 0)} ({fighter2.get('total_fights', 0)} fights)

**Key Statistics:**
- **Striking**: {fighter1['full_name']} lands {fighter1.get('avg_sig_strikes', 0):.1f} sig strikes/fight vs {fighter2['full_name']}'s {fighter2.get('avg_sig_strikes', 0):.1f}
- **Takedowns**: {fighter1['full_name']} averages {fighter1.get('avg_takedowns', 0):.1f}/fight vs {fighter2['full_name']}'s {fighter2.get('avg_takedowns', 0):.1f}
- **Knockdowns**: {fighter1['full_name']} {fighter1.get('avg_knockdowns', 0):.2f}/fight vs {fighter2['full_name']} {fighter2.get('avg_knockdowns', 0):.2f}/fight
- **First Round Finishes**: {fighter1['full_name']} has {fighter1.get('rd1_finishes', 0)} vs {fighter2['full_name']}'s {fighter2.get('rd1_finishes', 0)}
- **KO Wins**: {fighter1['full_name']} has {fighter1.get('ko_wins', 0)} KO wins vs {fighter2['full_name']}'s {fighter2.get('ko_wins', 0)}

**Tactical Analysis:**
"""

                # Determine advantages
                f1_advantages = []
                f2_advantages = []

                if fighter1.get('avg_sig_strikes', 0) > fighter2.get('avg_sig_strikes', 0):
                    f1_advantages.append(f"superior striking volume ({fighter1.get('avg_sig_strikes', 0):.1f} vs {fighter2.get('avg_sig_strikes', 0):.1f})")
                else:
                    f2_advantages.append(f"superior striking volume ({fighter2.get('avg_sig_strikes', 0):.1f} vs {fighter1.get('avg_sig_strikes', 0):.1f})")

                if fighter1.get('avg_takedowns', 0) > fighter2.get('avg_takedowns', 0):
                    f1_advantages.append(f"more active wrestling ({fighter1.get('avg_takedowns', 0):.1f} TD/fight)")
                elif fighter2.get('avg_takedowns', 0) > fighter1.get('avg_takedowns', 0):
                    f2_advantages.append(f"more active wrestling ({fighter2.get('avg_takedowns', 0):.1f} TD/fight)")

                if fighter1.get('rd1_finishes', 0) > fighter2.get('rd1_finishes', 0):
                    f1_advantages.append(f"better early finishing ability ({fighter1.get('rd1_finishes', 0)} R1 finishes)")
                elif fighter2.get('rd1_finishes', 0) > fighter1.get('rd1_finishes', 0):
                    f2_advantages.append(f"better early finishing ability ({fighter2.get('rd1_finishes', 0)} R1 finishes)")

                analysis += f"\n**{fighter1['full_name']}'s Advantages:** {', '.join(f1_advantages) if f1_advantages else 'Balanced skillset'}\n"
                analysis += f"**{fighter2['full_name']}'s Advantages:** {', '.join(f2_advantages) if f2_advantages else 'Balanced skillset'}\n"

                # Path to victory
                analysis += f"\n**Path to Victory:**\n"
                analysis += f"- **{fighter1['full_name']}**: {'Early aggression with striking pressure' if fighter1.get('avg_sig_strikes', 0) > 60 else 'Tactical wrestling and control'}\n"
                analysis += f"- **{fighter2['full_name']}**: {'Fast finish in early rounds' if fighter2.get('rd1_finishes', 0) > 3 else 'Technical striking and distance management'}\n"

                return analysis

            # For other query types, use template or simple analysis
            if template and '{{' in template:
                # Simple template rendering
                rendered = template
                for key, value in (data[0] if data else {}).items():
                    rendered = rendered.replace(f'{{{{{key}}}}}', str(value))
                return rendered

            # Fallback: simple data description
            return f"Found {len(data)} result(s). The data shows {', '.join(data[0].keys())[:100]}..."

        except Exception as e:
            logger.error(f"❌ V2 Analysis rendering error: {e}")
            return f"Found {len(data)} result(s) matching your question."

    def _handle_live_data_query(self, user_question: str, route_info: Dict, session_id: str) -> Dict[str, Any]:
        """Handle queries requiring live/current data"""
        # Reuse the existing live data handling from original service
        question_lower = user_question.lower()

        try:
            if any(kw in question_lower for kw in ['next event', 'upcoming', 'scheduled']):
                live_data = live_data_service.get_upcoming_events()
                # Format and return
                # (Similar to original implementation)
                return {
                    'success': True,
                    'question': user_question,
                    'data': [],
                    'analysis': "Live data integration for upcoming events",
                    'live_data': True,
                    'version': 'v2'
                }

            return {
                'success': False,
                'error': 'Live data query not yet implemented in V2',
                'version': 'v2'
            }

        except Exception as e:
            logger.error(f"❌ V2 Live data error: {e}")
            return {
                'success': False,
                'error': f'Live data error: {str(e)}',
                'version': 'v2'
            }

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
            logger.info(f"💾 V2 Executing SQL: {sql_query[:200]}...")

            db_session = db.session
            result = db_session.execute(text(sql_query))
            rows = result.fetchall()

            # Convert to dictionaries
            data = [row_to_dict(row) for row in rows]

            logger.info(f"✅ V2 Query returned {len(data)} rows")

            return {
                'success': True,
                'data': data
            }

        except Exception as e:
            logger.error(f"❌ V2 Database error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'error': f'Database error: {str(e)}',
                'success': False
            }

# Global service instance
mma_query_service_v2 = MMAQueryServiceV2()
