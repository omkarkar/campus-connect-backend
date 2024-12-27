from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import and_, or_
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from .base_service import BaseService
from ..models.group_event import GroupEvent, EventType
from ..models.chat import Chat, ChatParticipant
from ..models.notification import Notification, NotificationType
from ..models.user import User
from ..models import db

class GroupEventService(BaseService):
    """Service class for group event-related operations"""
    
    def __init__(self):
        super().__init__(GroupEvent)
    
    def create_event(
        self,
        chat_id: int,
        user_id: int,
        event_type: str,
        target_user_id: Optional[int] = None,
        event_data: Optional[Dict] = None
    ) -> GroupEvent:
        """Create a new group event"""
        try:
            # Validate event type
            if event_type not in EventType.__dict__.values():
                raise ValueError("Invalid event type")
            
            # Validate chat exists and user is a participant
            chat = Chat.query.join(
                ChatParticipant
            ).filter(
                Chat.chat_id == chat_id,
                ChatParticipant.user_id == user_id,
                ChatParticipant.left_at.is_(None)
            ).first()
            
            if not chat:
                raise ValueError("Invalid chat or user")
            
            # For events requiring target user, validate target exists
            if event_type in [
                EventType.ADD,
                EventType.REMOVE,
                EventType.PROMOTE,
                EventType.DEMOTE
            ]:
                if not target_user_id:
                    raise ValueError("Target user required for this event type")
                
                target_user = User.query.get(target_user_id)
                if not target_user:
                    raise ValueError("Target user does not exist")
            
            # Create event
            event = self.create({
                'chat_id': chat_id,
                'user_id': user_id,
                'target_user_id': target_user_id,
                'event_type': event_type,
                'event_data': event_data or {}
            })
            
            # Create notifications for relevant users
            self._create_event_notifications(event, chat)
            
            db.session.commit()
            return event
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating group event: {str(e)}")
            raise
    
    def _create_event_notifications(self, event: GroupEvent, chat: Chat) -> None:
        """Create notifications for a group event"""
        notification_data = {
            'chat_id': chat.chat_id,
            'event_id': event.event_id
        }
        
        # Get notification title and content based on event type
        title, content = self._get_event_notification_content(event)
        
        # Create notifications for all active participants except the event performer
        for participant in chat.active_participants:
            if participant.user_id != event.user_id:
                notification = Notification(
                    user_id=participant.user_id,
                    notification_type=NotificationType.GROUP,
                    title=title,
                    content=content,
                    data=notification_data
                )
                db.session.add(notification)
    
    def _get_event_notification_content(self, event: GroupEvent) -> tuple[str, str]:
        """Get notification title and content for an event"""
        performer = User.query.get(event.user_id)
        performer_name = performer.full_name
        
        if event.event_type == EventType.JOIN:
            return (
                "New member joined",
                f"{performer_name} joined the group"
            )
        elif event.event_type == EventType.LEAVE:
            return (
                "Member left",
                f"{performer_name} left the group"
            )
        elif event.event_type in [EventType.ADD, EventType.REMOVE, EventType.PROMOTE, EventType.DEMOTE]:
            target = User.query.get(event.target_user_id)
            target_name = target.full_name
            
            if event.event_type == EventType.ADD:
                return (
                    "New member added",
                    f"{performer_name} added {target_name} to the group"
                )
            elif event.event_type == EventType.REMOVE:
                return (
                    "Member removed",
                    f"{performer_name} removed {target_name} from the group"
                )
            elif event.event_type == EventType.PROMOTE:
                return (
                    "Admin promoted",
                    f"{performer_name} promoted {target_name} to admin"
                )
            else:  # DEMOTE
                return (
                    "Admin demoted",
                    f"{performer_name} removed admin privileges from {target_name}"
                )
        elif event.event_type == EventType.NAME_CHANGE:
            old_name = event.event_data.get('old_name', '')
            new_name = event.event_data.get('new_name', '')
            return (
                "Group name changed",
                f"{performer_name} changed group name from '{old_name}' to '{new_name}'"
            )
        else:
            return (
                "Group updated",
                f"{performer_name} updated the group"
            )
    
    def get_chat_events(
        self,
        chat_id: int,
        event_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Get events for a chat"""
        try:
            query = GroupEvent.query.filter_by(chat_id=chat_id)
            
            if event_type:
                query = query.filter_by(event_type=event_type)
            
            pagination = query.order_by(
                GroupEvent.event_time.desc()
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
            current_app.logger.error(f"Error getting chat events: {str(e)}")
            raise
    
    def get_user_events(
        self,
        user_id: int,
        as_target: bool = False,
        event_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Get events performed by or targeting a user"""
        try:
            if as_target:
                query = GroupEvent.query.filter_by(target_user_id=user_id)
            else:
                query = GroupEvent.query.filter_by(user_id=user_id)
            
            if event_type:
                query = query.filter_by(event_type=event_type)
            
            pagination = query.order_by(
                GroupEvent.event_time.desc()
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
            current_app.logger.error(f"Error getting user events: {str(e)}")
            raise
    
    def get_event_stats(self, chat_id: Optional[int] = None) -> Dict:
        """Get event statistics"""
        try:
            stats = {}
            query = GroupEvent.query
            
            if chat_id:
                query = query.filter_by(chat_id=chat_id)
            
            for event_type in EventType.__dict__.values():
                if not event_type.startswith('_'):
                    type_query = query.filter_by(event_type=event_type)
                    stats[event_type] = {
                        'total': type_query.count(),
                        'last_24h': type_query.filter(
                            GroupEvent.event_time > datetime.utcnow() - timedelta(days=1)
                        ).count()
                    }
            
            return stats
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error getting event stats: {str(e)}")
            raise
