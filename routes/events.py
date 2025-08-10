# routes/event.py - Event routes
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.event import Event
from utils.decorators import login_required, admin_required
from utils.validators import validate_event_data
import logging

events_bp = Blueprint('events', __name__)

@events_bp.route('/')
@login_required
def list_events():
    try:
        events = Event.get_all()
        return render_template('events/list.html', events=events)
    except Exception as e:
        logging.exception("Error listing events")
        # More specific error message for debugging
        error_msg = f"Could not load events. Error: {str(e)}"
        flash(error_msg, "danger")
        # Return empty events list instead of redirecting
        return render_template('events/list.html', events=[])

@events_bp.route('/<int:event_id>')
@login_required
def view_event(event_id):
    event = Event.get_by_id(event_id)
    if not event:
        flash("Event not found.", "warning")
        return redirect(url_for('events.list_events'))
    return render_template('events/view.html', event=event)

@events_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_event():
    if request.method == 'POST':
        data = request.form.to_dict()
        errors = validate_event_data(data)

        if errors:
            flash(f"Validation errors: {errors}", 'danger')
            return redirect(url_for('events.create_event'))

        Event.create(data)
        flash("Event created successfully.", "success")
        return redirect(url_for('events.list_events'))

    return render_template('events/create.html')

@events_bp.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_event(event_id):
    event = Event.get_by_id(event_id)
    if not event:
        flash("Event not found.", "warning")
        return redirect(url_for('events.list_events'))

    if request.method == 'POST':
        data = request.form.to_dict()
        errors = validate_event_data(data)

        if errors:
            flash(f"Validation errors: {errors}", 'danger')
            return redirect(url_for('events.edit_event', event_id=event_id))

        Event.update(event_id, data)
        flash("Event updated successfully.", "success")
        return redirect(url_for('events.view_event', event_id=event_id))

    return render_template('events/edit.html', event=event)

@events_bp.route('/delete/<int:event_id>', methods=['POST'])
@login_required
@admin_required
def delete_event(event_id):
    Event.delete(event_id)
    flash("Event deleted.", "info")
    return redirect(url_for('events.list_events'))
