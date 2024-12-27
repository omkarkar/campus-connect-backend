from typing import Dict, List, Optional, Tuple
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from .base_service import BaseService
from ..models.user import User
from ..models import db

class UserService(BaseService):
    """Service class for user-related operations"""
    
    def __init__(self):
        super().__init__(User)
    
    def create_user(self, data: Dict) -> User:
        """Create a new user with password hashing"""
        try:
            # Hash password before storing
            if 'password' in data:
                data['password'] = generate_password_hash(data['password'])
            
            return self.create(data)
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error creating user: {str(e)}")
            raise
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password"""
        try:
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                user.last_seen = datetime.utcnow()
                db.session.commit()
                return user
            return None
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error authenticating user: {str(e)}")
            raise
    
    def search_users(self, query: str, page: int = 1, per_page: int = 10) -> Dict:
        """Search users by name or email"""
        try:
            search = f"%{query}%"
            pagination = User.query.filter(
                or_(
                    User.first_name.ilike(search),
                    User.last_name.ilike(search),
                    User.email.ilike(search)
                )
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
            current_app.logger.error(f"Error searching users: {str(e)}")
            raise
    
    def update_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Update user's password"""
        try:
            user = self.get_by_id(user_id)
            if user and check_password_hash(user.password, old_password):
                user.password = generate_password_hash(new_password)
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating password: {str(e)}")
            raise
    
    def update_last_seen(self, user_id: int) -> bool:
        """Update user's last seen timestamp"""
        try:
            user = self.get_by_id(user_id)
            if user:
                user.last_seen = datetime.utcnow()
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating last seen: {str(e)}")
            raise
    
    def get_user_courses(self, user_id: int) -> List:
        """Get courses where user is a professor"""
        try:
            user = self.get_by_id(user_id)
            return user.courses if user else []
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error getting user courses: {str(e)}")
            raise
    
    def get_user_chats(self, user_id: int) -> List:
        """Get all chats where user is a participant"""
        try:
            user = self.get_by_id(user_id)
            if not user:
                return []
            
            from ..models.chat import ChatParticipant
            return [
                p.chat for p in ChatParticipant.query.filter_by(
                    user_id=user_id,
                    left_at=None
                ).all()
            ]
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error getting user chats: {str(e)}")
            raise
    
    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        page: int = 1,
        per_page: int = 10
    ) -> Dict:
        """Get user's notifications"""
        try:
            query = User.query.get(user_id).notifications
            if unread_only:
                query = query.filter_by(read=False)
            
            pagination = query.order_by(
                User.notifications.created_at.desc()
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
            current_app.logger.error(f"Error getting user notifications: {str(e)}")
            raise
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account"""
        try:
            user = self.get_by_id(user_id)
            if user:
                user.status = 'inactive'
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error deactivating user: {str(e)}")
            raise
    
    def reactivate_user(self, user_id: int) -> bool:
        """Reactivate a user account"""
        try:
            user = self.get_by_id(user_id)
            if user:
                user.status = 'active'
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error reactivating user: {str(e)}")
            raise
