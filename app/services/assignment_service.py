from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from .base_service import BaseService
from ..models.assignment import Assignment
from ..models.course import Course
from ..models.notification import Notification, NotificationType
from ..models import db

class AssignmentService(BaseService):
    """Service class for assignment-related operations"""
    
    def __init__(self):
        super().__init__(Assignment)
    
    def create_assignment(self, data: Dict) -> Assignment:
        """Create a new assignment and notify relevant users"""
        try:
            # Validate course exists
            course = Course.query.get(data['course_id'])
            if not course:
                raise ValueError("Course does not exist")
            
            # Convert string date to datetime if needed
            if isinstance(data.get('due_date'), str):
                data['due_date'] = datetime.strptime(
                    data['due_date'],
                    '%Y-%m-%d %H:%M:%S'
                )
            
            assignment = self.create(data)
            
            # Create notification for the assignment
            notification = Notification(
                user_id=course.professor_id,
                notification_type=NotificationType.ASSIGNMENT,
                title=f"New Assignment: {assignment.title}",
                content=f"Due date: {assignment.due_date.strftime('%Y-%m-%d %H:%M')}",
                data={'assignment_id': assignment.assignment_id}
            )
            db.session.add(notification)
            db.session.commit()
            
            return assignment
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating assignment: {str(e)}")
            raise
    
    def get_upcoming_assignments(
        self,
        course_id: Optional[int] = None,
        days: int = 7,
        page: int = 1,
        per_page: int = 10
    ) -> Dict:
        """Get upcoming assignments within specified days"""
        try:
            now = datetime.utcnow()
            end_date = now + timedelta(days=days)
            
            query = Assignment.query.filter(
                and_(
                    Assignment.due_date > now,
                    Assignment.due_date <= end_date
                )
            )
            
            if course_id:
                query = query.filter_by(course_id=course_id)
            
            pagination = query.order_by(
                Assignment.due_date.asc()
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
            current_app.logger.error(f"Error getting upcoming assignments: {str(e)}")
            raise
    
    def get_overdue_assignments(
        self,
        course_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict:
        """Get overdue assignments"""
        try:
            query = Assignment.query.filter(
                Assignment.due_date < datetime.utcnow()
            )
            
            if course_id:
                query = query.filter_by(course_id=course_id)
            
            pagination = query.order_by(
                Assignment.due_date.desc()
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
            current_app.logger.error(f"Error getting overdue assignments: {str(e)}")
            raise
    
    def update_assignment_status(self, assignment_id: int, status: bool) -> bool:
        """Update assignment status"""
        try:
            assignment = self.get_by_id(assignment_id)
            if assignment:
                assignment.status = status
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating assignment status: {str(e)}")
            raise
    
    def extend_due_date(
        self,
        assignment_id: int,
        new_due_date: datetime
    ) -> Optional[Assignment]:
        """Extend assignment due date"""
        try:
            assignment = self.get_by_id(assignment_id)
            if assignment and new_due_date > datetime.utcnow():
                old_due_date = assignment.due_date
                assignment.due_date = new_due_date
                db.session.commit()
                
                # Create notification for due date extension
                notification = Notification(
                    user_id=assignment.course.professor_id,
                    notification_type=NotificationType.ASSIGNMENT,
                    title=f"Due Date Extended: {assignment.title}",
                    content=(
                        f"Due date changed from {old_due_date.strftime('%Y-%m-%d %H:%M')} "
                        f"to {new_due_date.strftime('%Y-%m-%d %H:%M')}"
                    ),
                    data={'assignment_id': assignment_id}
                )
                db.session.add(notification)
                db.session.commit()
                
                return assignment
            return None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error extending assignment due date: {str(e)}")
            raise
    
    def search_assignments(
        self,
        query: str,
        course_id: Optional[int] = None,
        include_past: bool = False,
        page: int = 1,
        per_page: int = 10
    ) -> Dict:
        """Search assignments by title or description"""
        try:
            search = f"%{query}%"
            filters = [
                or_(
                    Assignment.title.ilike(search),
                    Assignment.description.ilike(search)
                )
            ]
            
            if course_id:
                filters.append(Assignment.course_id == course_id)
            
            if not include_past:
                filters.append(Assignment.due_date > datetime.utcnow())
            
            pagination = Assignment.query.filter(
                and_(*filters)
            ).order_by(
                Assignment.due_date.asc()
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
            current_app.logger.error(f"Error searching assignments: {str(e)}")
            raise
    
    def get_assignment_statistics(self, assignment_id: int) -> Dict:
        """Get statistics for an assignment"""
        try:
            assignment = self.get_by_id(assignment_id)
            if not assignment:
                raise ValueError("Assignment does not exist")
            
            return {
                'title': assignment.title,
                'total_points': assignment.total_points,
                'max_score': assignment.max_score,
                'completion_percentage': assignment.completion_percentage,
                'is_overdue': assignment.is_overdue,
                'time_remaining': assignment.time_remaining,
                'course': {
                    'id': assignment.course.course_id,
                    'name': assignment.course.course_name
                }
            }
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error getting assignment statistics: {str(e)}")
            raise
