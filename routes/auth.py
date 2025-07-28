from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from models.admin import Admin
from models.teacher import Teacher
from models.student import Student
from utils.validators import validate_email
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Index: redirect to register or login
@auth_bp.route('/')
def index():
    if not Admin.get_all():
        return redirect(url_for('auth.register_admin'))

    if 'user_role' in session:
        return redirect(url_for('auth.dashboard'))

    return redirect(url_for('auth.login'))

# # Admin registration (only shown if no admins exist)
# @auth_bp.route('/register', methods=['GET', 'POST'])
# def register_admin():
#     # if Admin.get_all():
#     #     flash("Admin already exists. Please log in.", "info")
#     #     return redirect(url_for('auth.login'))
#
#     if request.method == 'POST':
#         first_name = request.form.get('FirstName', '').strip()
#         last_name = request.form.get('LastName', '').strip()
#         email = request.form.get('Email', '').strip().lower()
#         password = request.form.get('password', '')
#
#         if not all([first_name, last_name, email, password]):
#             flash('All fields are required.', 'danger')
#             return render_template('register.html')
#
#         if not validate_email(email):
#             flash('Invalid email format.', 'danger')
#             return render_template('register.html')
#
#         try:
#             if Admin.email_exists(email):
#                 flash('Email already registered.', 'warning')
#                 return render_template('register.html')
#
#             Admin.create({
#                 'FirstName': first_name,
#                 'LastName': last_name,
#                 'Email': email,
#                 'Password': password  # Will be hashed in model
#             })
#
#             flash('Admin registered successfully. Please log in.', 'success')
#             return redirect(url_for('auth.login'))
#
#         except Exception:
#             logger.exception("Admin registration failed.")
#             flash('Registration failed. Try again.', 'danger')
#
#     return render_template('register.html')


# Replace your register_admin route with this debug version:

