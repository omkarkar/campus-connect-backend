from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Tuple
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from ..models import db

T = TypeVar('T')

class BaseService:
    """Base service class with common CRUD operations"""
    
    def __init__(self, model: Type[T]):
        self.model = model
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get a single record by ID"""
        try:
            return self.model.query.get(id)
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error retrieving {self.model.__name__}: {str(e)}")
            raise
    
    def get_all(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get all records with pagination"""
        try:
            pagination = self.model.query.paginate(
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
            current_app.logger.error(f"Error retrieving {self.model.__name__} list: {str(e)}")
            raise
    
    def create(self, data: Dict[str, Any]) -> T:
        """Create a new record"""
        try:
            instance = self.model(**data)
            db.session.add(instance)
            db.session.commit()
            return instance
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing record"""
        try:
            instance = self.get_by_id(id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                db.session.commit()
            return instance
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating {self.model.__name__}: {str(e)}")
            raise
    
    def delete(self, id: int) -> bool:
        """Delete a record"""
        try:
            instance = self.get_by_id(id)
            if instance:
                db.session.delete(instance)
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting {self.model.__name__}: {str(e)}")
            raise
    
    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """Create multiple records"""
        try:
            instances = [self.model(**item) for item in items]
            db.session.bulk_save_objects(instances)
            db.session.commit()
            return instances
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error bulk creating {self.model.__name__}: {str(e)}")
            raise
    
    def bulk_update(self, items: List[Dict[str, Any]]) -> List[T]:
        """Update multiple records"""
        try:
            instances = []
            for item in items:
                if 'id' not in item:
                    raise ValueError("Each item must have an 'id' field")
                instance = self.get_by_id(item['id'])
                if instance:
                    for key, value in item.items():
                        if key != 'id':
                            setattr(instance, key, value)
                    instances.append(instance)
            db.session.commit()
            return instances
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error bulk updating {self.model.__name__}: {str(e)}")
            raise
    
    def bulk_delete(self, ids: List[int]) -> bool:
        """Delete multiple records"""
        try:
            result = self.model.query.filter(self.model.id.in_(ids)).delete(synchronize_session=False)
            db.session.commit()
            return bool(result)
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error bulk deleting {self.model.__name__}: {str(e)}")
            raise
    
    def exists(self, **kwargs) -> bool:
        """Check if a record exists with given criteria"""
        try:
            return db.session.query(
                db.session.query(self.model).filter_by(**kwargs).exists()
            ).scalar()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error checking existence of {self.model.__name__}: {str(e)}")
            raise
    
    def count(self, **kwargs) -> int:
        """Count records with given criteria"""
        try:
            return self.model.query.filter_by(**kwargs).count()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error counting {self.model.__name__}: {str(e)}")
            raise
    
    def get_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[T, bool]:
        """Get an existing record or create a new one"""
        try:
            instance = self.model.query.filter_by(**kwargs).first()
            if instance:
                return instance, False
            
            params = dict(kwargs)
            if defaults:
                params.update(defaults)
            instance = self.create(params)
            return instance, True
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error in get_or_create for {self.model.__name__}: {str(e)}")
            raise
