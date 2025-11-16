"""Configuration management for MMA Website"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration"""
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')

    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() in ('true', '1', 'yes')

    # Cache settings
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'SimpleCache')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Rate limiting
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'True').lower() in ('true', '1', 'yes')
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200 per hour')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_TO_STDOUT = os.getenv('LOG_TO_STDOUT', 'True').lower() in ('true', '1', 'yes')

    # Azure OpenAI Configuration (for AI features)
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_DEPLOYMENT = os.getenv('AZURE_DEPLOYMENT', 'gpt-4-1')
    AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4-1')

    # ESPN API settings
    ESPN_API_BASE_URL = 'https://sports.core.api.espn.com/v2/sports/mma'
    ESPN_API_TIMEOUT = int(os.getenv('ESPN_API_TIMEOUT', 10))

    # Scheduler settings
    SCHEDULER_ENABLED = os.getenv('SCHEDULER_ENABLED', 'True').lower() in ('true', '1', 'yes')
    RANKINGS_UPDATE_CRON = os.getenv('RANKINGS_UPDATE_CRON', '0 3 * * *')  # Daily at 3 AM UTC


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries

    # Set database URI as class attribute
    _db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'mma.db'
    )
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{_db_path}'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    CACHE_TYPE = 'SimpleCache'
    RATELIMIT_ENABLED = False  # Disable rate limiting in tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Get configuration from environment - validate at import time
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Use Redis for caching in production
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', os.getenv('REDIS_URL'))  # Will be validated

    # Use Redis for rate limiting
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')

    # Database - PostgreSQL or fallback to SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "mma.db")}'

    @classmethod
    def validate(cls):
        """Validate production configuration"""
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production")
        if not os.getenv('REDIS_URL'):
            print("WARNING: REDIS_URL not set in production. Using fallback configuration.")

    # Production-specific settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration based on environment or explicit name"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    return config.get(config_name, config['default'])
