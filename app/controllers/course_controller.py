from flask import Blueprint, request, jsonify, g, current_app
from marshmallow import ValidationError
from datetime import datetime

from ..services import course_service
from ..schemas.course import (
    course_schema,
    courses_schema,
    course_list_schema,
    courses_list_schema
)
from .user_controller import login_required

course_bp = Blueprint('course', __name__)

@course_bp.route('/', methods=['POST'])
@login_required
def create_course():
    """Create a new course"""
    try:
        data = request.get_json()
        # Set the current user as professor if not specified
        if 'professor_id' not in data:
            data['professor_id'] = g.current_user.user_id
            
        course = course_schema.load(data)
        created_course = course_service.create_course(course_schema.dump(course))
        return jsonify(course_schema.dump(created_course)), 201
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating course: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@course_bp.route('/', methods=['GET'])
@login_required
def get_courses():
    """Get courses with optional filters"""
    try:
        # Get query parameters
        semester = request.args.get('semester')
        query = request.args.get('q')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        if query:
            # Search courses
            result = course_service.search_courses(query, semester, page, per_page)
        elif semester:
            # Get courses by semester
            result = course_service.get_courses_by_semester(semester, page, per_page)
        elif active_only:
            # Get active courses
            result = course_service.get_active_courses(page, per_page)
        else:
            # Get all courses (paginated)
            result = course_service.get_all(page, per_page)
        
        return jsonify({
            'courses': courses_list_schema.dump(result['items']),
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting courses: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@course_bp.route('/<int:course_id>', methods=['GET'])
@login_required
def get_course(course_id):
    """Get a specific course with its assignments"""
    try:
        course = course_service.get_course_with_assignments(course_id)
        if not course:
            return jsonify({'message': 'Course not found'}), 404
        return jsonify(course_schema.dump(course)), 200
    except Exception as e:
        current_app.logger.error(f"Error getting course: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@course_bp.route('/<int:course_id>', methods=['PUT'])
@login_required
def update_course(course_id):
    """Update a course"""
    try:
        course = course_service.get_by_id(course_id)
        if not course:
            return jsonify({'message': 'Course not found'}), 404
            
        # Check if user is the professor of the course
        if course.professor_id != g.current_user.user_id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        updated_course = course_service.update(course_id, data)
        return jsonify(course_schema.dump(updated_course)), 200
    except ValidationError as e:
        return jsonify({'message': 'Validation error', 'errors': e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating course: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@course_bp.route('/<int:course_id>', methods=['DELETE'])
@login_required
def delete_course(course_id):
    """Delete a course"""
    try:
        course = course_service.get_by_id(course_id)
        if not course:
            return jsonify({'message': 'Course not found'}), 404
            
        # Check if user is the professor of the course
        if course.professor_id != g.current_user.user_id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        course_service.delete(course_id)
        return jsonify({'message': 'Course deleted successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting course: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@course_bp.route('/professor/<int:professor_id>', methods=['GET'])
@login_required
def get_professor_courses(professor_id):
    """Get courses taught by a specific professor"""
    try:
        semester = request.args.get('semester')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        result = course_service.get_courses_by_professor(
            professor_id,
            semester,
            page,
            per_page
        )
        
        return jsonify({
            'courses': courses_list_schema.dump(result['items']),
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting professor courses: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@course_bp.route('/<int:course_id>/assignments', methods=['GET'])
@login_required
def get_course_assignments(course_id):
    """Get assignments for a specific course"""
    try:
        include_past = request.args.get('include_past', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        result = course_service.get_course_assignments(
            course_id,
            include_past,
            page,
            per_page
        )
        
        # Note: You'll need to import and use assignment_schema here
        return jsonify({
            'assignments': result['items'],
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'per_page': result['per_page']
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting course assignments: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@course_bp.route('/<int:course_id>/professor', methods=['PUT'])
@login_required
def update_course_professor(course_id):
    """Update the professor for a course (admin only)"""
    try:
        # Add admin check here
        data = request.get_json()
        new_professor_id = data.get('professor_id')
        
        if not new_professor_id:
            return jsonify({'message': 'New professor ID is required'}), 400
            
        if course_service.update_course_professor(course_id, new_professor_id):
            return jsonify({'message': 'Course professor updated successfully'}), 200
        return jsonify({'message': 'Course or professor not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error updating course professor: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500
