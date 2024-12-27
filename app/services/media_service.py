from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import mimetypes
from sqlalchemy import and_, or_
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from .base_service import BaseService
from ..models.media import Media
from ..models import db

class MediaService(BaseService):
    """Service class for media-related operations"""
    
    def __init__(self):
        super().__init__(Media)
        
        # Define allowed mime types per media type
        self.allowed_mime_types = {
            'image': [
                'image/jpeg', 'image/png', 'image/gif',
                'image/webp', 'image/svg+xml'
            ],
            'video': [
                'video/mp4', 'video/webm', 'video/ogg',
                'video/quicktime'
            ],
            'document': [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain'
            ],
            'audio': [
                'audio/mpeg', 'audio/ogg', 'audio/wav',
                'audio/webm'
            ]
        }
        
        # Maximum file sizes in bytes
        self.max_file_sizes = {
            'image': 10 * 1024 * 1024,  # 10MB
            'video': 100 * 1024 * 1024,  # 100MB
            'document': 20 * 1024 * 1024,  # 20MB
            'audio': 50 * 1024 * 1024  # 50MB
        }
    
    def create_media(
        self,
        user_id: int,
        file_name: str,
        media_url: str,
        file_size: int,
        mime_type: str,
        metadata: Optional[Dict] = None
    ) -> Media:
        """Create a new media record"""
        try:
            # Determine media type from mime type
            media_type = next(
                (k for k, v in self.allowed_mime_types.items() if mime_type in v),
                None
            )
            if not media_type:
                raise ValueError(f"Unsupported mime type: {mime_type}")
            
            # Validate file size
            max_size = self.max_file_sizes.get(media_type)
            if file_size > max_size:
                raise ValueError(
                    f"File size exceeds maximum allowed size for {media_type}"
                )
            
            # Generate file hash
            hash_input = f"{media_url}{file_size}{datetime.utcnow().timestamp()}"
            file_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            # Check for duplicate file
            existing_media = Media.query.filter_by(
                file_hash=file_hash,
                is_deleted=False
            ).first()
            if existing_media:
                return existing_media
            
            # Create media record
            media = self.create({
                'user_id': user_id,
                'media_type': media_type,
                'file_name': file_name,
                'original_name': file_name,
                'media_url': media_url,
                'mime_type': mime_type,
                'file_size': file_size,
                'file_hash': file_hash,
                'file_metadata': metadata or {}
            })
            
            return media
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating media: {str(e)}")
            raise
    
    def get_user_media(
        self,
        user_id: int,
        media_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Get media files uploaded by a user"""
        try:
            query = Media.query.filter_by(
                user_id=user_id,
                is_deleted=False
            )
            
            if media_type:
                query = query.filter_by(media_type=media_type)
            
            pagination = query.order_by(
                Media.uploaded_at.desc()
            ).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'items': pagination.items,
                'total': pagination.total,
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page
            }
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error getting user media: {str(e)}")
            raise
    
    def search_media(
        self,
        query: str,
        media_type: Optional[str] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Search media files"""
        try:
            search = f"%{query}%"
            filters = [
                Media.is_deleted == False,
                or_(
                    Media.file_name.ilike(search),
                    Media.original_name.ilike(search)
                )
            ]
            
            if media_type:
                filters.append(Media.media_type == media_type)
            if user_id:
                filters.append(Media.user_id == user_id)
            
            pagination = Media.query.filter(
                and_(*filters)
            ).order_by(
                Media.uploaded_at.desc()
            ).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'items': pagination.items,
                'total': pagination.total,
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page
            }
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error searching media: {str(e)}")
            raise
    
    def soft_delete_media(self, media_id: int, user_id: int) -> bool:
        """Soft delete a media file"""
        try:
            media = self.get_by_id(media_id)
            if media and media.user_id == user_id and not media.is_deleted:
                media.is_deleted = True
                media.deleted_at = datetime.utcnow()
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting media: {str(e)}")
            raise
    
    def update_media_access(self, media_id: int) -> bool:
        """Update last accessed timestamp"""
        try:
            media = self.get_by_id(media_id)
            if media and not media.is_deleted:
                media.last_accessed = datetime.utcnow()
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating media access: {str(e)}")
            raise
    
    def get_media_by_type(
        self,
        media_type: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Get media files by type"""
        try:
            pagination = Media.query.filter_by(
                media_type=media_type,
                is_deleted=False
            ).order_by(
                Media.uploaded_at.desc()
            ).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'items': pagination.items,
                'total': pagination.total,
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page
            }
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error getting media by type: {str(e)}")
            raise
    
    def get_media_stats(self, user_id: Optional[int] = None) -> Dict:
        """Get media usage statistics"""
        try:
            query = Media.query.filter_by(is_deleted=False)
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            stats = {}
            for media_type in self.allowed_mime_types.keys():
                type_query = query.filter_by(media_type=media_type)
                stats[media_type] = {
                    'count': type_query.count(),
                    'total_size': db.session.query(
                        db.func.sum(Media.file_size)
                    ).filter(
                        Media.media_type == media_type,
                        Media.is_deleted == False
                    ).scalar() or 0
                }
            
            return stats
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error getting media stats: {str(e)}")
            raise