@auth_bp.route('/register', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        try:
            # Debug: Print all form data
            print("=== REGISTRATION DEBUG ===")
            print("Form data received:", dict(request.form))

            first_name = request.form.get('FirstName', '').strip()
            last_name = request.form.get('LastName', '').strip()
            email = request.form.get('Email', '').strip().lower()
            password = request.form.get('password', '')

            print(f"Parsed data:")
            print(f"  FirstName: '{first_name}'")
            print(f"  LastName: '{last_name}'")
            print(f"  Email: '{email}'")
            print(f"  Password length: {len(password)}")
            print(f"  All fields present: {all([first_name, last_name, email, password])}")

            # Check required fields
            if not all([first_name, last_name, email, password]):
                missing = []
                if not first_name: missing.append('FirstName')
                if not last_name: missing.append('LastName')
                if not email: missing.append('Email')
                if not password: missing.append('Password')
                print(f"Missing fields: {missing}")
                flash('All fields are required.', 'danger')
                return render_template('register.html')

            # Validate email
            print("Validating email...")
            if not validate_email(email):
                print("Email validation failed")
                flash('Invalid email format.', 'danger')
                return render_template('register.html')
            print("Email validation passed")

            # Test database connection first
            print("Testing database connection...")
            try:
                from database import query_db
                test_result = query_db("SELECT 1 AS test")
                print(f"Database connection test: {test_result}")
            except Exception as db_test_error:
                print(f"Database connection failed: {db_test_error}")
                flash(f'Database connection error: {str(db_test_error)}', 'danger')
                return render_template('register.html')

            # Check if Admin class and methods exist
            print("Testing Admin class...")
            try:
                print(f"Admin class: {Admin}")
                print(f"Admin.email_exists method: {hasattr(Admin, 'email_exists')}")
                print(f"Admin.create method: {hasattr(Admin, 'create')}")
            except Exception as class_error:
                print(f"Admin class error: {class_error}")
                flash(f'Admin class error: {str(class_error)}', 'danger')
                return render_template('register.html')

            # Check if email already exists
            print("Checking if email exists...")
            try:
                email_exists = Admin.email_exists(email)
                print(f"Email exists result: {email_exists}")
                if email_exists:
                    flash('Email already registered.', 'warning')
                    return render_template('register.html')
            except Exception as email_check_error:
                print(f"Email check failed: {email_check_error}")
                flash(f'Email check error: {str(email_check_error)}', 'danger')
                return render_template('register.html')

            # Create admin
            print("Creating admin...")
            admin_data = {
                'FirstName': first_name,
                'LastName': last_name,
                'Email': email,
                'Password': password
            }
            print(f"Admin data to create: {admin_data}")

            try:
                Admin.create(admin_data)
                print("Admin.create() completed successfully")
            except Exception as create_error:
                print(f"Admin.create() failed: {create_error}")
                print(f"Error type: {type(create_error)}")
                flash(f'Admin creation error: {str(create_error)}', 'danger')
                return render_template('register.html')

            print("Registration completed successfully!")
            flash('Admin registered successfully. Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            print(f"=== REGISTRATION ERROR ===")
            print(f"Error: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback:")
            traceback.print_exc()

            logger.exception("Admin registration failed.")
            flash(f'Registration failed: {str(e)}', 'danger')
            return render_template('register.html')

    return render_template('register.html')

# Login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('Email', '').strip().lower()
        password = request.form.get('Password', '')

        user_role = None
        user_data = None

        try:
            admin_result = Admin.authenticate(email, password)
            if admin_result:
                user_role = 'admin'
                user_data = admin_result
            else:
                teacher_result = Teacher.authenticate(email, password)
                if teacher_result:
                    user_role = 'teacher'
                    user_data = teacher_result
                else:
                    student_result = Student.authenticate(email, password)
                    if student_result:
                        user_role = 'student'
                        user_data = student_result

            if user_role and user_data:
                session['user_id'] = user_data['AdminID'] if user_role == 'admin' else \
                                     user_data['TeacherID'] if user_role == 'teacher' else \
                                     user_data['StudentID']
                session['user_role'] = user_role
                session['user_email'] = user_data['Email']
                flash(f"Logged in as {user_role.title()}", 'success')
                return redirect(url_for('auth.dashboard'))
            else:
                flash('Invalid email or password', 'danger')

        except Exception:
            logger.exception("Login failed.")
            flash("Login error occurred. Try again.", "danger")

    return render_template('login.html')

# Add this route to your auth.py file

@auth_bp.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        try:
            student_result = Student.authenticate(email, password)
            if student_result:
                session['user_id'] = student_result['StudentID']
                session['user_role'] = 'student'
                session['user_email'] = student_result['Email']
                flash("Logged in as Student", 'success')
                return redirect(url_for('auth.dashboard'))
            else:
                flash('Invalid email or password', 'danger')

        except Exception:
            logger.exception("Student login failed.")
            flash("Login error occurred. Try again.", "danger")

    return render_template('studentlogin.html')

# Dashboard
@auth_bp.route('/dashboard')
def dashboard():
    if 'user_role' not in session:
        return redirect(url_for('auth.login'))

    return render_template('dashboard.html')


# Add this route to your auth.py file, before the dashboard route

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('forgot_password.html')

        if not validate_email(email):
            flash('Invalid email format.', 'danger')
            return render_template('forgot_password.html')

        try:
            # Check if email exists in any of the user tables
            user_found = False
            user_type = None

            # Check Admin table
            if Admin.get_by_email(email):
                user_found = True
                user_type = 'admin'
            # Check Teacher table
            elif Teacher.get_by_email(email):
                user_found = True
                user_type = 'teacher'
            # Check Student table
            elif Student.get_by_email(email):
                user_found = True
                user_type = 'student'

            if user_found:
                # In a real application, you would:
                # 1. Generate a secure reset token
                # 2. Save it to database with expiration
                # 3. Send email with reset link
                # For now, we'll just show a success message
                flash('If an account with that email exists, password reset instructions have been sent.', 'info')
                logger.info(f"Password reset requested for {user_type} email: {email}")
            else:
                # Don't reveal if email doesn't exist for security reasons
                flash('If an account with that email exists, password reset instructions have been sent.', 'info')
                logger.warning(f"Password reset requested for non-existent email: {email}")

        except Exception:
            logger.exception("Forgot password error.")
            flash("An error occurred. Please try again.", "danger")

    return render_template('forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # In a real application, you would:
    # 1. Validate the token
    # 2. Check if it's not expired
    # 3. Allow password reset
    # For now, this is a placeholder

    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not new_password or not confirm_password:
            flash('Please fill in all fields.', 'danger')
            return render_template('reset_password.html', token=token)

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)

        if len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('reset_password.html', token=token)

        # TODO: Implement actual password reset logic
        flash('Password reset functionality is not yet implemented.', 'warning')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)

# Logout
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('auth.login'))
