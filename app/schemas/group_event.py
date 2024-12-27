from marshmallow import fields, validates, ValidationError, validates_schema
from . import ma, BaseSchema
from ..models.group_event import GroupEvent, EventType
from datetime import datetime

class GroupEventSchema(BaseSchema):
    """Schema for GroupEvent model"""
    
    class Meta:
        model = GroupEvent
        load_instance = True
        include_fk = True
        dump_only = ('event_id', 'event_time')
    
    # Nested relationships
    performer = fields.Nested(
        'UserProfileSchema',
        only=('user_id', 'full_name'),
        dump_only=True
    )
    target = fields.Nested(
        'UserProfileSchema',
        only=('user_id', 'full_name'),
        dump_only=True
    )
    chat = fields.Nested(
        'ChatSchema',
        only=('chat_id', 'chat_type', 'chat_name'),
        dump_only=True
    )
    
    # Custom fields
    is_member_event = fields.Method("get_is_member_event", dump_only=True)
    is_role_event = fields.Method("get_is_role_event", dump_only=True)
    is_settings_event = fields.Method("get_is_settings_event", dump_only=True)
    
    def get_is_member_event(self, obj):
        """Check if event is related to member management"""
        return obj.is_member_event
    
    def get_is_role_event(self, obj):
        """Check if event is related to role changes"""
        return obj.is_role_event
    
    def get_is_settings_event(self, obj):
        """Check if event is related to group settings"""
        return obj.is_settings_event
    
    @validates('event_type')
    def validate_event_type(self, value):
        """Validate event type"""
        valid_types = [
            EventType.JOIN,
            EventType.LEAVE,
            EventType.ADD,
            EventType.REMOVE,
            EventType.PROMOTE,
            EventType.DEMOTE,
            EventType.NAME_CHANGE,
            EventType.DESCRIPTION_CHANGE,
            EventType.SETTINGS_CHANGE
        ]
        if value not in valid_types:
            raise ValidationError(f'Invalid event type. Must be one of: {", ".join(valid_types)}')
    
    @validates_schema
    def validate_event(self, data, **kwargs):
        """Validate event data"""
        # Validate target user for relevant event types
        if data.get('event_type') in [
            EventType.ADD,
            EventType.REMOVE,
            EventType.PROMOTE,
            EventType.DEMOTE
        ]:
            if not data.get('target_user_id'):
                raise ValidationError('Target user is required for this event type')
        
        # Validate event data format
        if data.get('event_data'):
            if not isinstance(data['event_data'], dict):
                raise ValidationError('Event data must be a JSON object')
            
            # Validate specific event data based on event type
            if data.get('event_type') == EventType.NAME_CHANGE:
                required_fields = ['old_name', 'new_name']
                for field in required_fields:
                    if field not in data['event_data']:
                        raise ValidationError(f'Event data must include {field} for name change events')
            
            elif data.get('event_type') == EventType.SETTINGS_CHANGE:
                if 'changes' not in data['event_data']:
                    raise ValidationError('Event data must include changes for settings change events')

# Initialize schema instances
group_event_schema = GroupEventSchema()
group_events_schema = GroupEventSchema(many=True)

# Schema for event listing (with fewer fields)
class GroupEventListSchema(GroupEventSchema):
    class Meta(GroupEventSchema.Meta):
        fields = (
            'event_id', 'event_type', 'performer', 'target',
            'event_time', 'event_data'
        )

group_event_list_schema = GroupEventListSchema()
group_events_list_schema = GroupEventListSchema(many=True)

# Schema for creating a group event
class GroupEventCreateSchema(ma.Schema):
    chat_id = fields.Integer(required=True)
    user_id = fields.Integer(required=True)
    target_user_id = fields.Integer()
    event_type = fields.String(required=True)
    event_data = fields.Dict()
    
    @validates_schema
    def validate_event_creation(self, data, **kwargs):
        """Validate event creation data"""
        # Validate chat exists
        from ..models.chat import Chat
        if not Chat.query.get(data['chat_id']):
            raise ValidationError('Chat does not exist')
        
        # Validate user exists
        from ..models.user import User
        if not User.query.get(data['user_id']):
            raise ValidationError('User does not exist')
        
        # Validate target user if provided
        if data.get('target_user_id'):
            if not User.query.get(data['target_user_id']):
                raise ValidationError('Target user does not exist')
            
            # User cannot target themselves
            if data['user_id'] == data['target_user_id']:
                raise ValidationError('User cannot target themselves')
        
        # Validate event type
        if data['event_type'] not in [
            EventType.JOIN,
            EventType.LEAVE,
            EventType.ADD,
            EventType.REMOVE,
            EventType.PROMOTE,
            EventType.DEMOTE,
            EventType.NAME_CHANGE,
            EventType.DESCRIPTION_CHANGE,
            EventType.SETTINGS_CHANGE
        ]:
            raise ValidationError('Invalid event type')

group_event_create_schema = GroupEventCreateSchema()
