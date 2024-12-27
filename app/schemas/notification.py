from marshmallow import fields, validates, ValidationError, validates_schema
from . import ma, BaseSchema
from ..models.notification import Notification, NotificationType
from datetime import datetime, timedelta

class NotificationSchema(BaseSchema):
    """Schema for Notification model"""
    
    class Meta:
        model = Notification
        load_instance = True
        include_fk = True
        dump_only = (
            'notification_id', 'created_at', 'updated_at',
            'seen_at', 'read_at'
        )
    
    # Nested relationships
    user = fields.Nested(
        'UserProfileSchema',
        only=('user_id', 'full_name'),
        dump_only=True
    )
    chat = fields.Nested(
        'ChatSchema',
        only=('chat_id', 'chat_type', 'chat_name'),
        dump_only=True
    )
    message = fields.Nested(
        'MessageSchema',
        only=('message_id', 'content', 'sender'),
        dump_only=True
    )
    
    # Custom fields
    is_expired = fields.Method("get_is_expired", dump_only=True)
    is_active = fields.Method("get_is_active", dump_only=True)
    
    def get_is_expired(self, obj):
        """Check if notification has expired"""
        return obj.is_expired
    
    def get_is_active(self, obj):
        """Check if notification is active"""
        return obj.is_active
    
    @validates('notification_type')
    def validate_notification_type(self, value):
        """Validate notification type"""
        valid_types = [
            NotificationType.ASSIGNMENT,
            NotificationType.MESSAGE,
            NotificationType.COURSE,
            NotificationType.SYSTEM,
            NotificationType.GROUP
        ]
        if value not in valid_types:
            raise ValidationError(f'Invalid notification type. Must be one of: {", ".join(valid_types)}')
    
    @validates('title')
    def validate_title(self, value):
        """Validate notification title"""
        if len(value.strip()) < 3:
            raise ValidationError('Title must be at least 3 characters long')
        if len(value) > 255:
            raise ValidationError('Title must not exceed 255 characters')
    
    @validates('priority')
    def validate_priority(self, value):
        """Validate notification priority"""
        if not isinstance(value, int) or value < 0 or value > 10:
            raise ValidationError('Priority must be an integer between 0 and 10')
    
    @validates_schema
    def validate_notification(self, data, **kwargs):
        """Validate notification data"""
        # Validate expiration date
        if 'expires_at' in data and data['expires_at']:
            if data['expires_at'] < datetime.utcnow():
                raise ValidationError('Expiration date cannot be in the past')
            
            # Maximum expiration time is 30 days
            max_expiry = datetime.utcnow() + timedelta(days=30)
            if data['expires_at'] > max_expiry:
                raise ValidationError('Expiration date cannot be more than 30 days in the future')
        
        # Validate data field based on notification type
        if 'notification_type' in data and 'data' in data:
            if data['notification_type'] == NotificationType.ASSIGNMENT:
                required_fields = ['assignment_id']
            elif data['notification_type'] == NotificationType.MESSAGE:
                required_fields = ['chat_id', 'message_id']
            elif data['notification_type'] == NotificationType.COURSE:
                required_fields = ['course_id']
            else:
                required_fields = []
            
            if data['data']:
                for field in required_fields:
                    if field not in data['data']:
                        raise ValidationError(f'Data must include {field} for {data["notification_type"]} notifications')

# Initialize schema instances
notification_schema = NotificationSchema()
notifications_schema = NotificationSchema(many=True)

# Schema for notification listing (with fewer fields)
class NotificationListSchema(NotificationSchema):
    class Meta(NotificationSchema.Meta):
        fields = (
            'notification_id', 'notification_type', 'title',
            'content', 'priority', 'seen', 'read',
            'created_at', 'is_expired', 'is_active'
        )

notification_list_schema = NotificationListSchema()
notifications_list_schema = NotificationListSchema(many=True)

# Schema for creating a notification
class NotificationCreateSchema(ma.Schema):
    user_id = fields.Integer(required=True)
    notification_type = fields.String(required=True)
    title = fields.String(required=True)
    content = fields.String()
    data = fields.Dict()
    priority = fields.Integer(missing=0)
    expires_at = fields.DateTime()
    
    @validates_schema
    def validate_notification_creation(self, data, **kwargs):
        """Validate notification creation data"""
        # Validate user exists (assuming User model is available)
        from ..models.user import User
        if not User.query.get(data['user_id']):
            raise ValidationError('User does not exist')
        
        # Validate notification type
        if data['notification_type'] not in [
            NotificationType.ASSIGNMENT,
            NotificationType.MESSAGE,
            NotificationType.COURSE,
            NotificationType.SYSTEM,
            NotificationType.GROUP
        ]:
            raise ValidationError('Invalid notification type')

notification_create_schema = NotificationCreateSchema()
