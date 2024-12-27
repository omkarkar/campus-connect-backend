from datetime import datetime
from . import db

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    status = db.Column(db.String(255))
    last_seen = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    courses = db.relationship('Course', backref='professor', lazy=True)
    messages = db.relationship('Message', backref='sender', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    group_events = db.relationship('GroupEvent', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
