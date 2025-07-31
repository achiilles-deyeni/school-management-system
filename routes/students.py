# routes/students.py - Enhanced Student Management Routes
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.utils import secure_filename
from models.student import Student
from models.teacher import Teacher
from utils.decorators import login_required, admin_required, student_required, teacher_required, admin_or_teacher_required
from utils.validators import validate_student_data, validate_email, validate_phone
from utils.file_handler import allowed_file, save_student_photo
import os
import csv
import io
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

students_bp = Blueprint('students', __name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads/students'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@students_bp.route('/')
@login_required
@admin_or_teacher_required
def list_students():
    """List all students with search, filter, and pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        class_filter = request.args.get('class', '').strip()
        gender_filter = request.args.get('gender', '').strip()
        sort_by = request.args.get('sort', 'last_name')
        sort_order = request.args.get('order', 'asc')

        # Validate pagination parameters
        per_page = min(max(per_page, 5), 100)  # Between 5 and 100
        page = max(page, 1)

        # Get filtered and paginated students
        result = Student.get_paginated(
            page=page,
            per_page=per_page,
            search=search,
            class_filter=class_filter,
            gender_filter=gender_filter,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Get available classes for filter dropdown
        classes = Student.get_all_classes()

        return render_template('students/list.html',
                               students=result['students'],
                               pagination=result['pagination'],
                               classes=classes,
                               current_filters={
                                   'search': search,
                                   'class': class_filter,
                                   'gender': gender_filter,
                                   'sort': sort_by,
                                   'order': sort_order
                               })

    except Exception as e:
        logger.error(f"Error listing students: {str(e)}")
        flash('Error retrieving student list', 'danger')
        return render_template('students/list.html', students=[], pagination=None, classes=[])


@students_bp.route('/<int:student_id>')
@login_required
def view_student(student_id):
    """View detailed student information"""
    try:
        student = Student.get_by_id(student_id)
        if not student:
            flash('Student not found', 'warning')
            return redirect(url_for('students.list_students'))

        # Get additional student data
        academic_history = Student.get_academic_history(student_id)
        attendance_summary = Student.get_attendance_summary(student_id)

        return render_template('students/detail.html',
                               student=student,
                               academic_history=academic_history,
                               attendance_summary=attendance_summary)

    except Exception as e:
        logger.error(f"Error viewing student {student_id}: {str(e)}")
        flash('Error retrieving student information', 'danger')
        return redirect(url_for('students.list_students'))


@students_bp.route('/profile')
@student_required
def profile():
    """Student's own profile page"""
    try:
        student_id = session.get('user_id')
        student = Student.get_by_student_id(student_id)

        if not student:
            flash('Student profile not found', 'danger')
            return redirect(url_for('auth.student_login'))

        # Get student's academic information
        current_results = Student.get_current_term_results(student_id)
        attendance_summary = Student.get_attendance_summary(student['id'])
        upcoming_events = Student.get_upcoming_events(student['id'])

        return render_template('students/profile.html',
                               student=student,
                               results=current_results,
                               attendance=attendance_summary,
                               events=upcoming_events)

    except Exception as e:
        logger.error(f"Error loading student profile: {str(e)}")
        flash('Error loading profile', 'danger')
        return redirect(url_for('auth.student_login'))


@students_bp.route('/new', methods=['GET', 'POST'])
@admin_required
def new_student():
    """Add a new student"""
    if request.method == 'POST':
        try:
            # Get and validate form data
            student_data = {
                'first_name': request.form.get('first_name', '').strip(),
                'last_name': request.form.get('last_name', '').strip(),
                'gender': request.form.get('gender', ''),
                'date_of_birth': request.form.get('date_of_birth', ''),
                'guardian_name': request.form.get('guardian_name', '').strip(),
                'guardian_phone': request.form.get('guardian_phone', '').strip(),
                'guardian_email': request.form.get('guardian_email', '').strip(),
                'address': request.form.get('address', '').strip(),
                'class_name': request.form.get('class_name', '').strip(),
                'admission_date': request.form.get('admission_date', ''),
                'teacher_id': request.form.get('teacher_id') or None,
                'medical_info': request.form.get('medical_info', '').strip(),
                'emergency_contact': request.form.get('emergency_contact', '').strip(),
                'emergency_phone': request.form.get('emergency_phone', '').strip()
            }

            # Validate input data
            validation_errors = validate_student_data(student_data)
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'danger')
                return render_template('students/new.html',
                                       student_data=student_data,
                                       teachers=Teacher.get_all_active())

            # Handle photo upload
            photo_filename = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
                    photo_filename = save_student_photo(file)

            student_data['photo'] = photo_filename

            # Create student
            student_id = Student.create(student_data)

            flash('Student added successfully', 'success')
            logger.info(f"New student created with ID: {student_id}")
            return redirect(url_for('students.view_student', student_id=student_id))

        except Exception as e:
            logger.error(f"Error creating student: {str(e)}")
            flash('Error adding student. Please try again.', 'danger')
            return render_template('students/new.html',
                                   student_data=request.form,
                                   teachers=Teacher.get_all_active())

    # GET request - show form
    try:
        teachers = Teacher.get_all_active()
        return render_template('students/new.html', teachers=teachers)
    except Exception as e:
        logger.error(f"Error loading new student form: {str(e)}")
        flash('Error loading form', 'danger')
        return redirect(url_for('students.list_students'))


