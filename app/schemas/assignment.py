from marshmallow import fields, validates, ValidationError, validates_schema, pre_load
from . import ma, BaseSchema
from ..models.assignment import Assignment
from datetime import datetime, timedelta

class AssignmentSchema(BaseSchema):
    """Schema for Assignment model"""
    
    class Meta:
        model = Assignment
        load_instance = True
        include_fk = True
        dump_only = ('assignment_id', 'created_on', 'updated_at')
    
    # Nested relationships
    course = fields.Nested(
        'CourseSchema',
        only=('course_id', 'course_name', 'semester'),
        dump_only=True
    )
    
    # Custom fields
    is_overdue = fields.Method("get_is_overdue", dump_only=True)
    time_remaining = fields.Method("get_time_remaining", dump_only=True)
    completion_percentage = fields.Method("get_completion_percentage", dump_only=True)
    
    def get_is_overdue(self, obj):
        """Check if assignment is overdue"""
        return obj.is_overdue
    
    def get_time_remaining(self, obj):
        """Get time remaining until due date"""
        return obj.time_remaining
    
    def get_completion_percentage(self, obj):
        """Get completion percentage"""
        return obj.completion_percentage
    
    @validates('title')
    def validate_title(self, value):
        """Validate assignment title"""
        if len(value.strip()) < 3:
            raise ValidationError('Title must be at least 3 characters long')
        if len(value) > 255:
            raise ValidationError('Title must not exceed 255 characters')
    
    @validates('description')
    def validate_description(self, value):
        """Validate assignment description"""
        if value and len(value.strip()) < 10:
            raise ValidationError('Description must be at least 10 characters long')
    
    @validates('max_score')
    def validate_max_score(self, value):
        """Validate maximum score"""
        if value <= 0:
            raise ValidationError('Maximum score must be greater than 0')
        if value > 1000:  # Arbitrary maximum
            raise ValidationError('Maximum score cannot exceed 1000')
    
    @validates('total_points')
    def validate_total_points(self, value):
        """Validate total points"""
        if value < 0:
            raise ValidationError('Total points cannot be negative')
    
    @pre_load
    def process_dates(self, data, **kwargs):
        """Process date strings into datetime objects"""
        if 'due_date' in data and isinstance(data['due_date'], str):
            try:
                data['due_date'] = datetime.strptime(
                    data['due_date'],
                    '%Y-%m-%d %H:%M:%S'
                )
            except ValueError:
                raise ValidationError('Invalid date format. Use YYYY-MM-DD HH:MM:SS')
        return data
    
    @validates_schema
    def validate_assignment(self, data, **kwargs):
        """Validate assignment data"""
        # Validate due date
        if 'due_date' in data:
            due_date = data['due_date']
            now = datetime.utcnow()
            
            # Due date should be at least 1 hour in the future
            min_due_date = now + timedelta(hours=1)
            if due_date < min_due_date:
                raise ValidationError('Due date must be at least 1 hour in the future')
            
            # Due date should not be more than 6 months in the future
            max_due_date = now + timedelta(days=180)
            if due_date > max_due_date:
                raise ValidationError('Due date cannot be more than 6 months in the future')
        
        # Validate total points against max score
        if 'total_points' in data and 'max_score' in data:
            if data['total_points'] > data['max_score']:
                raise ValidationError('Total points cannot exceed maximum score')

# Initialize schema instances
assignment_schema = AssignmentSchema()
assignments_schema = AssignmentSchema(many=True)

# Schema for assignment listing (with fewer fields)
class AssignmentListSchema(AssignmentSchema):
    class Meta(AssignmentSchema.Meta):
        fields = (
            'assignment_id', 'title', 'due_date', 'max_score',
            'total_points', 'status', 'is_overdue', 'time_remaining',
            'completion_percentage', 'course'
        )

assignment_list_schema = AssignmentListSchema()
assignments_list_schema = AssignmentListSchema(many=True)

# Schema for assignment submission
class AssignmentSubmissionSchema(ma.Schema):
    assignment_id = fields.Integer(required=True)
    student_id = fields.Integer(required=True)
    submission_text = fields.String()
    attachment_urls = fields.List(fields.String())
    submitted_at = fields.DateTime(dump_only=True)

assignment_submission_schema = AssignmentSubmissionSchema()
assignments_submission_schema = AssignmentSubmissionSchema(many=True)
