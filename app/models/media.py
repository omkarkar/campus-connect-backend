from datetime import datetime
from . import db

class Media(db.Model):
    __tablename__ = 'media'
    
    media_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    media_type = db.Column(db.String(50), nullable=False)  # 'image', 'video', 'document', 'audio'
    file_name = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    media_url = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    file_hash = db.Column(db.String(64))  # SHA-256 hash for deduplication
    file_metadata = db.Column(db.JSON)  # Store additional metadata (dimensions, duration, etc.)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Media {self.file_name} ({self.media_type})>'
    
    @property
    def size_in_mb(self):
        """Return file size in megabytes"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def is_image(self):
        return self.media_type == 'image'
    
    @property
    def is_video(self):
        return self.media_type == 'video'
    
    @property
    def is_document(self):
        return self.media_type == 'document'
    
    @property
    def is_audio(self):
        return self.media_type == 'audio'
    
    def soft_delete(self):
        """Soft delete the media file"""
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = datetime.utcnow()
            return True
        return False
    
    def update_last_accessed(self):
        """Update the last accessed timestamp"""
        self.last_accessed = datetime.utcnow()
    
    @staticmethod
    def get_by_hash(file_hash):
        """Find media by file hash to prevent duplicates"""
        return Media.query.filter_by(file_hash=file_hash, is_deleted=False).first()
