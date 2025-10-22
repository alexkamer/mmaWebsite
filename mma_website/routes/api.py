from flask import Blueprint, jsonify, request
from mma_website import cache
from mma_website.services.fighter_service import get_fighter_data
from mma_website.services.api_service import search_fighters, get_fight_details
import logging

# Configure logging
logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/fighter/<int:fighter_id>')
@cache.cached(timeout=1800)  # Cache for 30 minutes
def get_fighter(fighter_id):
    """API endpoint to get fighter data"""
    try:
        if fighter_id <= 0:
            return jsonify({"error": "Invalid fighter ID"}), 400

        fighter = get_fighter_data(fighter_id)
        if fighter:
            return jsonify(fighter)
        return jsonify({"error": "Fighter not found"}), 404
    except Exception as e:
        logger.error(f"Error in get_fighter: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/fighters/search')
@cache.cached(timeout=300, query_string=True)  # Cache search results for 5 minutes
def search_fighters_route():
    """API endpoint to search fighters"""
    try:
        query = request.args.get('q', '').strip()

        # Validate query parameter
        if not query:
            return jsonify({"error": "Search query is required"}), 400

        # Minimum query length
        if len(query) < 2:
            return jsonify([])

        # Get limit parameter with validation
        try:
            limit = request.args.get('limit', 10, type=int)
            if limit <= 0 or limit > 50:
                limit = 10  # Reset to default if invalid
        except (ValueError, TypeError):
            limit = 10

        results = search_fighters(query, limit)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in search_fighters: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/fight-stats/<fight_id>')
def get_fight_stats(fight_id):
    """API endpoint to get fight statistics"""
    try:
        # Validate fight_id format
        if not fight_id or '_' not in fight_id:
            return jsonify({"error": "Invalid fight ID format"}), 400
            
        fight = get_fight_details(fight_id)
        
        if not fight:
            return jsonify({"error": "Fight not found"}), 404
            
        return jsonify(fight)
    except Exception as e:
        logger.error(f"Error in get_fight_stats: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Error handlers
@bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500