from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import and_, or_
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from .base_service import BaseService
from ..models.course import Course
from ..models.user import User
from ..models.assignment import Assignment
from ..models import db

class CourseService(BaseService):
    """Service class for course-related operations"""
    
    def __init__(self):
        super().__init__(Course)
    
    def create_course(self, data: Dict) -> Course:
        """Create a new course"""
        try:
            # Validate professor exists
            professor = User.query.get(data['professor_id'])
            if not professor:
                raise ValueError("Professor does not exist")
            
            # Convert string date to datetime if needed
            if isinstance(data.get('date_and_year'), str):
                data['date_and_year'] = datetime.strptime(
                    data['date_and_year'],
                    '%Y-%m-%d %H:%M:%S'
                )
            
            return self.create(data)
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error creating course: {str(e)}")
            raise
    
    def get_course_with_assignments(self, course_id: int) -> Optional[Course]:
        """Get course with its assignments"""
        try:
            return Course.query.options(
                db.joinedload(Course.assignments)
            ).get(course_id)
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error getting course with assignments: {str(e)}")
            raise
    
    def get_courses_by_professor(
        self,
        professor_id: int,
        semester: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict:
        """Get courses taught by a professor"""
        try:
            query = Course.query.filter_by(professor_id=professor_id)
            if semester:
                query = query.filter_by(semester=semester)
            
            pagination = query.order_by(
                Course.date_and_year.desc()
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
            current_app.logger.error(f"Error getting professor courses: {str(e)}")
            raise
    
    def search_courses(
        self,
        query: str,
        semester: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict:
        """Search courses by name or professor"""
        try:
            search = f"%{query}%"
            filters = [Course.course_name.ilike(search)]
            
            if semester:
                filters.append(Course.semester == semester)
            
            # Join with User to search by professor name
            courses = Course.query.join(
                User, Course.professor_id == User.user_id
            ).filter(
                and_(
                    or_(
                        Course.course_name.ilike(search),
                        User.first_name.ilike(search),
                        User.last_name.ilike(search)
                    ),
                    *filters
                )
            )
            
            pagination = courses.paginate(
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
            current_app.logger.error(f"Error searching courses: {str(e)}")
            raise
    
    def get_course_assignments(
        self,
        course_id: int,
        include_past: bool = False,
        page: int = 1,
        per_page: int = 10
    ) -> Dict:
        """Get assignments for a course"""
        try:
            query = Assignment.query.filter_by(course_id=course_id)
            if not include_past:
                query = query.filter(Assignment.due_date > datetime.utcnow())
            
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
            current_app.logger.error(f"Error getting course assignments: {str(e)}")
            raise
    
    def get_courses_by_semester(
        self,
        semester: str,
        page: int = 1,
        per_page: int = 10
    ) -> Dict:
        """Get all courses for a specific semester"""
        try:
            pagination = Course.query.filter_by(
                semester=semester
            ).order_by(
                Course.course_name.asc()
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
            current_app.logger.error(f"Error getting semester courses: {str(e)}")
            raise
    
    def get_active_courses(
        self,
        page: int = 1,
        per_page: int = 10
    ) -> Dict:
        """Get all currently active courses"""
        try:
            current_date = datetime.utcnow()
            pagination = Course.query.filter(
                Course.date_and_year <= current_date
            ).order_by(
                Course.date_and_year.desc()
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
            current_app.logger.error(f"Error getting active courses: {str(e)}")
            raise
    
    def update_course_professor(self, course_id: int, new_professor_id: int) -> bool:
        """Update the professor for a course"""
        try:
            course = self.get_by_id(course_id)
            new_professor = User.query.get(new_professor_id)
            
            if course and new_professor:
                course.professor_id = new_professor_id
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating course professor: {str(e)}")
            raise
