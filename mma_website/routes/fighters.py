from flask import Blueprint, render_template, request, redirect, url_for, abort, jsonify
from mma_website.services.fighter_service import get_fighter_data
from mma_website.services.fighter_timeline import get_fighter_timeline
from mma_website.utils.text_utils import row_to_dict
from sqlalchemy import text
from mma_website import db
import logging

# Configure logging
logger = logging.getLogger(__name__)

bp = Blueprint('fighters', __name__, url_prefix='/fighter')

@bp.route('/<int:fighter_id>/timeline')
def fighter_timeline(fighter_id):
    """Display a fighter's career timeline with fights and rankings history"""
    try:
        # Validate fighter_id
        if fighter_id <= 0:
            logger.warning(f"Invalid fighter_id: {fighter_id}")
            return redirect(url_for('main.fighters'))
        
        fighter_data = get_fighter_timeline(fighter_id)
        if not fighter_data:
            logger.info(f"Fighter not found: {fighter_id}")
            return redirect(url_for('main.fighters'))
        
        return render_template('career_timeline.html', 
                             fighter=fighter_data,
                             timeline_events=fighter_data.get('timeline_events', []))
    except Exception as e:
        logger.error(f"Error in fighter_timeline: {str(e)}")
        return render_template('error.html', 
                             message="An error occurred while loading the fighter timeline",
                             error=str(e) if bp.debug else None)

@bp.route('/<int:fighter_id>')
def fighter_page(fighter_id):
    """Display a fighter's profile with stats and fight history"""
    try:
        # Validate fighter_id
        if fighter_id <= 0:
            logger.warning(f"Invalid fighter_id: {fighter_id}")
            return redirect(url_for('main.fighters'))
        
        # Get filter parameters from request
        filters = {
            'promotion': request.args.get('promotion', 'all'),
            'rounds_format': request.args.get('rounds_format', 'all'),
            'fight_type': request.args.get('fight_type', 'all'),
            'weight_class': request.args.get('weight_class', 'all'),
            'odds_type': request.args.get('odds_type', 'all')
        }
        
        # Get fighter data with the specified filters
        fighter = get_fighter_data(fighter_id, filters)
        
        if not fighter:
            logger.info(f"Fighter not found: {fighter_id}")
            return redirect(url_for('main.fighters'))
        
        return render_template('fighter.html', fighter=fighter)
    except Exception as e:
        logger.error(f"Error in fighter_page: {str(e)}")
        return render_template('error.html', 
                             message="An error occurred while loading the fighter page",
                             error=str(e) if bp.debug else None)

# Error handlers
@bp.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', message="Fighter not found"), 404

@bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return render_template('error.html', message="An internal error occurred"), 500

# Debug flag - should be False in production
bp.debug = False