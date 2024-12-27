from marshmallow import fields, validates, ValidationError, validates_schema, pre_load
from . import ma, BaseSchema
from ..models.course import Course
from datetime import datetime

class CourseSchema(BaseSchema):
    """Schema for Course model"""
    
    class Meta:
        model = Course
        load_instance = True
        include_fk = True
        dump_only = ('course_id', 'created_at', 'updated_at')
    
    # Nested relationships
    professor = fields.Nested(
        'UserProfileSchema',
        only=('user_id', 'full_name', 'email'),
        dump_only=True
    )
    assignments = fields.Nested(
        'AssignmentSchema',
        many=True,
        exclude=('course',),
        dump_only=True
    )
    
    # Custom fields
    assignment_count = fields.Method("get_assignment_count", dump_only=True)
    active_assignments = fields.Method("get_active_assignments", dump_only=True)
    
    def get_assignment_count(self, obj):
        """Get total number of assignments"""
        return len(obj.assignments)
    
    def get_active_assignments(self, obj):
        """Get number of active assignments"""
        return len([a for a in obj.assignments if not a.is_overdue])
    
    @validates('course_name')
    def validate_course_name(self, value):
        """Validate course name"""
        if len(value.strip()) < 3:
            raise ValidationError('Course name must be at least 3 characters long')
        if len(value) > 255:
            raise ValidationError('Course name must not exceed 255 characters')
    
    @validates('semester')
    def validate_semester(self, value):
        """Validate semester format"""
        valid_semesters = ['Fall', 'Spring', 'Summer']
        semester_parts = value.split()
        
        if len(semester_parts) != 2:
            raise ValidationError('Semester must be in format: [Fall/Spring/Summer] YYYY')
        
        semester, year = semester_parts
        if semester not in valid_semesters:
            raise ValidationError('Invalid semester. Must be Fall, Spring, or Summer')
        
        try:
            year = int(year)
            current_year = datetime.now().year
            if year < current_year or year > current_year + 2:
                raise ValidationError(f'Year must be between {current_year} and {current_year + 2}')
        except ValueError:
            raise ValidationError('Invalid year format')
    
    @pre_load
    def process_dates(self, data, **kwargs):
        """Process date strings into datetime objects"""
        if 'date_and_year' in data and isinstance(data['date_and_year'], str):
            try:
                data['date_and_year'] = datetime.strptime(
                    data['date_and_year'],
                    '%Y-%m-%d %H:%M:%S'
                )
            except ValueError:
                raise ValidationError('Invalid date format. Use YYYY-MM-DD HH:MM:SS')
        return data
    
    @validates_schema
    def validate_dates(self, data, **kwargs):
        """Validate date logic"""
        if 'date_and_year' in data:
            date = data['date_and_year']
            now = datetime.utcnow()
            
            # Course date should not be more than 1 year in the future
            max_future = datetime(now.year + 1, now.month, now.day)
            if date > max_future:
                raise ValidationError('Course date cannot be more than 1 year in the future')

# Initialize schema instances
course_schema = CourseSchema()
courses_schema = CourseSchema(many=True)

# Schema for course listing (with fewer fields)
class CourseListSchema(CourseSchema):
    class Meta(CourseSchema.Meta):
        fields = (
            'course_id', 'course_name', 'semester', 'professor',
            'assignment_count', 'active_assignments'
        )

course_list_schema = CourseListSchema()
courses_list_schema = CourseListSchema(many=True)
