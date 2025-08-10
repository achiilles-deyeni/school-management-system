# routes/log.py - Log routes
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models.log import Log
from utils.decorators import login_required, admin_required
import logging
from datetime import datetime, timedelta

logs_bp = Blueprint('logs', __name__)


@logs_bp.route('/')
@login_required
@admin_required
def list_logs():
    """Display paginated list of logs with filtering options"""
    try:
        # Get filter parameters
        limit = int(request.args.get('limit', 100))
        action_filter = request.args.get('action')
        user_filter = request.args.get('user')
        table_filter = request.args.get('table')
        search_term = request.args.get('search')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Apply filters
        if search_term:
            logs = Log.search_logs(search_term, limit)
        elif start_date and end_date:
            logs = Log.get_by_date_range(start_date, end_date, limit)
        elif action_filter:
            logs = Log.get_by_action(action_filter, limit)
        elif user_filter:
            logs = Log.get_by_user(user_filter, limit)
        elif table_filter:
            logs = Log.get_by_table(table_filter, limit)
        else:
            logs = Log.get_all(limit)

        # Get unique values for filter dropdowns
        all_logs_sample = Log.get_all(500)  # Sample for filters
        actions = list(set([log['Action'] for log in all_logs_sample if log['Action']]))
        users = list(set([log['UserEmail'] for log in all_logs_sample if log['UserEmail']]))
        tables = list(set([log['TableName'] for log in all_logs_sample if log['TableName']]))

        return render_template('logs/list.html',
                               logs=logs,
                               actions=actions,
                               users=users,
                               tables=tables,
                               current_filters={
                                   'action': action_filter,
                                   'user': user_filter,
                                   'table': table_filter,
                                   'search': search_term,
                                   'start_date': start_date,
                                   'end_date': end_date,
                                   'limit': limit
                               })
    except Exception as e:
        logging.exception("Error listing logs")
        flash("Could not load logs.", "danger")
        # Return empty logs list instead of redirecting
        return render_template('logs/list.html',
                               logs=[],
                               actions=[],
                               users=[],
                               tables=[],
                               current_filters={
                                   'action': '',
                                   'user': '',
                                   'table': '',
                                   'search': '',
                                   'start_date': '',
                                   'end_date': '',
                                   'limit': 100
                               })


@logs_bp.route('/<int:log_id>')
@login_required
@admin_required
def view_log(log_id):
    """View detailed information about a specific log entry"""
    log_entry = Log.get_by_id(log_id)
    if not log_entry:
        flash("Log entry not found.", "warning")
        return redirect(url_for('logs.list_logs'))
    return render_template('logs/view.html', log=log_entry)


@logs_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Display log analytics dashboard"""
    try:
        # Get summary data
        activity_summary = Log.get_activity_summary()
        user_activity_summary = Log.get_user_activity_summary()

        # Get recent logs
        recent_logs = Log.get_all(20)

        # Get logs from last 24 hours
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        recent_activity = Log.get_by_date_range(yesterday, today, 100)

        return render_template('logs/dashboard.html',
                               activity_summary=activity_summary,
                               user_activity_summary=user_activity_summary,
                               recent_logs=recent_logs,
                               recent_activity=recent_activity,
                               total_recent=len(recent_activity))
    except Exception as e:
        logging.exception("Error loading log dashboard")
        flash("Could not load log dashboard.", "danger")
        return redirect(url_for('main.dashboard'))


@logs_bp.route('/export')
@login_required
@admin_required
def export_logs():
    """Export logs as JSON or CSV"""
    try:
        format_type = request.args.get('format', 'json')
        limit = int(request.args.get('limit', 1000))

        logs = Log.get_all(limit)

        if format_type == 'csv':
            import csv
            import io
            from flask import make_response

            output = io.StringIO()
            writer = csv.DictWriter(output,
                                    fieldnames=['LogID', 'UserEmail', 'Action', 'TableName', 'RecordID', 'Details',
                                                'Timestamp'])
            writer.writeheader()
            for log in logs:
                writer.writerow(log)

            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers[
                'Content-Disposition'] = f'attachment; filename=logs_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            return response
        else:
            return jsonify({
                'logs': logs,
                'exported_at': datetime.now().isoformat(),
                'total_count': len(logs)
            })

    except Exception as e:
        logging.exception("Error exporting logs")
        flash("Could not export logs.", "danger")
        return redirect(url_for('logs.list_logs'))


@logs_bp.route('/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_logs():
    """Delete old logs to maintain database performance"""
    try:
        days = int(request.form.get('days', 90))
        Log.delete_old_logs(days)
        flash(f"Successfully cleaned up logs older than {days} days.", "success")
    except Exception as e:
        logging.exception("Error cleaning up logs")
        flash("Could not clean up logs.", "danger")

    return redirect(url_for('logs.list_logs'))


@logs_bp.route('/api/recent')
@login_required
@admin_required
def api_recent_logs():
    """API endpoint for recent logs (for AJAX updates)"""
    try:
        limit = int(request.args.get('limit', 10))
        logs = Log.get_all(limit)
        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        logging.exception("Error fetching recent logs")
        return jsonify({
            'success': False,
            'error': 'Could not fetch recent logs'
        }), 500


# Helper route to manually create a test log (for development)
@logs_bp.route('/test', methods=['POST'])
@login_required
@admin_required
def create_test_log():
    """Create a test log entry (development only)"""
    try:
        from models.log import log_activity
        user_email = session.get('user_email', 'test@example.com')
        log_activity(user_email, 'TEST', 'TestTable', 123, 'This is a test log entry')
        flash("Test log created successfully.", "success")
    except Exception as e:
        logging.exception("Error creating test log")
        flash("Could not create test log.", "danger")

    return redirect(url_for('logs.list_logs'))