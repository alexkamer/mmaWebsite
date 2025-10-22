"""
MMA Query Service - Natural language to SQL query generation using Azure OpenAI
Similar to StatMuse but for MMA data
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from sqlalchemy import text
from mma_website import db
from mma_website.utils.text_utils import row_to_dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure OpenAI integration (will be imported when available)
try:
    from openai import AzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False
    AzureOpenAI = None

logger = logging.getLogger(__name__)

class MMAQueryService:
    """Service for processing natural language MMA queries and generating SQL responses"""
    
    def __init__(self):
        self.client = None
        if AZURE_OPENAI_AVAILABLE:
            self.setup_azure_client()
        
        # Database schema context for the LLM
        self.schema_context = self._get_database_schema()
        
    def setup_azure_client(self):
        """Initialize Azure OpenAI client"""
        try:
            # These should be set as environment variables
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
            
            if not api_key or not endpoint:
                logger.warning("Azure OpenAI credentials not found in environment variables")
                return
                
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=endpoint
            )
            logger.info("Azure OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            self.client = None
    
    def _get_database_schema(self) -> str:
        """Get comprehensive database schema information for the LLM"""
        schema_info = """
# MMA Database Schema

## Core Tables:

### athletes
- id: Fighter unique identifier
- full_name: Fighter's full name
- nickname: Fighter's nickname
- weight_class: Fighter's primary weight class
- height: Fighter's height
- weight: Fighter's weight
- reach: Fighter's reach
- age: Fighter's age
- stance: Fighting stance (Orthodox, Southpaw, etc.)
- association: Fighter's gym/team
- default_league: Primary promotion (ufc, bellator, etc.)
- headshot_url: Fighter photo URL

### fights
- fight_id: Unique fight identifier
- event_id: Event identifier
- fighter_1_id: First fighter ID
- fighter_2_id: Second fighter ID
- fighter_1_winner: 1 if fighter 1 won, 0 if lost
- fighter_2_winner: 1 if fighter 2 won, 0 if lost
- weight_class: Fight weight class
- result_display_name: Fight result method (KO, TKO, Submission, Decision, etc.)
- end_round: Round the fight ended
- end_time: Time in round when fight ended
- card_segment: Position on card (Main Card, Preliminary Card, etc.)

### cards (events)
- event_id: Unique event identifier
- event_name: Name of the event
- date: Event date
- venue_name: Venue name
- city: Event city
- country: Event country
- league: Promotion (ufc, bellator, etc.)

### odds
- fight_id: Fight identifier
- home_athlete_id: Home fighter ID
- away_athlete_id: Away fighter ID
- home_moneyLine_odds_current_american: Home fighter odds
- away_moneyLine_odds_current_american: Away fighter odds
- home_favorite: 1 if home fighter is favorite
- away_favorite: 1 if away fighter is favorite

### statistics_for_fights
- athlete_id: Fighter ID
- competition_id: Fight ID (same as fight_id)
- event_id: Event ID
- sigStrikesLanded: Significant strikes landed
- sigStrikesAttempted: Significant strikes attempted
- totalStrikesLanded: Total strikes landed
- totalStrikesAttempted: Total strikes attempted
- takedownsLanded: Takedowns successful
- takedownsAttempted: Takedown attempts
- knockDowns: Knockdowns scored
- submissions: Submission attempts

### ufc_rankings
- fighter_id: Fighter ID
- division: Weight class division
- rank: Current ranking (1-15, or 'C' for champion)
- fighter_name: Fighter name

## Weight Classes:
Men's: Heavyweight, Light Heavyweight, Middleweight, Welterweight, Lightweight, Featherweight, Bantamweight, Flyweight
Women's: Women's Featherweight, Women's Bantamweight, Women's Flyweight, Women's Strawweight, Women's Atomweight

