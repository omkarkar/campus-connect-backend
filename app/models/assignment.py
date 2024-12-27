from datetime import datetime
from . import db

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    assignment_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    max_score = db.Column(db.Integer, nullable=False)
    total_points = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Boolean, default=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Assignment {self.title} for Course {self.course_id}>'
    
    @property
    def is_overdue(self):
        return datetime.utcnow() > self.due_date
    
    @property
    def time_remaining(self):
        if self.is_overdue:
            return "Overdue"
        delta = self.due_date - datetime.utcnow()
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{days}d {hours}h {minutes}m remaining"
    
    @property
    def completion_percentage(self):
        return (self.total_points / self.max_score) * 100 if self.max_score > 0 else 0
