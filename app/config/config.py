import os
from datetime import timedelta

class Config:
    # Base configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    
    # SQLAlchemy optimizations
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,  # Maximum number of database connections in the pool
        'pool_timeout': 30,  # Seconds to wait before giving up on getting a connection
        'pool_recycle': 1800,  # Recycle connections after 30 minutes
        'max_overflow': 2,  # Allow exceeding pool_size by up to 2 connections in high-load situations
        'echo': False,  # Don't log all SQL statements in production
    }
    
    # Caching configuration
    CACHE_TYPE = 'simple'  # Use SimpleCache by default
    CACHE_DEFAULT_TIMEOUT = 300  # Cache timeout in seconds
    
    # Performance optimizations
    PROPAGATE_EXCEPTIONS = True
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    JSON_SORT_KEYS = False  # Avoid unnecessary JSON key sorting
    
    # Logging configuration
    LOG_FORMAT = '%(asctime)s [%(request_id)s] %(levelname)s: %(message)s'
    LOG_LEVEL = 'INFO'
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 10
    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///campus_connect.db'
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'echo': True  # Log SQL statements in development
    }
    CACHE_TYPE = 'simple'
    LOG_LEVEL = 'DEBUG'
    
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    CACHE_TYPE = 'redis'  # Use Redis in production
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes cache timeout in production
    
    # Production-specific SQLAlchemy optimizations
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 20,  # Larger connection pool for production
        'max_overflow': 5,
        'pool_pre_ping': True,  # Enable connection health checks
    }
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
