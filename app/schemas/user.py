from marshmallow import fields, validates, ValidationError, validates_schema
from . import ma, BaseSchema
from ..models.user import User
import re

class UserSchema(BaseSchema):
    """Schema for User model"""
    
    class Meta:
        model = User
        load_instance = True
        include_fk = True
        dump_only = ('user_id', 'created_at', 'last_seen')
        
    # Custom fields
    full_name = fields.Method("get_full_name", dump_only=True)
    password = fields.String(load_only=True, required=True)
    confirm_password = fields.String(load_only=True, required=True)
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return f"{obj.first_name} {obj.last_name}"
    
    @validates('email')
    def validate_email(self, value):
        """Validate email format"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise ValidationError('Invalid email format')
        
        # Check if email already exists
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already registered')
    
    @validates('phone_number')
    def validate_phone(self, value):
        """Validate phone number format"""
        phone_regex = r'^\+?1?\d{9,15}$'
        if not re.match(phone_regex, value):
            raise ValidationError('Invalid phone number format')
        
        # Check if phone number already exists
        if User.query.filter_by(phone_number=value).first():
            raise ValidationError('Phone number already registered')
    
    @validates('first_name')
    def validate_first_name(self, value):
        """Validate first name"""
        if len(value.strip()) < 2:
            raise ValidationError('First name must be at least 2 characters long')
        if not value.strip().isalpha():
            raise ValidationError('First name must contain only letters')
    
    @validates('last_name')
    def validate_last_name(self, value):
        """Validate last name"""
        if len(value.strip()) < 2:
            raise ValidationError('Last name must be at least 2 characters long')
        if not value.strip().isalpha():
            raise ValidationError('Last name must contain only letters')
    
    @validates_schema
    def validate_passwords(self, data, **kwargs):
        """Validate password and confirm_password match"""
        if data.get('password') != data.get('confirm_password'):
            raise ValidationError('Passwords must match')
        
        password = data.get('password', '')
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in password):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in password):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in password):
            raise ValidationError('Password must contain at least one number')
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
            raise ValidationError('Password must contain at least one special character')

# Initialize schema instances
user_schema = UserSchema()
users_schema = UserSchema(many=True)

# Schema for user profile (excludes sensitive information)
class UserProfileSchema(UserSchema):
    class Meta(UserSchema.Meta):
        exclude = ('password', 'confirm_password')

user_profile_schema = UserProfileSchema()
users_profile_schema = UserProfileSchema(many=True)

# Schema for user login
class UserLoginSchema(ma.Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)

user_login_schema = UserLoginSchema()
