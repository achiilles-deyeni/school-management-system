# routes/expenses.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.expense import Expense
from utils.decorators import login_required, admin_required

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/')
@login_required
def list_expenses():
    expenses = Expense.get_all()
    return render_template('expenses/list.html', expenses=expenses)

@expenses_bp.route('/<int:expense_id>')
@login_required
def view_expense(expense_id):
    expense = Expense.get_by_id(expense_id)
    if not expense:
        flash('Expense not found', 'danger')
        return redirect(url_for('expenses.list_expenses'))
    return render_template('expenses/view.html', expense=expense)

@expenses_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_expense():
    if request.method == 'POST':
        data = {
            'Title': request.form['Title'],
            'Amount': request.form['Amount'],
            'ExpenseDate': request.form['ExpenseDate'],
            'Category': request.form['Category'],
            'Notes': request.form['Notes']
        }
        Expense.create(data)
        flash('Expense recorded successfully', 'success')
        return redirect(url_for('expenses.list_expenses'))
    return render_template('expenses/create.html')

@expenses_bp.route('/<int:expense_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_expense(expense_id):
    expense = Expense.get_by_id(expense_id)
    if not expense:
        flash('Expense not found', 'danger')
        return redirect(url_for('expenses.list_expenses'))
    if request.method == 'POST':
        data = {
            'Title': request.form['Title'],
            'Amount': request.form['Amount'],
            'ExpenseDate': request.form['ExpenseDate'],
            'Category': request.form['Category'],
            'Notes': request.form['Notes']
        }
        Expense.update(expense_id, data)
        flash('Expense updated successfully', 'success')
        return redirect(url_for('expenses.view_expense', expense_id=expense_id))
    return render_template('expenses/edit.html', expense=expense)

@expenses_bp.route('/<int:expense_id>/delete', methods=['POST'])
@admin_required
def delete_expense(expense_id):
    Expense.delete(expense_id)
    flash('Expense deleted', 'info')
    return redirect(url_for('expenses.list_expenses'))
