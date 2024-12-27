from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os

from .models import db
from .schemas import ma
from .config.config import config

def create_app(config_name='default'):
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
    
    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/campus_connect.log',
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Campus Connect startup')
    
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
media_service = services['media_service']
notification_service = services['notification_service']
group_event_service = services['group_event_service']
