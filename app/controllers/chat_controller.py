from flask import Blueprint, request, jsonify, g, current_app
from marshmallow import ValidationError
from datetime import datetime

from ..services import chat_service
from ..schemas.chat import (
    chat_schema,
    chats_schema,
    chat_list_schema,
    chats_list_schema,
    chat_create_schema,
    chat_participant_schema
)
from .user_controller import login_required

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/', methods=['POST'])
@login_required
def create_chat():
    """Create a new chat"""
    try:
        data = chat_create_schema.load(request.get_json())
        chat = chat_service.create_chat(
            chat_type=data['chat_type'],
            chat_name=data['chat_name'],
            creator_id=g.current_user.user_id,
            participant_ids=data['participant_ids']
        )
        return jsonify(chat_schema.dump(chat)), 201
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating chat: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@chat_bp.route('/', methods=['GET'])
@login_required
def get_chats():
    """Get user's chats"""
    try:
        chat_type = request.args.get('type')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        result = chat_service.get_user_chats(
            g.current_user.user_id,
            chat_type,
            page,
            per_page
        )
        
        return jsonify({
            'chats': chats_list_schema.dump(result['items']),
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting chats: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@chat_bp.route('/<int:chat_id>', methods=['GET'])
@login_required
def get_chat(chat_id):
    """Get a specific chat"""
    try:
        chat = chat_service.get_by_id(chat_id)
        if not chat:
            return jsonify({'message': 'Chat not found'}), 404
            
        # Check if user is a participant
        if not any(p.user_id == g.current_user.user_id and not p.left_at 
                  for p in chat.participants):
            return jsonify({'message': 'Unauthorized'}), 403
            
        return jsonify(chat_schema.dump(chat)), 200
    except Exception as e:
        current_app.logger.error(f"Error getting chat: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@chat_bp.route('/<int:chat_id>/messages', methods=['GET'])
@login_required
def get_messages():
    """Get chat messages"""
    try:
        chat_id = request.args.get('chat_id', type=int)
        query = request.args.get('q')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Check if user is a participant
        chat = chat_service.get_by_id(chat_id)
        if not chat or not any(p.user_id == g.current_user.user_id and not p.left_at 
                             for p in chat.participants):
            return jsonify({'message': 'Unauthorized'}), 403
        
        if query:
            result = chat_service.search_chat_messages(
                chat_id, query, page, per_page
            )
        else:
            result = chat_service.get_chat_messages(
                chat_id, page, per_page
            )
        
        # Note: You'll need to import and use message_schema here
        return jsonify({
            'messages': result['items'],
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting chat messages: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@chat_bp.route('/<int:chat_id>/participants', methods=['POST'])
@login_required
def add_participants(chat_id):
    """Add participants to a chat"""
    try:
        chat = chat_service.get_by_id(chat_id)
        if not chat:
            return jsonify({'message': 'Chat not found'}), 404
            
        # Check if user is an admin
        if not any(p.user_id == g.current_user.user_id and p.is_admin and not p.left_at 
                  for p in chat.participants):
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return jsonify({'message': 'User IDs are required'}), 400
            
        if chat_service.add_participants(chat_id, user_ids, g.current_user.user_id):
            return jsonify({'message': 'Participants added successfully'}), 200
        return jsonify({'message': 'Failed to add participants'}), 400
    except Exception as e:
        current_app.logger.error(f"Error adding chat participants: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@chat_bp.route('/<int:chat_id>/participants/<int:user_id>', methods=['DELETE'])
@login_required
def remove_participant(chat_id, user_id):
    """Remove a participant from a chat"""
    try:
        chat = chat_service.get_by_id(chat_id)
        if not chat:
            return jsonify({'message': 'Chat not found'}), 404
            
        # Check if user is an admin or removing themselves
        is_admin = any(p.user_id == g.current_user.user_id and p.is_admin and not p.left_at 
                      for p in chat.participants)
        is_self = g.current_user.user_id == user_id
        
        if not (is_admin or is_self):
            return jsonify({'message': 'Unauthorized'}), 403
            
        if chat_service.remove_participant(chat_id, user_id, g.current_user.user_id):
            return jsonify({'message': 'Participant removed successfully'}), 200
        return jsonify({'message': 'Failed to remove participant'}), 400
    except Exception as e:
        current_app.logger.error(f"Error removing chat participant: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@chat_bp.route('/<int:chat_id>/settings', methods=['PUT'])
@login_required
def update_settings(chat_id):
    """Update chat settings"""
    try:
        chat = chat_service.get_by_id(chat_id)
        if not chat:
            return jsonify({'message': 'Chat not found'}), 404
            
        # Check if user is an admin
        if not any(p.user_id == g.current_user.user_id and p.is_admin and not p.left_at 
                  for p in chat.participants):
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        if chat_service.update_chat_settings(chat_id, data, g.current_user.user_id):
            return jsonify({'message': 'Chat settings updated successfully'}), 200
        return jsonify({'message': 'Failed to update chat settings'}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating chat settings: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500
