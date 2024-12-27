from marshmallow import fields, validates, ValidationError, validates_schema
from . import ma, BaseSchema
from ..models.media import Media
import re

class MediaSchema(BaseSchema):
    """Schema for Media model"""
    
    class Meta:
        model = Media
        load_instance = True
        include_fk = True
        dump_only = (
            'media_id', 'uploaded_at', 'last_accessed',
            'is_deleted', 'deleted_at'
        )
    
    # Nested relationships
    user = fields.Nested(
        'UserProfileSchema',
        only=('user_id', 'full_name'),
        dump_only=True
    )
    
    # Custom fields
    size_in_mb = fields.Method("get_size_in_mb", dump_only=True)
    is_image = fields.Method("get_is_image", dump_only=True)
    is_video = fields.Method("get_is_video", dump_only=True)
    is_document = fields.Method("get_is_document", dump_only=True)
    is_audio = fields.Method("get_is_audio", dump_only=True)
    
    def get_size_in_mb(self, obj):
        """Get file size in megabytes"""
        return obj.size_in_mb
    
    def get_is_image(self, obj):
        """Check if media is an image"""
        return obj.is_image
    
    def get_is_video(self, obj):
        """Check if media is a video"""
        return obj.is_video
    
    def get_is_document(self, obj):
        """Check if media is a document"""
        return obj.is_document
    
    def get_is_audio(self, obj):
        """Check if media is an audio file"""
        return obj.is_audio
    
    @validates('media_type')
    def validate_media_type(self, value):
        """Validate media type"""
        valid_types = ['image', 'video', 'document', 'audio']
        if value not in valid_types:
            raise ValidationError(f'Invalid media type. Must be one of: {", ".join(valid_types)}')
    
    @validates('mime_type')
    def validate_mime_type(self, value):
        """Validate MIME type"""
        mime_regex = r'^[a-z]+/[a-z0-9\-\+\.]+$'
        if not re.match(mime_regex, value.lower()):
            raise ValidationError('Invalid MIME type format')
    
    @validates('file_size')
    def validate_file_size(self, value):
        """Validate file size"""
        if value <= 0:
            raise ValidationError('File size must be greater than 0')
        
        # 100MB limit for all files
        max_size = 100 * 1024 * 1024  # 100MB in bytes
        if value > max_size:
            raise ValidationError('File size cannot exceed 100MB')
    
    @validates('media_url')
    def validate_media_url(self, value):
        """Validate media URL"""
        url_regex = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_regex, value):
            raise ValidationError('Invalid media URL format')
    
    @validates_schema
    def validate_media(self, data, **kwargs):
        """Validate media data"""
        # Validate file name length
        if 'file_name' in data:
            if len(data['file_name']) > 255:
                raise ValidationError('File name is too long')
        
        # Validate file_metadata format if present
        if 'file_metadata' in data and data['file_metadata']:
            if not isinstance(data['file_metadata'], dict):
                raise ValidationError('File metadata must be a JSON object')
            
            # Validate specific file_metadata based on media type
            if data.get('media_type') == 'image':
                required_fields = ['width', 'height']
                for field in required_fields:
                    if field not in data['file_metadata']:
                        raise ValidationError(f'Image metadata must include {field}')
            
            elif data.get('media_type') == 'video':
                required_fields = ['duration', 'resolution']
                for field in required_fields:
                    if field not in data['file_metadata']:
                        raise ValidationError(f'Video metadata must include {field}')

# Initialize schema instances
media_schema = MediaSchema()
medias_schema = MediaSchema(many=True)

# Schema for media upload
class MediaUploadSchema(ma.Schema):
    file_name = fields.String(required=True)
    media_type = fields.String(required=True)
    mime_type = fields.String(required=True)
    file_size = fields.Integer(required=True)
    file_metadata = fields.Dict()
    
    @validates_schema
    def validate_upload(self, data, **kwargs):
        """Validate upload data"""
        # Validate file extension based on media type
        file_ext = data['file_name'].split('.')[-1].lower()
        valid_extensions = {
            'image': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
            'video': ['mp4', 'webm', 'mov'],
            'document': ['pdf', 'doc', 'docx', 'txt'],
            'audio': ['mp3', 'wav', 'ogg']
        }
        
        if data['media_type'] in valid_extensions:
            if file_ext not in valid_extensions[data['media_type']]:
                raise ValidationError(
                    f"Invalid file extension for {data['media_type']}. "
                    f"Must be one of: {', '.join(valid_extensions[data['media_type']])}"
                )

media_upload_schema = MediaUploadSchema()
