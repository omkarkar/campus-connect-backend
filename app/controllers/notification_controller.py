l0-from flask import Blueprint, request, jsonify, g, current_app
from marshmallow import ValidationError
from datetime import datetime

from ..services import notification_service
from ..schemas.notification import (
    notification_schema,
    notifications_schema,
    notification_list_schema,
    notifications_list_schema,
    notification_create_schema
)
from .user_controller import login_required

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/', methods=['POST'])
@login_required
def create_notification():
    """Create a new notification"""
    try:
        data = notification_create_schema.load(request.get_json())
        notification = notification_service.create_notification(
            user_id=data['user_id'],
            notification_type=data['notification_type'],
            title=data['title'],
            content=data.get('content'),
            data=data.get('data'),
            priority=data.get('priority', 0),
            expires_at=data.get('expires_at')
        )
        return jsonify(notification_schema.dump(notification)), 201
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating notification: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@notification_bp.route('/bulk', methods=['POST'])
@login_required
def create_bulk_notifications():
    """Create notifications for multiple users"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return jsonify({'message': 'User IDs are required'}), 400
            
        notifications = notification_service.create_bulk_notifications(
            user_ids=user_ids,
            notification_type=data['notification_type'],
            title=data['title'],
            content=data.get('content'),
            data=data.get('data'),
            priority=data.get('priority', 0),
            expires_at=data.get('expires_at')
        )
        
        return jsonify({
            'message': f'Created {len(notifications)} notifications',
            'notifications': notifications_schema.dump(notifications)
        }), 201
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating bulk notifications: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@notification_bp.route('/', methods=['GET'])
@login_required
def get_notifications():
    """Get user's notifications"""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        notification_type = request.args.get('type')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        result = notification_service.get_user_notifications(
            g.current_user.user_id,
            unread_only,
            notification_type,
            page,
            per_page
        )
        
        return jsonify({
            'notifications': notifications_list_schema.dump(result['items']),
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting notifications: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@notification_bp.route('/seen', methods=['POST'])
@login_required
def mark_seen():
    """Mark notifications as seen"""
    try:
        data = request.get_json()
        notification_ids = data.get('notification_ids', [])
        
        if not notification_ids:
            return jsonify({'message': 'Notification IDs are required'}), 400
            
        count = notification_service.mark_as_seen(
            notification_ids,
            g.current_user.user_id
        )
        
        return jsonify({
            'message': f'Marked {count} notifications as seen',
            'count': count
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error marking notifications as seen: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@notification_bp.route('/read', methods=['POST'])
@login_required
def mark_read():
    """Mark notifications as read"""
    try:
        data = request.get_json()
        notification_ids = data.get('notification_ids', [])
        
        if not notification_ids:
            return jsonify({'message': 'Notification IDs are required'}), 400
            
        count = notification_service.mark_as_read(
            notification_ids,
            g.current_user.user_id
        )
        
        return jsonify({
            'message': f'Marked {count} notifications as read',
            'count': count
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error marking notifications as read: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@notification_bp.route('/unread/count', methods=['GET'])
@login_required
def get_unread_count():
    """Get count of unread notifications"""
    try:
        notification_type = request.args.get('type')
        count = notification_service.get_unread_count(
            g.current_user.user_id,
            notification_type
        )
        return jsonify({'count': count}), 200
    except Exception as e:
        current_app.logger.error(f"Error getting unread count: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@notification_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get notification statistics"""
    try:
        stats = notification_service.get_notification_stats(g.current_user.user_id)
        return jsonify(stats), 200
    except Exception as e:
        current_app.logger.error(f"Error getting notification stats: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@notification_bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_expired():
    """Delete expired notifications (admin only)"""
    try:
        # Add admin check here
        count = notification_service.delete_expired_notifications()
        return jsonify({
            'message': f'Deleted {count} expired notifications',
            'count': count
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error cleaning up notifications: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500
