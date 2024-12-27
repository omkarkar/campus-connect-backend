from marshmallow import fields, validates, ValidationError, validates_schema
from . import ma, BaseSchema
from ..models.chat import Chat, ChatParticipant

class ChatParticipantSchema(BaseSchema):
    """Schema for ChatParticipant model"""
    
    class Meta:
        model = ChatParticipant
        load_instance = True
        include_fk = True
        dump_only = ('id', 'joined_at', 'left_at')
    
    # Nested relationships
    user = fields.Nested(
        'UserProfileSchema',
        only=('user_id', 'full_name', 'email', 'last_seen'),
        dump_only=True
    )
    
    @validates_schema
    def validate_participant(self, data, **kwargs):
        """Validate participant data"""
        if 'left_at' in data and data['left_at']:
            if data['left_at'] < data.get('joined_at', data['left_at']):
                raise ValidationError('Left time cannot be before join time')

class ChatSchema(BaseSchema):
    """Schema for Chat model"""
    
    class Meta:
        model = Chat
        load_instance = True
        include_fk = True
        dump_only = ('chat_id', 'created_at', 'updated_at', 'last_message_at')
    
    # Nested relationships
    participants = fields.Nested(
        ChatParticipantSchema,
        many=True,
        dump_only=True
    )
    messages = fields.Nested(
        'MessageSchema',
        many=True,
        only=('message_id', 'content', 'sent_at', 'sender'),
        dump_only=True
    )
    
    # Custom fields
    participant_count = fields.Method("get_participant_count", dump_only=True)
    active_participants = fields.Method("get_active_participants", dump_only=True)
    admins = fields.Method("get_admins", dump_only=True)
    last_message = fields.Method("get_last_message", dump_only=True)
    
    def get_participant_count(self, obj):
        """Get number of active participants"""
        return obj.participant_count
    
    def get_active_participants(self, obj):
        """Get list of active participants"""
        return [
            {
                'user_id': p.user_id,
                'full_name': p.user.full_name,
                'is_admin': p.is_admin
            }
            for p in obj.active_participants
        ]
    
    def get_admins(self, obj):
        """Get list of admin participants"""
        return [
            {
                'user_id': p.user_id,
                'full_name': p.user.full_name
            }
            for p in obj.admins
        ]
    
    def get_last_message(self, obj):
        """Get the last message in the chat"""
        if obj.messages:
            last_msg = max(obj.messages, key=lambda m: m.sent_at)
            return {
                'content': last_msg.content,
                'sent_at': last_msg.sent_at,
                'sender': last_msg.sender.full_name
            }
        return None
    
    @validates('chat_type')
    def validate_chat_type(self, value):
        """Validate chat type"""
        valid_types = ['private', 'group', 'course']
        if value not in valid_types:
            raise ValidationError(f'Invalid chat type. Must be one of: {", ".join(valid_types)}')
    
    @validates('chat_name')
    def validate_chat_name(self, value):
        """Validate chat name"""
        if len(value.strip()) < 3:
            raise ValidationError('Chat name must be at least 3 characters long')
        if len(value) > 255:
            raise ValidationError('Chat name must not exceed 255 characters')

# Initialize schema instances
chat_participant_schema = ChatParticipantSchema()
chat_participants_schema = ChatParticipantSchema(many=True)

chat_schema = ChatSchema()
chats_schema = ChatSchema(many=True)

# Schema for chat listing (with fewer fields)
class ChatListSchema(ChatSchema):
    class Meta(ChatSchema.Meta):
        fields = (
            'chat_id', 'chat_type', 'chat_name', 'participant_count',
            'last_message', 'last_message_at', 'updated_at'
        )

chat_list_schema = ChatListSchema()
chats_list_schema = ChatListSchema(many=True)

# Schema for creating a new chat
class ChatCreateSchema(ma.Schema):
    chat_type = fields.String(required=True)
    chat_name = fields.String(required=True)
    participant_ids = fields.List(fields.Integer(), required=True)
    is_course_chat = fields.Boolean(default=False)
    course_id = fields.Integer()  # Required if is_course_chat is True
    
    @validates_schema
    def validate_chat_creation(self, data, **kwargs):
        """Validate chat creation data"""
        if data['chat_type'] == 'private' and len(data['participant_ids']) != 2:
            raise ValidationError('Private chat must have exactly 2 participants')
        
        if data['chat_type'] == 'group' and len(data['participant_ids']) < 2:
            raise ValidationError('Group chat must have at least 2 participants')
        
        if data.get('is_course_chat') and not data.get('course_id'):
            raise ValidationError('Course ID is required for course chat')

chat_create_schema = ChatCreateSchema()
