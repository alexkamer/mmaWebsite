"""Health check and monitoring endpoints"""
from flask import Blueprint, jsonify, current_app
from mma_website import db
from sqlalchemy import text
import os
import time

bp = Blueprint('health', __name__)


@bp.route('/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'mma-website',
        'timestamp': time.time()
    }), 200


@bp.route('/health/detailed')
def detailed_health():
    """Detailed health check with component status"""
    health_status = {
        'status': 'healthy',
        'service': 'mma-website',
        'timestamp': time.time(),
        'checks': {}
    }

    # Check database connection
    try:
        db.session.execute(text('SELECT 1'))
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }

    # Check database file exists (for SQLite)
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if 'sqlite' in db_uri:
        db_path = db_uri.replace('sqlite:///', '')
        health_status['checks']['database_file'] = {
            'status': 'healthy' if os.path.exists(db_path) else 'unhealthy',
            'path': db_path,
            'exists': os.path.exists(db_path),
            'size_mb': round(os.path.getsize(db_path) / (1024*1024), 2) if os.path.exists(db_path) else 0
        }

    # Check cache
    try:
        from mma_website import cache
        cache.set('health_check', 'ok', timeout=10)
        cached_value = cache.get('health_check')
        health_status['checks']['cache'] = {
            'status': 'healthy' if cached_value == 'ok' else 'degraded',
            'message': 'Cache is working'
        }
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'degraded',
            'message': f'Cache check failed: {str(e)}'
        }

    # Check logs directory
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    health_status['checks']['logs'] = {
        'status': 'healthy' if os.path.exists(log_dir) else 'degraded',
        'path': log_dir,
        'writable': os.access(log_dir, os.W_OK) if os.path.exists(log_dir) else False
    }

    # Overall status
    if any(check.get('status') == 'unhealthy' for check in health_status['checks'].values()):
        health_status['status'] = 'unhealthy'
        return jsonify(health_status), 503
    elif any(check.get('status') == 'degraded' for check in health_status['checks'].values()):
        health_status['status'] = 'degraded'
        return jsonify(health_status), 200

    return jsonify(health_status), 200


@bp.route('/health/ready')
def readiness_check():
    """Readiness check for Kubernetes/container orchestration"""
    try:
        # Check if we can query the database
        result = db.session.execute(text('SELECT COUNT(*) FROM athletes LIMIT 1'))
        count = result.scalar()

        return jsonify({
            'status': 'ready',
            'database': 'connected',
            'data_loaded': count > 0
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'error': str(e)
        }), 503


@bp.route('/health/live')
def liveness_check():
    """Liveness check for Kubernetes/container orchestration"""
    # Simple check - if the app is running, it's alive
    return jsonify({
        'status': 'alive',
        'timestamp': time.time()
    }), 200
