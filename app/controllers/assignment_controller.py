from flask import Blueprint, request, jsonify, g, current_app
from marshmallow import ValidationError
from datetime import datetime

from ..services import assignment_service
from ..schemas.assignment import (
    assignment_schema,
    assignments_schema,
    assignment_list_schema,
    assignments_list_schema,
    assignment_submission_schema
)
from .user_controller import login_required

assignment_bp = Blueprint('assignment', __name__)

@assignment_bp.route('/', methods=['POST'])
@login_required
def create_assignment():
    """Create a new assignment"""
    try:
        data = request.get_json()
        assignment = assignment_schema.load(data)
        created_assignment = assignment_service.create_assignment(
            assignment_schema.dump(assignment)
        )
        return jsonify(assignment_schema.dump(created_assignment)), 201
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating assignment: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@assignment_bp.route('/', methods=['GET'])
@login_required
def get_assignments():
    """Get assignments with optional filters"""
    try:
        # Get query parameters
        course_id = request.args.get('course_id', type=int)
        query = request.args.get('q')
        include_past = request.args.get('include_past', 'false').lower() == 'true'
        upcoming_days = request.args.get('upcoming_days', type=int)
        overdue_only = request.args.get('overdue_only', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        if query:
            # Search assignments
            result = assignment_service.search_assignments(
                query, course_id, include_past, page, per_page
            )
        elif upcoming_days:
            # Get upcoming assignments
            result = assignment_service.get_upcoming_assignments(
                course_id, upcoming_days, page, per_page
            )
        elif overdue_only:
            # Get overdue assignments
            result = assignment_service.get_overdue_assignments(
                course_id, page, per_page
            )
        else:
            # Get all assignments (paginated)
            result = assignment_service.get_all(page, per_page)
        
        return jsonify({
            'assignments': assignments_list_schema.dump(result['items']),
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting assignments: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@assignment_bp.route('/<int:assignment_id>', methods=['GET'])
@login_required
def get_assignment(assignment_id):
    """Get a specific assignment"""
    try:
        assignment = assignment_service.get_by_id(assignment_id)
        if not assignment:
            return jsonify({'message': 'Assignment not found'}), 404
        return jsonify(assignment_schema.dump(assignment)), 200
    except Exception as e:
        current_app.logger.error(f"Error getting assignment: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@assignment_bp.route('/<int:assignment_id>', methods=['PUT'])
@login_required
def update_assignment(assignment_id):
    """Update an assignment"""
    try:
        assignment = assignment_service.get_by_id(assignment_id)
        if not assignment:
            return jsonify({'message': 'Assignment not found'}), 404
            
        # Check if user is the professor of the course
        if assignment.course.professor_id != g.current_user.user_id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        updated_assignment = assignment_service.update(assignment_id, data)
        return jsonify(assignment_schema.dump(updated_assignment)), 200
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating assignment: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@assignment_bp.route('/<int:assignment_id>', methods=['DELETE'])
@login_required
def delete_assignment(assignment_id):
    """Delete an assignment"""
    try:
        assignment = assignment_service.get_by_id(assignment_id)
        if not assignment:
            return jsonify({'message': 'Assignment not found'}), 404
            
        # Check if user is the professor of the course
        if assignment.course.professor_id != g.current_user.user_id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        assignment_service.delete(assignment_id)
        return jsonify({'message': 'Assignment deleted successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting assignment: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@assignment_bp.route('/<int:assignment_id>/status', methods=['PUT'])
@login_required
def update_status(assignment_id):
    """Update assignment status"""
    try:
        assignment = assignment_service.get_by_id(assignment_id)
        if not assignment:
            return jsonify({'message': 'Assignment not found'}), 404
            
        # Check if user is the professor of the course
        if assignment.course.professor_id != g.current_user.user_id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        status = data.get('status')
        
        if status is None:
            return jsonify({'message': 'Status is required'}), 400
            
        if assignment_service.update_assignment_status(assignment_id, status):
            return jsonify({'message': 'Assignment status updated successfully'}), 200
        return jsonify({'message': 'Failed to update assignment status'}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating assignment status: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@assignment_bp.route('/<int:assignment_id>/extend', methods=['PUT'])
@login_required
def extend_due_date(assignment_id):
    """Extend assignment due date"""
    try:
        assignment = assignment_service.get_by_id(assignment_id)
        if not assignment:
            return jsonify({'message': 'Assignment not found'}), 404
            
        # Check if user is the professor of the course
        if assignment.course.professor_id != g.current_user.user_id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        new_due_date = datetime.strptime(
            data.get('new_due_date'),
            '%Y-%m-%d %H:%M:%S'
        )
        
        updated_assignment = assignment_service.extend_due_date(
            assignment_id,
            new_due_date
        )
        
        if updated_assignment:
            return jsonify(assignment_schema.dump(updated_assignment)), 200
        return jsonify({'message': 'Failed to extend due date'}), 400
    except ValueError as e:
        return jsonify({'message': 'Invalid date format'}), 400
    except Exception as e:
        current_app.logger.error(f"Error extending due date: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@assignment_bp.route('/<int:assignment_id>/statistics', methods=['GET'])
@login_required
def get_statistics(assignment_id):
    """Get assignment statistics"""
    try:
        stats = assignment_service.get_assignment_statistics(assignment_id)
        return jsonify(stats), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error getting assignment statistics: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@assignment_bp.route('/upcoming', methods=['GET'])
@login_required
def get_upcoming():
    """Get upcoming assignments"""
    try:
        course_id = request.args.get('course_id', type=int)
        days = int(request.args.get('days', 7))
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        result = assignment_service.get_upcoming_assignments(
            course_id, days, page, per_page
        )
        
        return jsonify({
            'assignments': assignments_list_schema.dump(result['items']),
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting upcoming assignments: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@assignment_bp.route('/overdue', methods=['GET'])
@login_required
def get_overdue():
    """Get overdue assignments"""
    try:
        course_id = request.args.get('course_id', type=int)
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        result = assignment_service.get_overdue_assignments(
            course_id, page, per_page
        )
        
        return jsonify({
            'assignments': assignments_list_schema.dump(result['items']),
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting overdue assignments: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500
