from flask import Blueprint, request, jsonify, g, current_app
from marshmallow import ValidationError
from functools import wraps
from datetime import datetime

from ..services import user_service
from ..schemas.user import (
    user_schema,
    users_schema,
    user_profile_schema,
    users_profile_schema,
    user_login_schema
)

user_bp = Blueprint('user', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(g, 'current_user', None):
            return jsonify({'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        user = user_schema.load(data)
        created_user = user_service.create_user(user_schema.dump(user))
        return jsonify(user_profile_schema.dump(created_user)), 201
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"Error in user registration: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = user_login_schema.load(request.get_json())
        user = user_service.authenticate(data['email'], data['password'])
        if user:
            # Here you would typically generate and return a JWT token
            return jsonify({
                'message': 'Login successful',
                'user': user_profile_schema.dump(user)
            }), 200
        return jsonify({'message': 'Invalid credentials'}), 401
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"Error in user login: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user's profile"""
    try:
        return jsonify(user_profile_schema.dump(g.current_user)), 200
    except Exception as e:
        current_app.logger.error(f"Error getting user profile: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update current user's profile"""
    try:
        data = request.get_json()
        updated_user = user_service.update(g.current_user.user_id, data)
        return jsonify(user_profile_schema.dump(updated_user)), 200
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating user profile: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@user_bp.route('/search', methods=['GET'])
@login_required
def search_users():
    """Search users by name or email"""
    try:
        query = request.args.get('q', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        result = user_service.search_users(query, page, per_page)
        return jsonify({
            'users': users_profile_schema.dump(result['items']),
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error searching users: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@user_bp.route('/password', methods=['PUT'])
@login_required
def update_password():
    """Update user's password"""
    try:
        data = request.get_json()
        if user_service.update_password(
            g.current_user.user_id,
            data['old_password'],
            data['new_password']
        ):
            return jsonify({'message': 'Password updated successfully'}), 200
        return jsonify({'message': 'Invalid old password'}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating password: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@user_bp.route('/courses', methods=['GET'])
@login_required
def get_user_courses():
    """Get current user's courses"""
    try:
        courses = user_service.get_user_courses(g.current_user.user_id)
        # Note: You'll need to import and use course_schema here
        return jsonify({'courses': courses}), 200
    except Exception as e:
        current_app.logger.error(f"Error getting user courses: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@user_bp.route('/chats', methods=['GET'])
@login_required
def get_user_chats():
    """Get current user's chats"""
    try:
        chats = user_service.get_user_chats(g.current_user.user_id)
        # Note: You'll need to import and use chat_schema here
        return jsonify({'chats': chats}), 200
    except Exception as e:
        current_app.logger.error(f"Error getting user chats: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@user_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get user's notifications"""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        result = user_service.get_user_notifications(
            g.current_user.user_id,
            unread_only,
            page,
            per_page
        )
        # Note: You'll need to import and use notification_schema here
        return jsonify({
            'notifications': result['items'],
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting notifications: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@user_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@login_required
def deactivate_account(user_id):
    """Deactivate a user account (admin only)"""
    try:
        # Add admin check here
        if user_service.deactivate_user(user_id):
            return jsonify({'message': 'Account deactivated successfully'}), 200
        return jsonify({'message': 'User not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error deactivating account: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@user_bp.route('/<int:user_id>/reactivate', methods=['POST'])
@login_required
def reactivate_account(user_id):
    """Reactivate a user account (admin only)"""
    try:
        # Add admin check here
        if user_service.reactivate_user(user_id):
            return jsonify({'message': 'Account reactivated successfully'}), 200
        return jsonify({'message': 'User not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error reactivating account: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500
