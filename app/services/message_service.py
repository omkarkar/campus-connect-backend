from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import and_, or_
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from .base_service import BaseService
from ..models.message import Message, MessageReadStatus
from ..models.chat import Chat, ChatParticipant
from ..models.notification import Notification, NotificationType
from ..models import db

class MessageService(BaseService):
    """Service class for message-related operations"""
    
    def __init__(self):
        super().__init__(Message)
    
    def send_message(
        self,
        chat_id: int,
        sender_id: int,
        message_type: str,
        content: Optional[str] = None,
        media_url: Optional[str] = None,
        reply_to: Optional[int] = None
    ) -> Message:
        """Send a new message in a chat"""
        try:
            # Validate chat exists and sender is a participant
            chat = Chat.query.join(
                ChatParticipant
            ).filter(
                Chat.chat_id == chat_id,
                ChatParticipant.user_id == sender_id,
                ChatParticipant.left_at.is_(None)
            ).first()
            
            if not chat:
                raise ValueError("Invalid chat or sender")
            
            # Create message
            message = self.create({
                'chat_id': chat_id,
                'sender_id': sender_id,
                'message_type': message_type,
                'content': content,
                'media_url': media_url,
                'reply_to': reply_to
            })
            
            # Update chat's last message timestamp
            chat.last_message_at = datetime.utcnow()
            
            # Create notifications for other participants
            for participant in chat.active_participants:
                if participant.user_id != sender_id:
                    notification = Notification(
                        user_id=participant.user_id,
                        notification_type=NotificationType.MESSAGE,
                        title=f"New message in {chat.chat_name}",
                        content=content[:100] if content else "New message",
                        data={
                            'chat_id': chat_id,
                            'message_id': message.message_id
                        }
                    )
                    db.session.add(notification)
            
            db.session.commit()
            return message
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error sending message: {str(e)}")
            raise
    
    def edit_message(
        self,
        message_id: int,
        user_id: int,
        new_content: str
    ) -> Optional[Message]:
        """Edit an existing message"""
        try:
            message = self.get_by_id(message_id)
            if message and message.sender_id == user_id and not message.is_deleted:
                message.content = new_content
                message.edited_at = datetime.utcnow()
                db.session.commit()
                return message
            return None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error editing message: {str(e)}")
            raise
    
    def delete_message(self, message_id: int, user_id: int) -> bool:
        """Soft delete a message"""
        try:
            message = self.get_by_id(message_id)
            if message and message.sender_id == user_id:
                message.is_deleted = True
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting message: {str(e)}")
            raise
    
    def mark_as_delivered(
        self,
        message_ids: List[int],
        user_id: int
    ) -> int:
        """Mark multiple messages as delivered"""
        try:
            count = Message.query.filter(
                Message.message_id.in_(message_ids),
                Message.sender_id != user_id,
                Message.delivered_at.is_(None)
            ).update({
                'delivered_at': datetime.utcnow()
            }, synchronize_session=False)
            
            db.session.commit()
            return count
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error marking messages as delivered: {str(e)}")
            raise
    
    def mark_as_read(
        self,
        message_ids: List[int],
        user_id: int
    ) -> int:
        """Mark multiple messages as read"""
        try:
            # Get messages that haven't been read by this user
            messages = Message.query.filter(
                Message.message_id.in_(message_ids),
                Message.sender_id != user_id,
                ~Message.read_by.any(
                    MessageReadStatus.user_id == user_id
                )
            ).all()
            
            # Create read status for each message
            for message in messages:
                read_status = MessageReadStatus(
                    message_id=message.message_id,
                    user_id=user_id
                )
                db.session.add(read_status)
            
            db.session.commit()
            return len(messages)
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error marking messages as read: {str(e)}")
            raise
    
    def get_unread_count(self, user_id: int, chat_id: Optional[int] = None) -> int:
        """Get count of unread messages"""
        try:
            query = Message.query.filter(
                Message.sender_id != user_id,
                ~Message.read_by.any(
                    MessageReadStatus.user_id == user_id
                )
            )
            
            if chat_id:
                query = query.filter(Message.chat_id == chat_id)
            else:
                # Only count messages from chats where user is still a participant
                query = query.join(
                    Chat
                ).join(
                    ChatParticipant
                ).filter(
                    ChatParticipant.user_id == user_id,
                    ChatParticipant.left_at.is_(None)
                )
            
            return query.count()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error getting unread count: {str(e)}")
            raise
    
    def get_message_readers(
        self,
        message_id: int,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Get users who have read a message"""
        try:
            pagination = MessageReadStatus.query.filter_by(
                message_id=message_id
            ).order_by(
                MessageReadStatus.read_at.asc()
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
            current_app.logger.error(f"Error getting message readers: {str(e)}")
            raise
