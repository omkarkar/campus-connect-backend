from flask import Blueprint, request, jsonify, g, current_app
from marshmallow import ValidationError
from datetime import datetime

from ..services import message_service
from ..schemas.message import (
    message_schema,
    messages_schema,
    message_list_schema,
    messages_list_schema,
    message_create_schema,
    message_edit_schema,
    message_read_status_schema,
    message_read_statuses_schema
)
from .user_controller import login_required

message_bp = Blueprint('message', __name__)

@message_bp.route('/', methods=['POST'])
@login_required
def send_message():
    """Send a new message"""
    try:
        data = message_create_schema.load(request.get_json())
        message = message_service.send_message(
            chat_id=data['chat_id'],
            sender_id=g.current_user.user_id,
            message_type=data['message_type'],
            content=data.get('content'),
            media_url=data.get('media_url'),
            reply_to=data.get('reply_to')
        )
        return jsonify(message_schema.dump(message)), 201
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error sending message: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@message_bp.route('/<int:message_id>', methods=['PUT'])
@login_required
def edit_message(message_id):
    """Edit a message"""
    try:
        data = message_edit_schema.load(request.get_json())
        message = message_service.edit_message(
            message_id,
            g.current_user.user_id,
            data['content']
        )
        
        if message:
            return jsonify(message_schema.dump(message)), 200
        return jsonify({'message': 'Message not found or unauthorized'}), 404
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"Error editing message: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@message_bp.route('/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    """Delete a message"""
    try:
        if message_service.delete_message(message_id, g.current_user.user_id):
            return jsonify({'message': 'Message deleted successfully'}), 200
        return jsonify({'message': 'Message not found or unauthorized'}), 404
    except Exception as e:
        current_app.logger.error(f"Error deleting message: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@message_bp.route('/delivered', methods=['POST'])
@login_required
def mark_delivered():
    """Mark messages as delivered"""
    try:
        data = request.get_json()
        message_ids = data.get('message_ids', [])
        
        if not message_ids:
            return jsonify({'message': 'Message IDs are required'}), 400
            
        count = message_service.mark_as_delivered(
            message_ids,
            g.current_user.user_id
        )
        
        return jsonify({
            'message': f'Marked {count} messages as delivered',
            'count': count
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error marking messages as delivered: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@message_bp.route('/read', methods=['POST'])
@login_required
def mark_read():
    """Mark messages as read"""
    try:
        data = request.get_json()
        message_ids = data.get('message_ids', [])
        
        if not message_ids:
            return jsonify({'message': 'Message IDs are required'}), 400
            
        count = message_service.mark_as_read(
            message_ids,
            g.current_user.user_id
        )
        
        return jsonify({
            'message': f'Marked {count} messages as read',
            'count': count
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error marking messages as read: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@message_bp.route('/unread/count', methods=['GET'])
@login_required
def get_unread_count():
    """Get count of unread messages"""
    try:
        chat_id = request.args.get('chat_id', type=int)
        count = message_service.get_unread_count(g.current_user.user_id, chat_id)
        return jsonify({'count': count}), 200
    except Exception as e:
        current_app.logger.error(f"Error getting unread count: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@message_bp.route('/<int:message_id>/readers', methods=['GET'])
@login_required
def get_readers(message_id):
    """Get users who have read a message"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        result = message_service.get_message_readers(
            message_id,
            page,
            per_page
        )
        
        return jsonify({
            'readers': message_read_statuses_schema.dump(result['items']),
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting message readers: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500