## Common Query Patterns:
- Fighter records: Use fighter_1_winner/fighter_2_winner to determine wins/losses
- Fight finishes: Look for result_display_name containing 'KO', 'TKO', 'Submission'
- Recent fights: Order by cards.date DESC
- Fighter vs Fighter: Match both fighter IDs in fights table
- Rankings: Use ufc_rankings table for current standings
"""
        return schema_info
    
    def process_query(self, user_question: str) -> Dict[str, Any]:
        """
        Process a natural language MMA question and return structured response
        
        Args:
            user_question: User's natural language question
            
        Returns:
            Dict containing query results, SQL used, and formatted response
        """
        if not self.client:
            return {
                'error': 'Azure OpenAI not configured. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables.',
                'success': False
            }
        
        try:
            # Generate SQL query from natural language
            sql_query = self._generate_sql_query(user_question)
            
            if not sql_query:
                return {
                    'error': 'Could not generate a valid SQL query from your question.',
                    'success': False
                }
            
            # Execute the query
            query_results = self._execute_query(sql_query)
            
            if 'error' in query_results:
                return query_results
            
            # Generate natural language response
            response_text = self._generate_response(user_question, sql_query, query_results['data'])
            
            return {
                'success': True,
                'question': user_question,
                'sql_query': sql_query,
                'data': query_results['data'],
                'response': response_text,
                'row_count': len(query_results['data']) if query_results['data'] else 0
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'error': f'An error occurred while processing your question: {str(e)}',
                'success': False
            }
    
    def _generate_sql_query(self, user_question: str) -> Optional[str]:
        """Generate SQL query from natural language using Azure OpenAI"""
        
        system_prompt = f"""You are an expert SQL query generator for an MMA (Mixed Martial Arts) database. 
Your job is to convert natural language questions into valid SQLite queries.

{self.schema_context}

IMPORTANT RULES:
1. ONLY return the SQL query, no explanations or markdown
2. Use proper SQLite syntax
3. Always use JOIN operations when accessing multiple tables
4. For fighter records, use UNION to combine fighter_1 and fighter_2 perspectives
5. Use LIKE for partial string matching (case insensitive with LOWER())
6. Limit results to reasonable numbers (use LIMIT clause)
7. For fighter vs fighter queries, check both fighter_1_id/fighter_2_id combinations
8. Use proper date formatting for date comparisons
9. For win/loss records, count fighter_1_winner=1 or fighter_2_winner=1 as wins

Example query patterns:
- Fighter record: SELECT wins, losses FROM (complex UNION query)
- Recent fights: JOIN fights f with cards c ON f.event_id = c.event_id ORDER BY c.date DESC
- Fighter comparisons: Complex query with multiple JOINs
"""

        user_prompt = f"""Convert this MMA question to a SQL query: "{user_question}"

Return ONLY the SQL query, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4-1'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the response (remove markdown if present)
            if sql_query.startswith('```'):
                sql_query = sql_query.split('\n')[1:-1]
                sql_query = '\n'.join(sql_query)
            
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            return None
    
    def _execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query safely and return results"""
        
        # Basic SQL injection prevention
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = sql_query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return {
                    'error': f'Query contains dangerous keyword: {keyword}',
                    'success': False
                }
        
        try:
            db_session = db.session
            
            # Execute query with a reasonable timeout
            result = db_session.execute(text(sql_query))
            rows = result.fetchall()
            
            # Convert to dictionaries for easier handling
            data = [row_to_dict(row) for row in rows]
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return {
                'error': f'Database error: {str(e)}',
                'success': False
            }
    
    def _generate_response(self, question: str, sql_query: str, data: list[dict]) -> str:
        """Generate natural language response from query results"""
        
        if not data:
            return "I couldn't find any data matching your question. Try rephrasing or asking about something else."
        
        # Create a summary of the data for the LLM
        data_summary = {
            'row_count': len(data),
            'columns': list(data[0].keys()) if data else [],
            'sample_rows': data[:5],  # First 5 rows
            'has_more': len(data) > 5
        }
        
        system_prompt = """You are an MMA expert analyst. Given a user question, SQL query, and query results, 
provide a clear, informative response in natural language. 

Guidelines:
1. Answer the specific question asked
2. Present data in an organized, easy-to-read format
3. Include relevant statistics and insights
4. Use proper MMA terminology
5. If there are many results, summarize the key findings
6. Be conversational but authoritative
7. Add context when helpful (e.g., "This is impressive because...")
"""

        user_prompt = f"""
Question: {question}

Query Results Summary:
- Found {data_summary['row_count']} results
- Columns: {', '.join(data_summary['columns'])}

Data:
{json.dumps(data_summary['sample_rows'], indent=2)}

{'(Showing first 5 of ' + str(data_summary['row_count']) + ' results)' if data_summary['has_more'] else ''}

Please provide a clear, informative response to the user's question based on this data.
"""

        try:
            response = self.client.chat.completions.create(
                model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4-1'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Found {len(data)} results for your query, but I couldn't generate a detailed response. Here's the raw data: {data[:3]}"

# Global service instance
mma_query_service = MMAQueryService()