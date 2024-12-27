from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from .base_service import BaseService
from ..models.notification import Notification, NotificationType
from ..models.user import User
from ..models import db

class NotificationService(BaseService):
    """Service class for notification-related operations"""
    
    def __init__(self):
        super().__init__(Notification)
    
    def create_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        content: Optional[str] = None,
        data: Optional[Dict] = None,
        priority: int = 0,
        expires_at: Optional[datetime] = None
    ) -> Notification:
        """Create a new notification"""
        try:
            # Validate notification type
            if notification_type not in NotificationType.__dict__.values():
                raise ValueError("Invalid notification type")
            
            # Validate priority range
            if not 0 <= priority <= 10:
                raise ValueError("Priority must be between 0 and 10")
            
            # Set default expiration if not provided
            if not expires_at:
                expires_at = datetime.utcnow() + timedelta(days=30)
            
            notification = self.create({
                'user_id': user_id,
                'notification_type': notification_type,
                'title': title,
                'content': content,
                'data': data or {},
                'priority': priority,
                'expires_at': expires_at
            })
            
            return notification
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating notification: {str(e)}")
            raise
    
    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Get notifications for a user"""
        try:
            query = Notification.query.filter(
                and_(
                    Notification.user_id == user_id,
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at > datetime.utcnow()
                    )
                )
            )
            
            if unread_only:
                query = query.filter_by(read=False)
            
            if notification_type:
                query = query.filter_by(notification_type=notification_type)
            
            pagination = query.order_by(
                Notification.priority.desc(),
                Notification.created_at.desc()
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
            current_app.logger.error(f"Error getting user notifications: {str(e)}")
            raise
    
    def mark_as_seen(self, notification_ids: List[int], user_id: int) -> int:
        """Mark multiple notifications as seen"""
        try:
            count = Notification.query.filter(
                Notification.notification_id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.seen == False
            ).update({
                'seen': True,
                'seen_at': datetime.utcnow()
            }, synchronize_session=False)
            
            db.session.commit()
            return count
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error marking notifications as seen: {str(e)}")
            raise
    
    def mark_as_read(self, notification_ids: List[int], user_id: int) -> int:
        """Mark multiple notifications as read"""
        try:
            count = Notification.query.filter(
                Notification.notification_id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.read == False
            ).update({
                'read': True,
                'read_at': datetime.utcnow(),
                'seen': True,
                'seen_at': datetime.utcnow()
            }, synchronize_session=False)
            
            db.session.commit()
            return count
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error marking notifications as read: {str(e)}")
            raise
    
    def get_unread_count(
        self,
        user_id: int,
        notification_type: Optional[str] = None
    ) -> int:
        """Get count of unread notifications"""
        try:
            query = Notification.query.filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.read == False,
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at > datetime.utcnow()
                    )
                )
            )
            
            if notification_type:
                query = query.filter_by(notification_type=notification_type)
            
            return query.count()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error getting unread count: {str(e)}")
            raise
    
    def delete_expired_notifications(self) -> int:
        """Delete expired notifications"""
        try:
            count = Notification.query.filter(
                Notification.expires_at <= datetime.utcnow()
            ).delete(synchronize_session=False)
            
            db.session.commit()
            return count
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting expired notifications: {str(e)}")
            raise
    
    def create_bulk_notifications(
        self,
        user_ids: List[int],
        notification_type: str,
        title: str,
        content: Optional[str] = None,
        data: Optional[Dict] = None,
        priority: int = 0,
        expires_at: Optional[datetime] = None
    ) -> List[Notification]:
        """Create notifications for multiple users"""
        try:
            notifications = []
            for user_id in user_ids:
                notification = Notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    content=content,
                    data=data or {},
                    priority=priority,
                    expires_at=expires_at
                )
                notifications.append(notification)
            
            db.session.bulk_save_objects(notifications)
            db.session.commit()
            
            return notifications
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating bulk notifications: {str(e)}")
            raise
    
    def get_notification_stats(self, user_id: int) -> Dict:
        """Get notification statistics for a user"""
        try:
            stats = {}
            for notification_type in NotificationType.__dict__.values():
                if not notification_type.startswith('_'):
                    type_query = Notification.query.filter_by(
                        user_id=user_id,
                        notification_type=notification_type
                    )
                    stats[notification_type] = {
                        'total': type_query.count(),
                        'unread': type_query.filter_by(read=False).count(),
                        'unseen': type_query.filter_by(seen=False).count()
                    }
            
            return stats
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error getting notification stats: {str(e)}")
            raise
