from datetime import datetime
from . import db

class Course(db.Model):
    __tablename__ = 'courses'
    
    course_id = db.Column(db.Integer, primary_key=True)
    professor_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    date_and_year = db.Column(db.DateTime, nullable=False)
    course_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('Assignment', backref='course', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Course {self.course_name} - {self.semester}>'
    
    @property
    def assignment_count(self):
        return len(self.assignments)
    
    @property
    def active_assignments(self):
        return [a for a in self.assignments if a.due_date > datetime.utcnow()]
