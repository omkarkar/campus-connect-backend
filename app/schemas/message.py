from marshmallow import fields, validates, ValidationError, validates_schema, pre_load
from . import ma, BaseSchema
from ..models.message import Message, MessageReadStatus
from datetime import datetime

class MessageReadStatusSchema(BaseSchema):
    """Schema for MessageReadStatus model"""
    
    class Meta:
        model = MessageReadStatus
        load_instance = True
        include_fk = True
        dump_only = ('id', 'read_at')
    
    # Nested relationships
    user = fields.Nested(
        'UserProfileSchema',
        only=('user_id', 'full_name'),
        dump_only=True
    )

class MessageSchema(BaseSchema):
    """Schema for Message model"""
    
    class Meta:
        model = Message
        load_instance = True
        include_fk = True
        dump_only = (
            'message_id', 'sent_at', 'delivered_at',
            'read_at', 'edited_at', 'is_deleted'
        )
    
    # Nested relationships
    sender = fields.Nested(
        'UserProfileSchema',
        only=('user_id', 'full_name', 'last_seen'),
        dump_only=True
    )
    chat = fields.Nested(
        'ChatSchema',
        only=('chat_id', 'chat_type', 'chat_name'),
        dump_only=True
    )
    replied_to = fields.Nested(
        'MessageSchema',
        only=('message_id', 'content', 'sender'),
        dump_only=True
    )
    read_by = fields.Nested(
        MessageReadStatusSchema,
        many=True,
        dump_only=True
    )
    
    # Custom fields
    is_edited = fields.Method("get_is_edited", dump_only=True)
    read_count = fields.Method("get_read_count", dump_only=True)
    
    def get_is_edited(self, obj):
        """Check if message has been edited"""
        return obj.is_edited
    
    def get_read_count(self, obj):
        """Get number of users who have read the message"""
        return obj.read_count
    
    @validates('message_type')
    def validate_message_type(self, value):
        """Validate message type"""
        valid_types = ['text', 'image', 'file', 'system']
        if value not in valid_types:
            raise ValidationError(f'Invalid message type. Must be one of: {", ".join(valid_types)}')
    
    @validates('content')
    def validate_content(self, value):
        """Validate message content"""
        if not value or not value.strip():
            raise ValidationError('Message content cannot be empty')
        if len(value) > 5000:  # Arbitrary maximum
            raise ValidationError('Message content cannot exceed 5000 characters')
    
    @validates_schema
    def validate_message(self, data, **kwargs):
        """Validate message data"""
        # Validate media URL for media messages
        if data.get('message_type') in ['image', 'file']:
            if not data.get('media_url'):
                raise ValidationError('Media URL is required for image/file messages')
        
        # Validate reply_to message exists
        if data.get('reply_to'):
            if not Message.query.get(data['reply_to']):
                raise ValidationError('Reply-to message does not exist')

# Initialize schema instances
message_read_status_schema = MessageReadStatusSchema()
message_read_statuses_schema = MessageReadStatusSchema(many=True)

message_schema = MessageSchema()
messages_schema = MessageSchema(many=True)

# Schema for message listing (with fewer fields)
class MessageListSchema(MessageSchema):
    class Meta(MessageSchema.Meta):
        fields = (
            'message_id', 'message_type', 'content', 'media_url',
            'sent_at', 'is_edited', 'sender', 'read_count',
            'replied_to'
        )

message_list_schema = MessageListSchema()
messages_list_schema = MessageListSchema(many=True)

# Schema for sending a new message
class MessageCreateSchema(ma.Schema):
    chat_id = fields.Integer(required=True)
    message_type = fields.String(required=True)
    content = fields.String()
    media_url = fields.String()
    reply_to = fields.Integer()
    
    @validates_schema
    def validate_message_creation(self, data, **kwargs):
        """Validate message creation data"""
        if data['message_type'] in ['image', 'file'] and not data.get('media_url'):
            raise ValidationError('Media URL is required for image/file messages')
        
        if data['message_type'] == 'text' and not data.get('content'):
            raise ValidationError('Content is required for text messages')
        
        if data.get('reply_to'):
            if not Message.query.get(data['reply_to']):
                raise ValidationError('Reply-to message does not exist')

message_create_schema = MessageCreateSchema()

# Schema for editing a message
class MessageEditSchema(ma.Schema):
    content = fields.String(required=True)
    
    @validates('content')
    def validate_content(self, value):
        """Validate edited content"""
        if not value or not value.strip():
            raise ValidationError('Message content cannot be empty')
        if len(value) > 5000:
            raise ValidationError('Message content cannot exceed 5000 characters')

message_edit_schema = MessageEditSchema()
