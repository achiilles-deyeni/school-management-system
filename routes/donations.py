# routes/donations.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.donation import Donation
from utils.decorators import login_required, admin_required

donations_bp = Blueprint('donations', __name__, url_prefix='/donations')

@donations_bp.route('/')
@login_required
def list_donations():
    donations = Donation.get_all()
    return render_template('donations/list.html', donations=donations)

@donations_bp.route('/<int:donation_id>')
@login_required
def view_donation(donation_id):
    donation = Donation.get_by_id(donation_id)
    if not donation:
        flash('Donation not found', 'danger')
        return redirect(url_for('donations.list_donations'))
    return render_template('donations/view.html', donation=donation)

@donations_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_donation():
    if request.method == 'POST':
        data = {
            'DonorName': request.form['DonorName'],
            'Amount': request.form['Amount'],
            'DonationDate': request.form['DonationDate'],
            'Notes': request.form['Notes']
        }
        Donation.create(data)
        flash('Donation recorded successfully', 'success')
        return redirect(url_for('donations.list_donations'))
    return render_template('donations/create.html')

@donations_bp.route('/<int:donation_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_donation(donation_id):
    donation = Donation.get_by_id(donation_id)
    if not donation:
        flash('Donation not found', 'danger')
        return redirect(url_for('donations.list_donations'))
    if request.method == 'POST':
        data = {
            'DonorName': request.form['DonorName'],
            'Amount': request.form['Amount'],
            'DonationDate': request.form['DonationDate'],
            'Notes': request.form['Notes']
        }
        Donation.update(donation_id, data)
        flash('Donation updated successfully', 'success')
        return redirect(url_for('donations.view_donation', donation_id=donation_id))
    return render_template('donations/edit.html', donation=donation)

@donations_bp.route('/<int:donation_id>/delete', methods=['POST'])
@admin_required
def delete_donation(donation_id):
    Donation.delete(donation_id)
    flash('Donation deleted', 'info')
    return redirect(url_for('donations.list_donations'))