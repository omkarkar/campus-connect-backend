from flask import Blueprint, request, jsonify, g, current_app
from marshmallow import ValidationError
from datetime import datetime

from ..services import media_service
from ..schemas.media import (
    media_schema,
    medias_schema,
    media_upload_schema
)
from .user_controller import login_required

media_bp = Blueprint('media', __name__)

@media_bp.route('/', methods=['POST'])
@login_required
def upload_media():
    """Upload new media"""
    try:
        data = media_upload_schema.load(request.get_json())
        media = media_service.create_media(
            user_id=g.current_user.user_id,
            file_name=data['file_name'],
            media_url=request.json.get('media_url'),  # From file upload service
            file_size=data['file_size'],
            mime_type=data['mime_type'],
            metadata=data.get('file_metadata')
        )
        return jsonify(media_schema.dump(media)), 201
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error uploading media: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@media_bp.route('/', methods=['GET'])
@login_required
def get_media():
    """Get media files with optional filters"""
    try:
        media_type = request.args.get('type')
        query = request.args.get('q')
        user_id = request.args.get('user_id', type=int)
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        if query:
            # Search media
            result = media_service.search_media(
                query,
                media_type,
                user_id,
                page,
                per_page
            )
        elif media_type:
            # Get media by type
            result = media_service.get_media_by_type(
                media_type,
                page,
                per_page
            )
        else:
            # Get user's media
            result = media_service.get_user_media(
                g.current_user.user_id,
                media_type,
                page,
                per_page
            )
        
        return jsonify({
            'media': medias_schema.dump(result['items']),
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting media: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@media_bp.route('/<int:media_id>', methods=['GET'])
@login_required
def get_media_by_id(media_id):
    """Get a specific media file"""
    try:
        media = media_service.get_by_id(media_id)
        if not media or media.is_deleted:
            return jsonify({'message': 'Media not found'}), 404
            
        # Update last accessed timestamp
        media_service.update_media_access(media_id)
        
        return jsonify(media_schema.dump(media)), 200
    except Exception as e:
        current_app.logger.error(f"Error getting media: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@media_bp.route('/<int:media_id>', methods=['DELETE'])
@login_required
def delete_media(media_id):
    """Delete a media file"""
    try:
        if media_service.soft_delete_media(media_id, g.current_user.user_id):
            return jsonify({'message': 'Media deleted successfully'}), 200
        return jsonify({'message': 'Media not found or unauthorized'}), 404
    except Exception as e:
        current_app.logger.error(f"Error deleting media: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@media_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get media usage statistics"""
    try:
        user_id = request.args.get('user_id', type=int)
        if user_id and user_id != g.current_user.user_id:
            # Only allow admins to view other users' stats
            # Add admin check here
            return jsonify({'message': 'Unauthorized'}), 403
            
        stats = media_service.get_media_stats(user_id)
        return jsonify(stats), 200
    except Exception as e:
        current_app.logger.error(f"Error getting media stats: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@media_bp.route('/types', methods=['GET'])
@login_required
def get_allowed_types():
    """Get allowed media types and their constraints"""
    try:
        return jsonify({
            'allowed_mime_types': media_service.allowed_mime_types,
            'max_file_sizes': media_service.max_file_sizes
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting allowed types: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500
