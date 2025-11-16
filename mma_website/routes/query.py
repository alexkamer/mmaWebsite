"""
MMA Query Routes - Natural language query interface
"""

from flask import Blueprint, render_template, request, jsonify, session
from mma_website.services.mma_query_service_agno import mma_query_service
from mma_website.services.mma_query_service_v2 import mma_query_service_v2
from mma_website.services.query_cache import query_cache
import logging
import uuid

logger = logging.getLogger(__name__)

bp = Blueprint('query', __name__, url_prefix='/query')

@bp.route('/')
def mma_query():
    """MMA Query interface - StatMuse-like natural language queries"""
    return render_template('mma_query.html')

@bp.route('/ask', methods=['POST'])
def ask_question():
    """Process a natural language MMA question"""
    data = request.get_json()
    
    if not data or 'question' not in data:
        return jsonify({
            'error': 'No question provided',
            'success': False
        }), 400
    
    question = data['question'].strip()
    
    if not question:
        return jsonify({
            'error': 'Question cannot be empty',
            'success': False
        }), 400
    
    if len(question) > 500:
        return jsonify({
            'error': 'Question too long. Please keep it under 500 characters.',
            'success': False
        }), 400
    
    print(f"🔍 ROUTE: Processing MMA query: {question}")
    
    # Get or create session ID for conversation tracking
    if 'chat_session_id' not in session:
        session['chat_session_id'] = str(uuid.uuid4())
    
    session_id = session['chat_session_id']
    print(f"🔍 ROUTE: Using session ID: {session_id}")
    
    try:
        # Process the query using our service with conversation memory
        print(f"🔍 ROUTE: Calling mma_query_service.process_query()")
        result = mma_query_service.process_query(question, session_id)
        print(f"🔍 ROUTE: Got result: {result}")
        
        # Log the result for debugging
        if result.get('success'):
            print(f"🔍 ROUTE: Query successful. SQL: {result.get('sql_query', 'N/A')}")
            print(f"🔍 ROUTE: Returned {result.get('row_count', 0)} results")
        else:
            print(f"❌ ROUTE: Query failed: {result.get('error', 'Unknown error')}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ ROUTE: Exception in route: {e}")
        import traceback
        print(f"❌ ROUTE: Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': f'Route error: {str(e)}',
            'success': False
        })

@bp.route('/ask-v2', methods=['POST'])
def ask_question_v2():
    """Process a natural language MMA question using V2 streamlined architecture"""
    data = request.get_json()

    if not data or 'question' not in data:
        return jsonify({
            'error': 'No question provided',
            'success': False
        }), 400

    question = data['question'].strip()

    if not question:
        return jsonify({
            'error': 'Question cannot be empty',
            'success': False
        }), 400

    if len(question) > 500:
        return jsonify({
            'error': 'Question too long. Please keep it under 500 characters.',
            'success': False
        }), 400

    print(f"🚀 V2 ROUTE: Processing MMA query: {question}")

    # Get or create session ID for conversation tracking
    if 'chat_session_id' not in session:
        session['chat_session_id'] = str(uuid.uuid4())

    session_id = session['chat_session_id']
    print(f"🚀 V2 ROUTE: Using session ID: {session_id}")

    try:
        # Process the query using V2 service
        print(f"🚀 V2 ROUTE: Calling mma_query_service_v2.process_query()")
        result = mma_query_service_v2.process_query(question, session_id)
        print(f"🚀 V2 ROUTE: Got result: {result}")

        # Log the result for debugging
        if result.get('success'):
            print(f"✅ V2 ROUTE: Query successful. SQL: {result.get('sql_query', 'N/A')[:100]}")
            print(f"✅ V2 ROUTE: Returned {result.get('row_count', 0)} results")
        else:
            print(f"❌ V2 ROUTE: Query failed: {result.get('error', 'Unknown error')}")

        return jsonify(result)

    except Exception as e:
        print(f"❌ V2 ROUTE: Exception in route: {e}")
        import traceback
        print(f"❌ V2 ROUTE: Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': f'V2 Route error: {str(e)}',
            'success': False
        })

