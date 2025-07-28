# routes/results.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.result import Result
from models.student import Student
from utils.decorators import login_required, teacher_required, admin_required

results_bp = Blueprint('results', __name__, url_prefix='/results')

@results_bp.route('/')
@login_required
def list_results():
    results = Result.get_all()
    return render_template('results/list.html', results=results)

@results_bp.route('/student/<int:student_id>')
@login_required
def view_student_results(student_id):
    student = Student.get_by_id(student_id)
    results = Result.get_by_student(student_id)
    return render_template('results/student_results.html', student=student, results=results)

@results_bp.route('/<int:result_id>')
@login_required
def view_result(result_id):
    result = Result.get_by_id(result_id)
    return render_template('results/view.html', result=result)

@results_bp.route('/create', methods=['GET', 'POST'])
@teacher_required
def create_result():
    if request.method == 'POST':
        data = {
            'StudentID': request.form['StudentID'],
            'AcademicYear': request.form['AcademicYear'],
            'Term': request.form['Term'],
            'Subject': request.form['Subject'],
            'Score': request.form['Score'],
            'Grade': request.form['Grade'],
            'Remarks': request.form['Remarks']
        }
        Result.create(data)
        flash('Result added successfully', 'success')
        return redirect(url_for('results.list_results'))
    students = Student.get_all()
    return render_template('results/create.html', students=students)

@results_bp.route('/<int:result_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_result(result_id):
    result = Result.get_by_id(result_id)
    if not result:
        flash('Result not found', 'danger')
        return redirect(url_for('results.list_results'))
    if request.method == 'POST':
        data = {
            'AcademicYear': request.form['AcademicYear'],
            'Term': request.form['Term'],
            'Subject': request.form['Subject'],
            'Score': request.form['Score'],
            'Grade': request.form['Grade'],
            'Remarks': request.form['Remarks']
        }
        Result.update(result_id, data)
        flash('Result updated successfully', 'success')
        return redirect(url_for('results.view_result', result_id=result_id))
    return render_template('results/edit.html', result=result)

@results_bp.route('/<int:result_id>/delete', methods=['POST'])
@admin_required
def delete_result(result_id):
    Result.delete(result_id)
    flash('Result deleted', 'info')
    return redirect(url_for('results.list_results'))

@results_bp.route('/student/<int:student_id>/print')
@login_required
def print_results(student_id):
    student = Student.get_by_id(student_id)
    results = Result.get_by_student(student_id)
    return render_template('results/print.html', student=student, results=results, layout='printable')
