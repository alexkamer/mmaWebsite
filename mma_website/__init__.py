from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
import os
import secrets
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
cache = Cache()

def create_app(config_name=None):
    # Get the project root directory (parent of mma_website package)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(__name__,
                template_folder=os.path.join(project_root, 'templates'),
                static_folder=os.path.join(project_root, 'static'))

    # Configuration
    app.secret_key = secrets.token_hex(16)

    # Database configuration
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'mma.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Cache configuration (simple in-memory cache)
    app.config['CACHE_TYPE'] = 'SimpleCache'  # Use 'RedisCache' for production
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes default

    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)

    # Register blueprints
    from mma_website.routes import main, fighters, events, api, games, query, analytics
    app.register_blueprint(main.bp)
    app.register_blueprint(fighters.bp)
    app.register_blueprint(events.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(games.bp)
    app.register_blueprint(query.bp)
    app.register_blueprint(analytics.bp)

    # Add custom filters
    app.jinja_env.filters['format_date'] = format_date

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