@students_bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    """Edit student information"""
    try:
        student = Student.get_by_id(student_id)
        if not student:
            flash('Student not found', 'warning')
            return redirect(url_for('students.list_students'))

        if request.method == 'POST':
            # Get and validate form data
            student_data = {
                'first_name': request.form.get('first_name', '').strip(),
                'last_name': request.form.get('last_name', '').strip(),
                'gender': request.form.get('gender', ''),
                'date_of_birth': request.form.get('date_of_birth', ''),
                'guardian_name': request.form.get('guardian_name', '').strip(),
                'guardian_phone': request.form.get('guardian_phone', '').strip(),
                'guardian_email': request.form.get('guardian_email', '').strip(),
                'address': request.form.get('address', '').strip(),
                'class_name': request.form.get('class_name', '').strip(),
                'teacher_id': request.form.get('teacher_id') or None,
                'medical_info': request.form.get('medical_info', '').strip(),
                'emergency_contact': request.form.get('emergency_contact', '').strip(),
                'emergency_phone': request.form.get('emergency_phone', '').strip(),
                'status': request.form.get('status', 'active')
            }

            # Validate input data
            validation_errors = validate_student_data(student_data, is_update=True)
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'danger')
                return render_template('students/edit.html',
                                       student=student,
                                       teachers=Teacher.get_all_active())

            # Handle photo upload
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
                    photo_filename = save_student_photo(file, student_id)
                    student_data['photo'] = photo_filename

            # Update student
            Student.update(student_id, student_data)

            flash('Student updated successfully', 'success')
            logger.info(f"Student {student_id} updated")
            return redirect(url_for('students.view_student', student_id=student_id))

        # GET request - show form
        teachers = Teacher.get_all_active()
        return render_template('students/edit.html',
                               student=student,
                               teachers=teachers)

    except Exception as e:
        logger.error(f"Error editing student {student_id}: {str(e)}")
        flash('Error updating student', 'danger')
        return redirect(url_for('students.list_students'))


