from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Tuple
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from flask import current_app
from ..models import db
from .. import cache
import hashlib
import json

T = TypeVar('T')

class BaseService:
    """Base service class with common CRUD operations"""
    
    def __init__(self, model: Type[T]):
        self.model = model
        self.cache_prefix = model.__name__.lower()
        self.default_cache_timeout = 300  # 5 minutes default cache timeout
    
    def _get_cache_key(self, key_parts: Union[str, List[Any]]) -> str:
        """Generate a cache key from parts"""
        if isinstance(key_parts, str):
            key_parts = [key_parts]
        key_str = f"{self.cache_prefix}:" + ":".join(str(p) for p in key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _invalidate_cache(self, key_parts: Union[str, List[Any]]) -> None:
        """Invalidate a cache entry"""
        cache.delete(self._get_cache_key(key_parts))

    def get_by_id(self, id: int, relations: Optional[List[str]] = None) -> Optional[T]:
        """Get a single record by ID with optional eager loading"""
        cache_key = self._get_cache_key(['by_id', id, str(relations)])
        
        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
            
        try:
            query = self.model.query
            
            # Add eager loading if relations specified
            if relations:
                for relation in relations:
                    query = query.options(joinedload(relation))
            
            result = query.get(id)
            if result:
                # Cache the result
                cache.set(cache_key, result, timeout=self.default_cache_timeout)
            return result
        except SQLAlchemyError as e:
            current_app.logger.error(f"Error retrieving {self.model.__name__}: {str(e)}")
            raise
    
    def get_all(self, page: int = 1, per_page: int = 10, relations: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get all records with pagination and optional eager loading"""
        cache_key = self._get_cache_key(['all', page, per_page, str(relations)])
        
        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
            
        try:
            query = self.model.query
            
            # Add eager loading if relations specified
            if relations:
                for relation in relations:
                    query = query.options(joinedload(relation))
            
            # Add ordering by ID for consistent pagination
            query = query.order_by(self.model.id)
            
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            result = {
                'items': pagination.items,
                'total': pagination.total,
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page
            }
            
            # Cache the result
            cache.set(cache_key, result, timeout=self.default_cache_timeout)
            return result
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
            
            # Invalidate relevant caches
            self._invalidate_cache('all')
            
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
    
    def bulk_create(self, items: List[Dict[str, Any]], chunk_size: int = 1000) -> List[T]:
        """Create multiple records with chunking for better performance"""
        try:
            instances = []
            # Process in chunks to avoid memory issues
            for i in range(0, len(items), chunk_size):
                chunk = items[i:i + chunk_size]
                chunk_instances = [self.model(**item) for item in chunk]
                db.session.bulk_save_objects(chunk_instances)
                instances.extend(chunk_instances)
                
            db.session.commit()
            
            # Invalidate relevant caches
            self._invalidate_cache('all')
            
            return instances
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error bulk creating {self.model.__name__}: {str(e)}")
            raise
    
    def bulk_update(self, items: List[Dict[str, Any]], chunk_size: int = 1000) -> List[T]:
        """Update multiple records with chunking"""
        try:
            instances = []
            # Process in chunks
            for i in range(0, len(items), chunk_size):
                chunk = items[i:i + chunk_size]
                chunk_instances = []
                
                # Get all IDs for this chunk
                ids = [item['id'] for item in chunk if 'id' in item]
                existing_instances = {
                    instance.id: instance 
                    for instance in self.model.query.filter(self.model.id.in_(ids))
                }
                
                for item in chunk:
                    if 'id' not in item:
                        raise ValueError("Each item must have an 'id' field")
                    instance = existing_instances.get(item['id'])
                    if instance:
                        for key, value in item.items():
                            if key != 'id':
                                setattr(instance, key, value)
                        chunk_instances.append(instance)
                
                instances.extend(chunk_instances)
                db.session.commit()
                
                # Invalidate caches for updated records
                for item in chunk:
                    self._invalidate_cache(['by_id', item['id']])
            
            # Invalidate general caches
            self._invalidate_cache('all')
            
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
        """Check if a record exists with given criteria (with caching)"""
        cache_key = self._get_cache_key(['exists', json.dumps(kwargs, sort_keys=True)])
        
        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
            
        try:
            result = db.session.query(
                db.session.query(self.model).filter_by(**kwargs).exists()
            ).scalar()
            
            # Cache the result
            cache.set(cache_key, result, timeout=self.default_cache_timeout)
            return result
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
