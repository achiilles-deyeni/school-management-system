import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
from models.teacher import Teacher
from utils.decorators import login_required, admin_required, teacher_required
from utils.validators import validate_teacher_data
import logging

teachers_bp = Blueprint('teachers', __name__)
UPLOAD_FOLDER = 'static/photos/teachers'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@teachers_bp.route('/')
@login_required
@admin_required
def list_teachers():
    try:
        subject = request.args.get('subject', '').strip()
        sort = request.args.get('sort', 'last_name')

        teachers = Teacher.get_all()

        # Filter
        if subject:
            teachers = [t for t in teachers if subject.lower() in t['Subjects_taught'].lower()]

        # Sort
        if sort == 'first_name':
            teachers.sort(key=lambda x: x['FirstName'])
        else:
            teachers.sort(key=lambda x: x['LastName'])

        return render_template('teachers/list.html', teachers=teachers, subject=subject, sort=sort)
    except Exception as e:
        logging.exception("Error listing teachers")
        flash("Failed to retrieve teacher list.", "danger")
        # Return empty teachers list instead of redirecting
        return render_template('teachers/list.html', teachers=[], subject='', sort='last_name')

@teachers_bp.route('/<int:teacher_id>')
@login_required
def view_teacher(teacher_id):
    teacher = Teacher.get_by_id(teacher_id)
    if not teacher:
        flash('Teacher not found.', 'warning')
        return redirect(url_for('teachers.list_teachers'))
    return render_template('teachers/view.html', teacher=teacher)

@teachers_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_teacher():
    if request.method == 'POST':
        data = request.form.to_dict()
        errors = validate_teacher_data(data)
        photo = request.files.get('photo')

        if errors:
            flash(f"Validation errors: {errors}", 'danger')
            return redirect(url_for('teachers.create_teacher'))

        filename = None
        if photo:
            ext = os.path.splitext(photo.filename)[1]
            filename = f"{uuid.uuid4().hex}{ext}"
            photo.save(os.path.join(UPLOAD_FOLDER, secure_filename(filename)))
            data['photo'] = filename

        Teacher.create(data)
        flash('Teacher created successfully.', 'success')
        return redirect(url_for('teachers.list_teachers'))

    return render_template('teachers/create.html')

@teachers_bp.route('/edit/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_teacher(teacher_id):
    teacher = Teacher.get_by_id(teacher_id)
    if not teacher:
        flash('Teacher not found.', 'warning')
        return redirect(url_for('teachers.list_teachers'))

    if request.method == 'POST':
        data = request.form.to_dict()
        errors = validate_teacher_data(data)
        photo = request.files.get('photo')

        if errors:
            flash(f"Validation errors: {errors}", 'danger')
            return redirect(url_for('teachers.edit_teacher', teacher_id=teacher_id))

        if photo:
            ext = os.path.splitext(photo.filename)[1]
            filename = f"{uuid.uuid4().hex}{ext}"
            photo.save(os.path.join(UPLOAD_FOLDER, secure_filename(filename)))
            data['photo'] = filename

        Teacher.update(teacher_id, data)
        flash('Teacher updated successfully.', 'success')
        return redirect(url_for('teachers.view_teacher', teacher_id=teacher_id))

    return render_template('teachers/edit.html', teacher=teacher)

@teachers_bp.route('/delete/<int:teacher_id>', methods=['POST'])
@login_required
@admin_required
def delete_teacher(teacher_id):
    teacher = Teacher.get_by_id(teacher_id)
    if not teacher:
        flash('Teacher not found.', 'warning')
    else:
        Teacher.delete(teacher_id)
        flash('Teacher deleted successfully.', 'info')
    return redirect(url_for('teachers.list_teachers'))

@teachers_bp.route('/photo/<filename>')
def serve_teacher_photo(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@teachers_bp.route('/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        teacher = Teacher.authenticate(email, password)
        if teacher:
            session['user_id'] = teacher['TeacherID']
            session['user_email'] = teacher['Email']
            session['user_role'] = 'teacher'
            flash('Login successful.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('teachers.teacher_login'))

    return render_template('teachers/login.html')

@teachers_bp.route('/logout')
@login_required
def logout_teacher():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('teachers.teacher_login'))
