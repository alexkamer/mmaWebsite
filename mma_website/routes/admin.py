"""Admin routes for data management"""
from flask import Blueprint, jsonify, request, render_template
from mma_website import db, cache
from mma_website.services.rankings_update_service import get_rankings_service
from mma_website.tasks.scheduler import get_scheduled_jobs
from mma_website.tasks.update_tasks import (
    run_incremental_update,
    run_post_event_update,
    run_odds_update,
    get_last_update_times
)
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/rankings/update', methods=['POST'])
def trigger_rankings_update():
    """
    Manually trigger rankings update

    Returns:
        JSON response with update statistics
    """
    logger.info("Manual rankings update triggered")

    try:
        service = get_rankings_service()

        # Check if update is needed
        force = request.args.get('force', 'false').lower() == 'true'

        if not force and not service.needs_update(hours=1):
            last_update = service.get_last_update_time()
            return jsonify({
                'success': False,
                'message': 'Rankings were recently updated. Use force=true to override.',
                'last_update': last_update.isoformat() if last_update else None
            }), 429

        # Perform update
        stats = service.update_rankings()

        return jsonify({
            'success': True,
            'message': 'Rankings updated successfully',
            'stats': {
                'divisions_processed': stats['total_divisions'],
                'rankings_updated': stats['updated_rankings'],
                'new_fighters': stats['new_fighters'],
                'errors': stats['errors'],
                'duration_seconds': (stats['end_time'] - stats['start_time']).total_seconds()
            }
        }), 200

    except Exception as e:
        logger.error(f"Error updating rankings: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/rankings/status')
def rankings_status():
    """
    Get rankings update status

    Returns:
        JSON response with current rankings status
    """
    try:
        service = get_rankings_service()
        last_update = service.get_last_update_time()
        needs_update = service.needs_update(hours=24)

        # Get count of current rankings
        result = db.session.execute(db.text("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT division) as divisions
            FROM ufc_rankings
        """)).fetchone()

        return jsonify({
            'last_update': last_update.isoformat() if last_update else None,
            'needs_update': needs_update,
            'total_rankings': result[0] if result else 0,
            'divisions_count': result[1] if result else 0
        }), 200

    except Exception as e:
        logger.error(f"Error getting rankings status: {e}", exc_info=True)
        return jsonify({
            'error': str(e)
        }), 500


@bp.route('/scheduler/status')
def scheduler_status():
    """
    Get scheduler status and scheduled jobs

    Returns:
        JSON response with scheduler information
    """
    try:
        jobs = get_scheduled_jobs()

        return jsonify({
            'enabled': len(jobs) > 0,
            'jobs': jobs
        }), 200

    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}", exc_info=True)
        return jsonify({
            'error': str(e)
        }), 500


@bp.route('/data/stats')
def data_stats():
    """
    Get overall data statistics

    Returns:
        JSON response with database statistics
    """
    try:
        # Get various counts
        stats = {}

        # Fighters count
        result = db.session.execute(db.text("SELECT COUNT(*) FROM athletes")).fetchone()
        stats['fighters'] = result[0]

        # Events count
        result = db.session.execute(db.text("SELECT COUNT(*) FROM cards")).fetchone()
        stats['events'] = result[0]

        # Fights count
        result = db.session.execute(db.text("SELECT COUNT(*) FROM fights")).fetchone()
        stats['fights'] = result[0]

        # Rankings count
        result = db.session.execute(db.text("SELECT COUNT(*) FROM ufc_rankings")).fetchone()
        stats['rankings'] = result[0]

        # Last fight date
        result = db.session.execute(db.text("""
            SELECT MAX(c.date) FROM cards c
            JOIN fights f ON c.event_id = f.event_id
        """)).fetchone()
        stats['last_fight_date'] = result[0] if result else None

        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error getting data stats: {e}", exc_info=True)
        return jsonify({
            'error': str(e)
        }), 500


@bp.route('/updates/incremental', methods=['POST'])
def trigger_incremental_update():
    """
    Manually trigger incremental database update

    Returns:
        JSON response with update statistics
    """
    logger.info("Manual incremental update triggered")

    try:
        result = run_incremental_update()

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Incremental update completed successfully',
                'stats': result['stats'],
                'timestamp': result['timestamp']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'timestamp': result['timestamp']
            }), 500

    except Exception as e:
        logger.error(f"Error triggering incremental update: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/updates/post-event', methods=['POST'])
def trigger_post_event_update():
    """
    Manually trigger post-event update

    Returns:
        JSON response with update statistics
    """
    logger.info("Manual post-event update triggered")

    try:
        result = run_post_event_update()

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Post-event update completed successfully',
                'stats': result['stats'],
                'timestamp': result['timestamp']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'timestamp': result['timestamp']
            }), 500

    except Exception as e:
        logger.error(f"Error triggering post-event update: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/updates/odds', methods=['POST'])
def trigger_odds_update():
    """
    Manually trigger odds update

    Returns:
        JSON response with update statistics
    """
    logger.info("Manual odds update triggered")

    try:
        result = run_odds_update()

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Odds update completed successfully',
                'odds_checked': result.get('odds_checked', 0),
                'timestamp': result['timestamp']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'timestamp': result['timestamp']
            }), 500

    except Exception as e:
        logger.error(f"Error triggering odds update: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/updates/status')
def updates_status():
    """
    Get status of all data update jobs

    Returns:
        JSON response with update timestamps and scheduled jobs
    """
    try:
        # Get last update times from database
        last_updates = get_last_update_times()

        # Get scheduled jobs
        scheduled_jobs = get_scheduled_jobs()

        return jsonify({
            'success': True,
            'last_updates': last_updates,
            'scheduled_jobs': scheduled_jobs
        }), 200

    except Exception as e:
        logger.error(f"Error getting updates status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """
    Clear application cache

    Returns:
        JSON response with cache clear status
    """
    logger.info("Manual cache clear triggered")

    try:
        cache.clear()
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/dashboard')
def admin_dashboard():
    """
    Admin dashboard UI for managing data updates

    Returns:
        HTML page with admin controls
    """
    return render_template('admin_dashboard.html')
