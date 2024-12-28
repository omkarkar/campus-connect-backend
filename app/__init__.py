from flask import Flask, request, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_caching import Cache
import logging
from logging.handlers import RotatingFileHandler
import os
import uuid
from time import time
from functools import wraps

from .models import db
from .schemas import ma
from .config.config import config

# Initialize Flask-Caching
cache = Cache()

def request_id_filter():
    """Add request ID to log records"""
    return {'request_id': getattr(g, 'request_id', '-')}

class RequestFormatter(logging.Formatter):
    """Custom formatter that includes request ID"""
    def format(self, record):
        record.request_id = getattr(g, 'request_id', '-')
        return super().format(record)

def performance_logging(f):
    """Decorator to log request performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time()
        response = f(*args, **kwargs)
        duration = time() - start_time
        current_app.logger.info(f'Request completed in {duration:.2f}s')
        return response
    return decorated_function

def create_app(config_name='default'):
    """Application factory function with performance optimizations"""
    """Application factory function"""
    
    # Initialize Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app)  # Enable CORS
    db.init_app(app)  # Initialize SQLAlchemy
    ma.init_app(app)  # Initialize Marshmallow
    Migrate(app, db)  # Initialize Flask-Migrate
    cache.init_app(app)  # Initialize Flask-Caching
    
    # Request ID middleware
    @app.before_request
    def before_request():
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        g.start_time = time()
    
    @app.after_request
    def after_request(response):
        # Add request ID to response headers
        response.headers['X-Request-ID'] = g.request_id
        
        # Log request performance
        duration = time() - g.start_time
        app.logger.info(f'Request {request.method} {request.path} completed in {duration:.2f}s')
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    # Setup enhanced logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Configure rotating file handler with custom formatter
        file_handler = RotatingFileHandler(
            'logs/campus_connect.log',
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(RequestFormatter(app.config['LOG_FORMAT']))
        file_handler.setLevel(app.config['LOG_LEVEL'])
        app.logger.addHandler(file_handler)
        
        # Set application log level
        app.logger.setLevel(app.config['LOG_LEVEL'])
        app.logger.info('Campus Connect startup', extra={'request_id': 'startup'})
    
    # Register blueprints
    from .controllers.user_controller import user_bp
    from .controllers.course_controller import course_bp
    from .controllers.assignment_controller import assignment_bp
    from .controllers.chat_controller import chat_bp
    from .controllers.message_controller import message_bp
    from .controllers.media_controller import media_bp
    from .controllers.notification_controller import notification_bp
    from .controllers.group_event_controller import group_event_bp
    
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(course_bp, url_prefix='/api/courses')
    app.register_blueprint(assignment_bp, url_prefix='/api/assignments')
    app.register_blueprint(chat_bp, url_prefix='/api/chats')
    app.register_blueprint(message_bp, url_prefix='/api/messages')
    app.register_blueprint(media_bp, url_prefix='/api/media')
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    app.register_blueprint(group_event_bp, url_prefix='/api/group-events')
    
    # Register error handlers
    from .errors import register_error_handlers
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

def init_services():
    """Initialize all services"""
    from .services import (
        UserService,
        CourseService,
        AssignmentService,
        ChatService,
        MessageService,
        MediaService,
        NotificationService,
        GroupEventService
    )
    
    return {
        'user_service': UserService(),
        'course_service': CourseService(),
        'assignment_service': AssignmentService(),
        'chat_service': ChatService(),
        'message_service': MessageService(),
        'media_service': MediaService(),
        'notification_service': NotificationService(),
        'group_event_service': GroupEventService()
    }

# Initialize services
services = init_services()

# Export services
user_service = services['user_service']
course_service = services['course_service']
assignment_service = services['assignment_service']
chat_service = services['chat_service']
message_service = services['message_service']
