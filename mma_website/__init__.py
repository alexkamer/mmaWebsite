from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
import os
from datetime import datetime
from mma_website.utils.logger import setup_logger
from mma_website.config import get_config

# Initialize extensions
db = SQLAlchemy()
cache = Cache()

def create_app(config_name=None):
    # Get the project root directory (parent of mma_website package)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(__name__,
                template_folder=os.path.join(project_root, 'templates'),
                static_folder=os.path.join(project_root, 'static'))

    # Load configuration from config.py
    config_class = get_config(config_name)

    # Validate production config if needed
    if config_name == 'production' and hasattr(config_class, 'validate'):
        config_class.validate()

    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)

    # Setup logging
    logger = setup_logger(app, log_level=os.getenv('LOG_LEVEL', 'INFO'))
    logger.info(f"MMA Website initialized (Config: {config_name or 'default'})")

    # Register blueprints
    from mma_website.routes import main, fighters, events, api, games, query, analytics, health, admin
    app.register_blueprint(main.bp)
    app.register_blueprint(fighters.bp)
    app.register_blueprint(events.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(games.bp)
    app.register_blueprint(query.bp)
    app.register_blueprint(analytics.bp)
    app.register_blueprint(health.bp)
    app.register_blueprint(admin.bp)

    # Setup rate limiting
    if app.config.get('RATELIMIT_ENABLED', True):
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[app.config.get('RATELIMIT_DEFAULT', '200 per hour')],
            storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://'),
        )
        logger.info("Rate limiting enabled")

        # Store limiter for access in routes
        app.limiter = limiter

    # Add custom filters
    app.jinja_env.filters['format_date'] = format_date

    # Add cache headers for static files
    @app.after_request
    def add_cache_headers(response):
        """Add cache headers for static assets"""
        if request.path.startswith('/static/'):
            # Cache static files for 1 year (immutable)
            response.cache_control.max_age = 31536000
            response.cache_control.public = True
            response.cache_control.immutable = True
        elif request.path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico')):
            # Cache images for 1 week
            response.cache_control.max_age = 604800
            response.cache_control.public = True
        return response

    # Initialize scheduler (only if not in testing mode and in main process)
    if not app.config.get('TESTING', False) and app.config.get('SCHEDULER_ENABLED', True):
        import atexit
        from mma_website.tasks.scheduler import init_scheduler, shutdown_scheduler

        # Initialize in a way that works with Flask's reloader
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
            init_scheduler(app)
            atexit.register(shutdown_scheduler)
            logger.info("Task scheduler initialized")

    return app

def format_date(date_str):
    """Format date string for display"""
    try:
        # Split on space to remove time component
        date_part = date_str.split()[0]
        date_obj = datetime.strptime(date_part, '%Y-%m-%d')
        return date_obj.strftime('%m-%d-%Y')
    except:
        return date_str 