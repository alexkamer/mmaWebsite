"""
Analytics Routes - Dashboard for MMA Intelligence usage and performance
"""

from flask import Blueprint, render_template, jsonify
from mma_website.services.query_cache import query_cache
from mma_website.services.conversation_memory import conversation_memory
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp.route('/')
def dashboard():
    """Analytics dashboard for MMA Intelligence"""
    return render_template('analytics_dashboard.html')

@bp.route('/api/stats')
def get_analytics_data():
    """Get comprehensive analytics data for the dashboard"""
    
    # Get cache statistics
    cache_stats = query_cache.get_stats()
    
    # Get conversation memory stats
    memory_stats = conversation_memory.get_stats()
    
    # Get cached questions for popular queries analysis
    cached_questions = query_cache.get_cached_questions()
    
    # Analyze question types from cached queries
    question_types = {}
    for question_info in cached_questions:
        q_type = question_info.get('question_type', 'unknown')
        question_types[q_type] = question_types.get(q_type, 0) + 1
    
    # Calculate performance metrics
    total_requests = cache_stats.get('hit_count', 0) + cache_stats.get('miss_count', 0)
    
    analytics_data = {
        'overview': {
            'total_queries': total_requests,
            'cache_hit_rate': cache_stats.get('hit_rate', '0%'),
            'active_sessions': memory_stats.get('active_sessions', 0),
            'cached_results': cache_stats.get('cache_size', 0),
            'last_updated': datetime.now().isoformat()
        },
        'cache_performance': {
            'hits': cache_stats.get('hit_count', 0),
            'misses': cache_stats.get('miss_count', 0),
            'hit_rate_numeric': float(cache_stats.get('hit_rate', '0%').rstrip('%')),
            'cache_size': cache_stats.get('cache_size', 0),
            'max_size': cache_stats.get('max_size', 100)
        },
        'conversation_stats': {
            'active_sessions': memory_stats.get('active_sessions', 0),
            'total_interactions': memory_stats.get('total_interactions', 0),
            'session_timeout_minutes': memory_stats.get('session_timeout_minutes', 30)
        },
        'popular_question_types': question_types,
        'recent_queries': [
            {
                'question': q.get('question', '')[:100] + ('...' if len(q.get('question', '')) > 100 else ''),
                'type': q.get('question_type', 'unknown'),
                'cached_at': q.get('cached_at', '')
            }
            for q in cached_questions[-10:]  # Last 10 cached queries
        ]
    }
    
    return jsonify({
        'success': True,
        'data': analytics_data
    })

@bp.route('/api/clear-cache', methods=['POST'])
def clear_all_caches():
    """Clear all caches for testing purposes"""
    try:
        query_cache.clear()
        conversation_memory.conversations.clear()
        
        return jsonify({
            'success': True,
            'message': 'All caches cleared successfully'
        })
    except Exception as e:
        logger.error(f"Error clearing caches: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500