@bp.route('/examples')
def get_examples():
    """Get example questions for the interface"""
    examples = [
        {
            "category": "Fighter Records & Stats",
            "questions": [
                "What is Conor McGregor's UFC record?",
                "Tom Aspinall recent fights",
                "How many wins does Jon Jones have by submission?",
                "Who has the most knockouts in the heavyweight division?"
            ]
        },
        {
            "category": "🔴 Live & Current Events",
            "questions": [
                "Next UFC event",
                "Who's fighting this weekend?",
                "Current UFC rankings",
                "Recent fight results"
            ]
        },
        {
            "category": "Head-to-Head Comparisons", 
            "questions": [
                "Compare Jon Jones vs Daniel Cormier records",
                "Who won when Fedor fought Cro Cop?",
                "Silva vs Sonnen 1 result",
                "Compare striking stats between Adesanya and Whittaker"
            ]
        },
        {
            "category": "Rankings & Top Lists",
            "questions": [
                "Top 10 UFC finishers of all time",
                "Best heavyweight champions in UFC history",
                "Who has the longest win streak in lightweight?",
                "Most dominant title defenses"
            ]
        },
        {
            "category": "Fight Predictions & Analysis",
            "questions": [
                "Who would win between Jones and Aspinall?",
                "Best matchups for current champions",
                "Predict Adesanya vs Du Plessis",
                "Next title shot contenders by division"
            ]
        },
        {
            "category": "Techniques & Styles",
            "questions": [
                "Best submission specialists in UFC",
                "Most technical strikers in bantamweight",
                "Wrestling heavy fighters by division",
                "Highest finishing rate by technique"
            ]
        },
        {
            "category": "Events & Historical Trends",
            "questions": [
                "UFC 300 fight card results",
                "Evolution of heavyweight division",
                "Biggest upsets in UFC title fights",
                "Average fight time trends over years"
            ]
        },
        {
            "category": "Physical & Athletic Analysis",
            "questions": [
                "Tallest fighters in each division",
                "Longest reach in UFC history",
                "Age vs performance correlation",
                "Southpaw vs orthodox win rates"
            ]
        },
        {
            "category": "Knockout & Finishing Analysis",
            "questions": [
                "Most knockouts received in UFC",
                "Best comeback victories from adversity",
                "Fastest finishes in title fights",
                "Who has never been finished?"
            ]
        },
        {
            "category": "Upsets & Controversial Moments",
            "questions": [
                "Biggest betting upsets ever",
                "Most controversial judging decisions",
                "Underdog champions who shocked the world",
                "Fights that should have been stopped earlier"
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'examples': examples
    })

@bp.route('/health')
def health_check():
    """Check if the Agno-based query service is properly configured"""
    
    # Check if all Agno agents are configured
    has_agno_config = all([
        mma_query_service.question_classifier_agent is not None,
        mma_query_service.data_presentation_agent is not None,
        mma_query_service.sql_agent is not None,
        mma_query_service.mma_analyst_agent is not None
    ])
    
    # Check environment variables
    import os
    has_env_vars = all([
        os.getenv('AZURE_OPENAI_API_KEY'),
        os.getenv('AZURE_OPENAI_ENDPOINT'), 
        os.getenv('AZURE_DEPLOYMENT')
    ])
    
    return jsonify({
        'service_available': True,
        'agno_configured': has_agno_config,
        'environment_variables_set': has_env_vars,
        'database_accessible': True,  # If we got here, DB is accessible
        'schema_loaded': bool(mma_query_service.schema_context),
        'agents_available': {
            'question_classifier_agent': mma_query_service.question_classifier_agent is not None,
            'data_presentation_agent': mma_query_service.data_presentation_agent is not None,
            'sql_agent': mma_query_service.sql_agent is not None,
            'mma_analyst_agent': mma_query_service.mma_analyst_agent is not None
        }
    })

@bp.route('/cache/stats')
def cache_stats():
    """Get cache performance statistics"""
    return jsonify({
        'success': True,
        'cache_stats': query_cache.get_stats(),
        'cached_questions': query_cache.get_cached_questions()
    })

@bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the query cache"""
    query_cache.clear()
    return jsonify({
        'success': True,
        'message': 'Cache cleared successfully'
    })