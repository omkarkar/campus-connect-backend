from flask_marshmallow import Marshmallow
from marshmallow import validates_schema, ValidationError
from datetime import datetime

ma = Marshmallow()

class BaseSchema(ma.SQLAlchemyAutoSchema):
    """Base schema with common functionality"""
    
    class Meta:
        load_instance = True
        include_fk = True
        include_relationships = True
    
    @validates_schema
    def validate_dates(self, data, **kwargs):
        """Validate date fields are not in the past for relevant fields"""
        date_fields = ['due_date', 'event_time']
        for field in date_fields:
            if field in data and data[field] < datetime.utcnow():
                raise ValidationError(f"{field} cannot be in the past")

    def handle_error(self, error, data, **kwargs):
        """Custom error handler for schema validation errors"""
        message = []
        for field_name, field_errors in error.messages.items():
            for err in field_errors:
                message.append(f"{field_name}: {err}")
        return {"error": "Validation failed", "messages": message}
