from datetime import datetime
from . import db

class ChatParticipant(db.Model):
    __tablename__ = 'chat_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.chat_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Ensure unique participants per chat
    __table_args__ = (
        db.UniqueConstraint('chat_id', 'user_id', name='unique_chat_participant'),
    )

class Chat(db.Model):
    __tablename__ = 'chats'
    
    chat_id = db.Column(db.Integer, primary_key=True)
    chat_type = db.Column(db.String(20), nullable=False)  # 'private', 'group', 'course'
    chat_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = db.Column(db.DateTime)
    
    # Relationships
    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan')
    participants = db.relationship('ChatParticipant', backref='chat', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='chat', lazy=True)
    group_events = db.relationship('GroupEvent', backref='chat', lazy=True)

    def __repr__(self):
        return f'<Chat {self.chat_name} ({self.chat_type})>'
    
    @property
    def participant_count(self):
        return len([p for p in self.participants if not p.left_at])
    
    @property
    def active_participants(self):
        return [p for p in self.participants if not p.left_at]
    
    @property
    def admins(self):
        return [p for p in self.participants if p.is_admin and not p.left_at]
    
    def add_participant(self, user_id, is_admin=False):
        participant = ChatParticipant(
            chat_id=self.chat_id,
            user_id=user_id,
            is_admin=is_admin
        )
        db.session.add(participant)
        return participant
    
    def remove_participant(self, user_id):
        participant = ChatParticipant.query.filter_by(
            chat_id=self.chat_id,
            user_id=user_id,
            left_at=None
        ).first()
        if participant:
            participant.left_at = datetime.utcnow()
            return True
        return False
