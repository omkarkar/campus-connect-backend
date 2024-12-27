from datetime import datetime
from . import db

class Message(db.Model):
    __tablename__ = 'messages'
    
    message_id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.chat_id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    message_type = db.Column(db.String(20), nullable=False)  # 'text', 'image', 'file', 'system'
    content = db.Column(db.Text)
    media_url = db.Column(db.String(255))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivered_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    edited_at = db.Column(db.DateTime)
    reply_to = db.Column(db.Integer, db.ForeignKey('messages.message_id'))
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Relationships
    notifications = db.relationship('Notification', backref='message', lazy=True)
    replies = db.relationship(
        'Message',
        backref=db.backref('replied_to', remote_side=[message_id]),
        lazy=True
    )
    read_by = db.relationship(
        'MessageReadStatus',
        backref='message',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Message {self.message_id} in Chat {self.chat_id}>'
    
    @property
    def is_edited(self):
        return self.edited_at is not None
    
    @property
    def read_count(self):
        return len(self.read_by)
    
    def mark_as_delivered(self):
        if not self.delivered_at:
            self.delivered_at = datetime.utcnow()
            return True
        return False
    
    def mark_as_read(self, user_id):
        if not any(status.user_id == user_id for status in self.read_by):
            read_status = MessageReadStatus(
                message_id=self.message_id,
                user_id=user_id,
                read_at=datetime.utcnow()
            )
            db.session.add(read_status)
            return True
        return False

class MessageReadStatus(db.Model):
    __tablename__ = 'message_read_status'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.message_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure each user can only mark a message as read once
    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id', name='unique_message_read_status'),
    )

    def __repr__(self):
        return f'<MessageReadStatus {self.message_id} by User {self.user_id}>'