@students_bp.route('/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    """Soft delete a student (mark as inactive)"""
    try:
        student = Student.get_by_id(student_id)
        if not student:
            flash('Student not found', 'warning')
            return redirect(url_for('students.list_students'))

        # Soft delete (mark as inactive)
        Student.soft_delete(student_id)

        flash(f'Student {student["first_name"]} {student["last_name"]} has been deactivated', 'success')
        logger.info(f"Student {student_id} soft deleted")
        return redirect(url_for('students.list_students'))

    except Exception as e:
        logger.error(f"Error deleting student {student_id}: {str(e)}")
        flash('Error deactivating student', 'danger')
        return redirect(url_for('students.list_students'))


@students_bp.route('/bulk-import', methods=['GET', 'POST'])
@admin_required
def bulk_import():
    """Bulk import students from CSV file"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'danger')
                return redirect(request.url)

            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(request.url)

            if not file.filename.endswith('.csv'):
                flash('Please upload a CSV file', 'danger')
                return redirect(request.url)

            # Process CSV file
            result = Student.bulk_import_from_csv(file)

            if result['success']:
                flash(f'Successfully imported {result["imported"]} students. {result["errors"]} errors.', 'success')
                if result['error_details']:
                    for error in result['error_details'][:10]:  # Show first 10 errors
                        flash(f'Row {error["row"]}: {error["message"]}', 'warning')
            else:
                flash('Import failed. Please check your file format.', 'danger')

            return redirect(url_for('students.list_students'))

        except Exception as e:
            logger.error(f"Error in bulk import: {str(e)}")
            flash('Error processing file', 'danger')
            return redirect(request.url)

    return render_template('students/bulk_import.html')


@students_bp.route('/export')
@admin_required
def export_students():
    """Export students to CSV"""
    try:
        # Get filter parameters
        class_filter = request.args.get('class', '')
        gender_filter = request.args.get('gender', '')
        status_filter = request.args.get('status', 'active')

        students = Student.get_for_export(class_filter, gender_filter, status_filter)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Student ID', 'First Name', 'Last Name', 'Gender', 'Date of Birth',
            'Class', 'Guardian Name', 'Guardian Phone', 'Guardian Email',
            'Address', 'Admission Date', 'Status'
        ])

        # Write data
        for student in students:
            writer.writerow([
                student['student_id'], student['first_name'], student['last_name'],
                student['gender'], student['date_of_birth'], student['class_name'],
                student['guardian_name'], student['guardian_phone'],
                student['guardian_email'], student['address'],
                student['admission_date'], student['status']
            ])

        # Create response
        output.seek(0)
        filename = f"students_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Error exporting students: {str(e)}")
        flash('Error exporting students', 'danger')
        return redirect(url_for('students.list_students'))


@students_bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for student search (AJAX)"""
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)

        if len(query) < 2:
            return jsonify({'students': []})

        students = Student.search(query, limit)

        return jsonify({
            'students': [{
                'id': s['id'],
                'student_id': s['student_id'],
                'name': f"{s['first_name']} {s['last_name']}",
                'class': s['class_name'],
                'photo': s['photo']
            } for s in students]
        })

    except Exception as e:
        logger.error(f"Error in student search API: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500


@students_bp.route('/<int:student_id>/photo')
@login_required
def student_photo(student_id):
    """Serve student photo"""
    try:
        student = Student.get_by_id(student_id)
        if not student or not student.get('photo'):
            # Return default avatar
            return redirect(url_for('static', filename='images/default_avatar.png'))

        photo_path = os.path.join(UPLOAD_FOLDER, student['photo'])
        if os.path.exists(photo_path):
            return send_file(photo_path)
        else:
            return redirect(url_for('static', filename='images/default_avatar.png'))

    except Exception as e:
        logger.error(f"Error serving student photo: {str(e)}")
        return redirect(url_for('static', filename='images/default_avatar.png'))


@students_bp.route('/<int:student_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_status(student_id):
    """Toggle student active/inactive status"""
    try:
        student = Student.get_by_id(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        new_status = 'inactive' if student['status'] == 'active' else 'active'
        Student.update_status(student_id, new_status)

        return jsonify({
            'success': True,
            'status': new_status,
            'message': f'Student status changed to {new_status}'
        })

    except Exception as e:
        logger.error(f"Error toggling student status: {str(e)}")
        return jsonify({'error': 'Failed to update status'}), 500


# Error handlers specific to students blueprint
@students_bp.errorhandler(413)
def file_too_large(e):
    flash('File too large. Maximum size is 5MB.', 'danger')
    return redirect(request.url)


@students_bp.errorhandler(404)
def student_not_found(e):
    flash('Student not found', 'warning')
    return redirect(url_for('students.list_students'))