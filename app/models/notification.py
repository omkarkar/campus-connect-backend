`from datetime import datetime
from . import db

class NotificationType:
    ASSIGNMENT = 'assignment'
    MESSAGE = 'message'
    COURSE = 'course'
    SYSTEM = 'system'
    GROUP = 'group'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.chat_id'))
    message_id = db.Column(db.Integer, db.ForeignKey('messages.message_id'))
    notification_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    data = db.Column(db.JSON)  # Additional data specific to notification type
    priority = db.Column(db.Integer, default=0)  # Higher number = higher priority
    seen = db.Column(db.Boolean, default=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    seen_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)  # Optional expiration time
    
    def __repr__(self):
        return f'<Notification {self.notification_id} for User {self.user_id}>'
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    @property
    def is_active(self):
        """Check if notification is active (not expired and not read)"""
        return not (self.is_expired or self.read)
    
    def mark_as_seen(self):
        """Mark notification as seen"""
        if not self.seen:
            self.seen = True
            self.seen_at = datetime.utcnow()
            return True
        return False
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.read:
            self.read = True
            self.read_at = datetime.utcnow()
            # Also mark as seen if not already
            if not self.seen:
                self.mark_as_seen()
            return True
        return False
    
    @classmethod
    def create_assignment_notification(cls, user_id, assignment_id, title, content=None):
        """Create a notification for an assignment"""
        return cls(
            user_id=user_id,
            notification_type=NotificationType.ASSIGNMENT,
            title=title,
            content=content,
            data={'assignment_id': assignment_id},
            priority=1
        )
    
    @classmethod
    def create_message_notification(cls, user_id, chat_id, message_id, sender_name):
        """Create a notification for a new message"""
        return cls(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            notification_type=NotificationType.MESSAGE,
            title=f'New message from {sender_name}',
            priority=1
        )
    
    @classmethod
    def create_system_notification(cls, user_id, title, content, priority=0):
        """Create a system notification"""
        return cls(
            user_id=user_id,
            notification_type=NotificationType.SYSTEM,
            title=title,
            content=content,
            priority=priority
        )
