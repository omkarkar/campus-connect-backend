from typing import Dict, List, Optional, Set
from datetime import datetime
from sqlalchemy import and_, or_
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from .base_service import BaseService
from ..models.chat import Chat, ChatParticipant
from ..models.user import User
from ..models.message import Message
from ..models.notification import Notification, NotificationType
from ..models import db

class ChatService(BaseService):
    """Service class for chat-related operations"""
    
    def __init__(self):
        super().__init__(Chat)
    
    def create_chat(
        self,
        chat_type: str,
        chat_name: str,
        creator_id: int,
        participant_ids: List[int]
    ) -> Chat:
        """Create a new chat with participants"""
        try:
            # Validate chat type
            if chat_type not in ['private', 'group', 'course']:
                raise ValueError("Invalid chat type")
            
            # For private chats, ensure exactly 2 participants
            if chat_type == 'private' and len(participant_ids) != 2:
                raise ValueError("Private chats must have exactly 2 participants")
            
            # Ensure creator is in participant list
            if creator_id not in participant_ids:
                participant_ids.append(creator_id)
            
            # Create chat
            chat = self.create({
                'chat_type': chat_type,
                'chat_name': chat_name
            })
            
            # Add participants
            for user_id in participant_ids:
                participant = ChatParticipant(
                    chat_id=chat.chat_id,
                    user_id=user_id,
                    is_admin=user_id == creator_id
                )
                db.session.add(participant)
            
            db.session.commit()
            return chat
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating chat: {str(e)}")
            raise
    
    def add_participants(
        self,
        chat_id: int,
        user_ids: List[int],
        added_by_id: int
    ) -> bool:
        """Add multiple participants to a chat"""
        try:
            chat = self.get_by_id(chat_id)
            if not chat or chat.chat_type == 'private':
                return False
            
            # Get existing participant IDs
            existing_ids = {p.user_id for p in chat.participants if not p.left_at}
            new_ids = set(user_ids) - existing_ids
            
            # Add new participants
            for user_id in new_ids:
                participant = ChatParticipant(
                    chat_id=chat_id,
                    user_id=user_id
                )
                db.session.add(participant)
                
                # Create notification for new participant
                notification = Notification(
                    user_id=user_id,
                    notification_type=NotificationType.GROUP,
                    title=f"Added to chat: {chat.chat_name}",
                    content=f"You were added by {User.query.get(added_by_id).full_name}",
                    data={'chat_id': chat_id}
                )
                db.session.add(notification)
            
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding chat participants: {str(e)}")
            raise
    
    def remove_participant(
        self,
        chat_id: int,
        user_id: int,
        removed_by_id: int
    ) -> bool:
        """Remove a participant from a chat"""
        try:
            participant = ChatParticipant.query.filter_by(
                chat_id=chat_id,
                user_id=user_id,
                left_at=None
            ).first()
            
            if participant:
                participant.left_at = datetime.utcnow()
                
                # Create notification for removed user
                notification = Notification(
                    user_id=user_id,
                    notification_type=NotificationType.GROUP,
                    title=f"Removed from chat",
                    content=f"You were removed by {User.query.get(removed_by_id).full_name}",
                    data={'chat_id': chat_id}
                )
                db.session.add(notification)
                
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error removing chat participant: {str(e)}")
            raise
    
    def get_chat_messages(
        self,
        chat_id: int,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Get messages for a chat with pagination"""
        try:
            pagination = Message.query.filter_by(
                chat_id=chat_id,
                is_deleted=False
            ).order_by(
                Message.sent_at.desc()
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
            current_app.logger.error(f"Error getting chat messages: {str(e)}")
            raise
    
    def get_user_chats(
        self,
        user_id: int,
        chat_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict:
        """Get all chats for a user"""
        try:
            query = Chat.query.join(
                ChatParticipant
            ).filter(
                ChatParticipant.user_id == user_id,
                ChatParticipant.left_at.is_(None)
            )
            
            if chat_type:
                query = query.filter(Chat.chat_type == chat_type)
            
            pagination = query.order_by(
                Chat.last_message_at.desc().nullslast()
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
            current_app.logger.error(f"Error getting user chats: {str(e)}")
            raise
    
    def search_chat_messages(
        self,
        chat_id: int,
        query: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Search messages in a chat"""
        try:
            search = f"%{query}%"
            pagination = Message.query.filter(
                and_(
                    Message.chat_id == chat_id,
                    Message.content.ilike(search),
                    Message.is_deleted == False
                )
            ).order_by(
                Message.sent_at.desc()
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
            current_app.logger.error(f"Error searching chat messages: {str(e)}")
            raise
    
    def update_chat_settings(
        self,
        chat_id: int,
        settings: Dict,
        updated_by_id: int
    ) -> bool:
        """Update chat settings"""
        try:
            chat = self.get_by_id(chat_id)
            if chat and chat.chat_type != 'private':
                # Update allowed settings
                if 'chat_name' in settings:
                    chat.chat_name = settings['chat_name']
                
                # Create notification for all participants
                for participant in chat.active_participants:
                    if participant.user_id != updated_by_id:
                        notification = Notification(
                            user_id=participant.user_id,
                            notification_type=NotificationType.GROUP,
                            title=f"Chat settings updated",
                            content=f"Settings updated by {User.query.get(updated_by_id).full_name}",
                            data={'chat_id': chat_id}
                        )
                        db.session.add(notification)
                
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating chat settings: {str(e)}")
            raise
