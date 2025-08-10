from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.admin import Admin
from utils.decorators import login_required, admin_required
from utils.validators import validate_admin_data
import logging

admin_bp = Blueprint('admins', __name__)


@admin_bp.route('/register', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        data = request.form.to_dict()
        errors = validate_admin_data(data)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(request.url)
        try:
            existing_admin = Admin.get_by_email(data['Email'])
            if existing_admin:
                flash("An account with this email already exists.", "warning")
                return redirect(request.url)

            Admin.create(data)
            flash("Admin registered successfully. You can now log in.", "success")
            # Optional: Auto-login after registration
            admin = Admin.authenticate(data['Email'], data['Password'])
            if admin:
                session['admin_id'] = admin['AdminID']
                session['admin_email'] = admin['Email']
                session['admin_name'] = f"{admin['FirstName']} {admin['LastName']}"
                return redirect(url_for('main.dashboard'))
            return redirect(url_for('auth.login'))
        except Exception:
            logging.exception("Error during registration")
            flash("Failed to register admin", "danger")
    return render_template('admins/register.html')


@admin_bp.route('/')
@login_required
@admin_required
def list_admins():
    try:
        admins = Admin.get_all()
        return render_template('admins/list.html', admins=admins)
    except Exception:
        logging.exception("Failed to fetch admin list")
        flash("Unable to retrieve admin list", "danger")
        return redirect(url_for('main.dashboard'))


@admin_bp.route('/<int:admin_id>')
@login_required
@admin_required
def view_admin(admin_id):
    admin = Admin.get_by_id(admin_id)
    if not admin:
        flash("Admin not found", "warning")
        return redirect(url_for('admins.list_admins'))
    return render_template('admins/view.html', admin=admin)


@admin_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_admin():
    if request.method == 'POST':
        data = request.form.to_dict()
        errors = validate_admin_data(data)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(request.url)
        try:
            existing = Admin.get_by_email(data['Email'])
            if existing:
                flash("Email already exists.", "warning")
                return redirect(request.url)
            Admin.create(data)
            flash("Admin created successfully", "success")
            return redirect(url_for('admins.list_admins'))
        except Exception:
            logging.exception("Error creating admin")
            flash("Failed to create admin", "danger")
    return render_template('admins/create.html')


@admin_bp.route('/<int:admin_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_admin(admin_id):
    admin = Admin.get_by_id(admin_id)
    if not admin:
        flash("Admin not found", "warning")
        return redirect(url_for('admins.list_admins'))
    if request.method == 'POST':
        data = request.form.to_dict()
        errors = validate_admin_data(data)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(request.url)
        try:
            Admin.update(admin_id, data)
            flash("Admin updated successfully", "success")
            return redirect(url_for('admins.view_admin', admin_id=admin_id))
        except Exception:
            logging.exception("Error updating admin")
            flash("Failed to update admin", "danger")
    return render_template('admins/edit.html', admin=admin)


@admin_bp.route('/<int:admin_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_admin(admin_id):
    try:
        Admin.delete(admin_id)
        flash("Admin deleted successfully", "info")
    except Exception as e:
        logging.exception("Error deleting admin")
        flash(str(e), "danger")
    return redirect(url_for('admins.list_admins'))
