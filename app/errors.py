from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

def error_response(status_code, message=None):
    """Create a JSON error response"""
    payload = {
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error'),
        'status_code': status_code
    }
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response

def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(400)
    def bad_request_error(error):
        return error_response(400, str(error.description))
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        return error_response(401, 'Authentication required')
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return error_response(403, 'Forbidden')
    
    @app.errorhandler(404)
    def not_found_error(error):
        return error_response(404, 'Resource not found')
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return error_response(405, 'Method not allowed')
    
    @app.errorhandler(422)
    def validation_error(error):
        return error_response(422, str(error.description))
    
    @app.errorhandler(429)
    def ratelimit_error(error):
        return error_response(429, 'Too many requests')
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {str(error)}')
        return error_response(500, 'Internal server error')
    
    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        app.logger.error(f'Database Error: {str(error)}')
        return error_response(500, 'Database error occurred')
    
    @app.errorhandler(IntegrityError)
    def integrity_error(error):
        app.logger.error(f'Integrity Error: {str(error)}')
        return error_response(409, 'Data integrity error')
    
    @app.errorhandler(Exception)
    def unhandled_error(error):
        app.logger.error(f'Unhandled Error: {str(error)}')
        return error_response(500, 'An unexpected error occurred')

class APIError(Exception):
    """Base class for API errors"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        rv['error'] = HTTP_STATUS_CODES.get(self.status_code, 'Unknown error')
        return rv

class ValidationError(APIError):
    """Raised when validation fails"""
    def __init__(self, message):
        super().__init__(message, status_code=422)

class AuthenticationError(APIError):
    """Raised when authentication fails"""
    def __init__(self, message='Authentication required'):
        super().__init__(message, status_code=401)

class AuthorizationError(APIError):
    """Raised when authorization fails"""
    def __init__(self, message='Permission denied'):
        super().__init__(message, status_code=403)

class ResourceNotFoundError(APIError):
    """Raised when a resource is not found"""
    def __init__(self, message='Resource not found'):
        super().__init__(message, status_code=404)

class ResourceExistsError(APIError):
    """Raised when attempting to create a duplicate resource"""
    def __init__(self, message='Resource already exists'):
        super().__init__(message, status_code=409)

class RateLimitError(APIError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message='Too many requests'):
        super().__init__(message, status_code=429)
