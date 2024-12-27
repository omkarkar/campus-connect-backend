from datetime import datetime
from . import db

class EventType:
    JOIN = 'join'
    LEAVE = 'leave'
    ADD = 'add'
    REMOVE = 'remove'
    PROMOTE = 'promote'
    DEMOTE = 'demote'
    NAME_CHANGE = 'name_change'
    DESCRIPTION_CHANGE = 'description_change'
    SETTINGS_CHANGE = 'settings_change'

class GroupEvent(db.Model):
    __tablename__ = 'group_events'
    
    event_id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.chat_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # User who performed the action
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))  # User who was affected (optional)
    event_type = db.Column(db.String(50), nullable=False)
    event_data = db.Column(db.JSON)  # Additional event-specific data
    event_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    performer = db.relationship('User', foreign_keys=[user_id], backref='performed_events')
    target = db.relationship('User', foreign_keys=[target_user_id], backref='targeted_events')
    
    def __repr__(self):
        return f'<GroupEvent {self.event_type} in Chat {self.chat_id}>'
    
    @property
    def is_member_event(self):
        """Check if event is related to member management"""
        return self.event_type in [
            EventType.JOIN,
            EventType.LEAVE,
            EventType.ADD,
            EventType.REMOVE
        ]
    
    @property
    def is_role_event(self):
        """Check if event is related to role changes"""
        return self.event_type in [EventType.PROMOTE, EventType.DEMOTE]
    
    @property
    def is_settings_event(self):
        """Check if event is related to group settings"""
        return self.event_type in [
            EventType.NAME_CHANGE,
            EventType.DESCRIPTION_CHANGE,
            EventType.SETTINGS_CHANGE
        ]
    
    @classmethod
    def create_join_event(cls, chat_id, user_id):
        """Create an event for a user joining the group"""
        return cls(
            chat_id=chat_id,
            user_id=user_id,
            event_type=EventType.JOIN
        )
    
    @classmethod
    def create_leave_event(cls, chat_id, user_id):
        """Create an event for a user leaving the group"""
        return cls(
            chat_id=chat_id,
            user_id=user_id,
            event_type=EventType.LEAVE
        )
    
    @classmethod
    def create_add_event(cls, chat_id, admin_id, added_user_id):
        """Create an event for a user being added to the group"""
        return cls(
            chat_id=chat_id,
            user_id=admin_id,
            target_user_id=added_user_id,
            event_type=EventType.ADD
        )
    
    @classmethod
    def create_remove_event(cls, chat_id, admin_id, removed_user_id):
        """Create an event for a user being removed from the group"""
        return cls(
            chat_id=chat_id,
            user_id=admin_id,
            target_user_id=removed_user_id,
            event_type=EventType.REMOVE
        )
    
    @classmethod
    def create_promote_event(cls, chat_id, admin_id, promoted_user_id):
        """Create an event for a user being promoted to admin"""
        return cls(
            chat_id=chat_id,
            user_id=admin_id,
            target_user_id=promoted_user_id,
            event_type=EventType.PROMOTE
        )
    
    @classmethod
    def create_name_change_event(cls, chat_id, user_id, old_name, new_name):
        """Create an event for group name change"""
        return cls(
            chat_id=chat_id,
            user_id=user_id,
            event_type=EventType.NAME_CHANGE,
            event_data={
                'old_name': old_name,
                'new_name': new_name
            }
        )
