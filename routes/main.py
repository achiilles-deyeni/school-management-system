from flask import Blueprint, render_template, session
from utils.decorators import login_required

main_bp = Blueprint('main', __name__)

@main_bp.app_context_processor
def inject_current_user():
    return dict(current_user=session.get('user'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    user = session.get('user')
    return render_template("dashboard.html", user=user)
