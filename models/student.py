# models/student.py - Enhanced Student Model
from database import query_db, execute_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import csv
import io
import logging
import re
import uuid

logger = logging.getLogger(__name__)


class Student:
    """Student model for managing student data and operations"""

    @staticmethod
    def create(data):
        """Create a new student record"""
        try:
            # Generate unique student ID
            student_id = Student._generate_student_id()

            # Generate default password (can be changed later)
            default_password = generate_password_hash(f"{data['last_name'].lower()}{student_id[-4:]}")

            query = '''
                INSERT INTO Students_114 (
                    StudentID, FirstName, LastName, Gender, DateOfBirth,
                    GuardianName, GuardianPhone, GuardianEmail, Address,
                    Class, AdmissionDate, TeacherID, MedicalInfo,
                    EmergencyContact, EmergencyPhone, Photo, Password,
                    Status, CreatedAt, UpdatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''

            params = (
                student_id,
                data['first_name'],
                data['last_name'],
                data['gender'],
                data['date_of_birth'],
                data['guardian_name'],
                data['guardian_phone'],
                data.get('guardian_email', ''),
                data.get('address', ''),
                data['class_name'],
                data.get('admission_date', datetime.now().date()),
                data.get('teacher_id'),
                data.get('medical_info', ''),
                data.get('emergency_contact', ''),
                data.get('emergency_phone', ''),
                data.get('photo'),
                default_password,
                'active',
                datetime.now(),
                datetime.now()
            )

            result = execute_db(query, params)
            logger.info(f"Student created with ID: {student_id}")
            return result

        except Exception as e:
            logger.error(f"Error creating student: {str(e)}")
            raise Exception(f"Failed to create student: {str(e)}")

    @staticmethod
    def get_all():
        """Get all active students"""
        try:
            query = '''
                SELECT 
                    s.ID, s.StudentID, s.FirstName, s.LastName, s.Gender,
                    s.DateOfBirth, s.Class, s.GuardianName, s.GuardianPhone,
                    s.GuardianEmail, s.Address, s.AdmissionDate, s.Status,
                    s.Photo, t.FirstName + ' ' + t.LastName AS TeacherName
                FROM Students_114 s
                LEFT JOIN Teachers_114 t ON s.TeacherID = t.ID
                WHERE s.Status = 'active'
                ORDER BY s.LastName, s.FirstName
            '''

            results = query_db(query)
            return [Student._row_to_dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting all students: {str(e)}")
            raise Exception("Failed to retrieve students")

    @staticmethod
    def get_paginated(page=1, per_page=20, search='', class_filter='',
                      gender_filter='', sort_by='last_name', sort_order='asc'):
        """Get paginated students with filtering and sorting"""
        try:
            # Build WHERE clause
            where_conditions = ["s.Status = 'active'"]
            params = []

            if search:
                where_conditions.append('''(
                    s.FirstName LIKE ? OR s.LastName LIKE ? OR 
                    s.StudentID LIKE ? OR s.GuardianName LIKE ?
                )''')
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param, search_param])

            if class_filter:
                where_conditions.append("s.Class = ?")
                params.append(class_filter)

            if gender_filter:
                where_conditions.append("s.Gender = ?")
                params.append(gender_filter)

            where_clause = " AND ".join(where_conditions)

            # Validate sort parameters
            valid_sort_columns = ['first_name', 'last_name', 'student_id', 'class', 'admission_date']
            if sort_by not in valid_sort_columns:
                sort_by = 'last_name'

            if sort_order.lower() not in ['asc', 'desc']:
                sort_order = 'asc'

            # Map sort_by to actual column names
            sort_column_map = {
                'first_name': 's.FirstName',
                'last_name': 's.LastName',
                'student_id': 's.StudentID',
                'class': 's.Class',
                'admission_date': 's.AdmissionDate'
            }

            order_clause = f"ORDER BY {sort_column_map[sort_by]} {sort_order.upper()}"

            # Get total count
            count_query = f'''
                SELECT COUNT(*) 
                FROM Students_114 s
                LEFT JOIN Teachers_114 t ON s.TeacherID = t.ID
                WHERE {where_clause}
            '''

            total_count = query_db(count_query, params)[0][0]

            # Calculate pagination
            offset = (page - 1) * per_page
            total_pages = (total_count + per_page - 1) // per_page

            # Get paginated results
            query = f'''
                SELECT 
                    s.ID, s.StudentID, s.FirstName, s.LastName, s.Gender,
                    s.DateOfBirth, s.Class, s.GuardianName, s.GuardianPhone,
                    s.GuardianEmail, s.Address, s.AdmissionDate, s.Status,
                    s.Photo, t.FirstName + ' ' + t.LastName AS TeacherName
                FROM Students_114 s
                LEFT JOIN Teachers_114 t ON s.TeacherID = t.ID
                WHERE {where_clause}
                {order_clause}
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            '''

            params.extend([offset, per_page])
            results = query_db(query, params)

            students = [Student._row_to_dict(row) for row in results]

            pagination = {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages,
                'prev_num': page - 1 if page > 1 else None,
                'next_num': page + 1 if page < total_pages else None
            }

            return {'students': students, 'pagination': pagination}

        except Exception as e:
            logger.error(f"Error getting paginated students: {str(e)}")
            raise Exception("Failed to retrieve paginated students")

    @staticmethod
    def get_by_id(student_id):
        """Get student by internal ID"""
        try:
            query = '''
                SELECT 
                    s.ID, s.StudentID, s.FirstName, s.LastName, s.Gender,
                    s.DateOfBirth, s.Class, s.GuardianName, s.GuardianPhone,
                    s.GuardianEmail, s.Address, s.AdmissionDate, s.TeacherID,
                    s.MedicalInfo, s.EmergencyContact, s.EmergencyPhone,
                    s.Photo, s.Status, s.CreatedAt, s.UpdatedAt,
                    t.FirstName + ' ' + t.LastName AS TeacherName
                FROM Students_114 s
                LEFT JOIN Teachers_114 t ON s.TeacherID = t.ID
                WHERE s.ID = ?
            '''

            result = query_db(query, (student_id,))
            return Student._row_to_dict(result[0]) if result else None

        except Exception as e:
            logger.error(f"Error getting student by ID {student_id}: {str(e)}")
            return None

    @staticmethod
    def get_by_student_id(student_id):
        """Get student by StudentID (login ID)"""
        try:
            query = '''
                SELECT 
                    s.ID, s.StudentID, s.FirstName, s.LastName, s.Gender,
                    s.DateOfBirth, s.Class, s.GuardianName, s.GuardianPhone,
                    s.GuardianEmail, s.Address, s.AdmissionDate, s.TeacherID,
                    s.MedicalInfo, s.EmergencyContact, s.EmergencyPhone,
                    s.Photo, s.Status, s.CreatedAt, s.UpdatedAt,
                    t.FirstName + ' ' + t.LastName AS TeacherName
                FROM Students_114 s
                LEFT JOIN Teachers_114 t ON s.TeacherID = t.ID
                WHERE s.StudentID = ? AND s.Status = 'active'
            '''

            result = query_db(query, (student_id,))
            return Student._row_to_dict(result[0]) if result else None

        except Exception as e:
            logger.error(f"Error getting student by StudentID {student_id}: {str(e)}")
            return None

    @staticmethod
    def update(student_id, data):
        """Update student information"""
        try:
            # Build dynamic update query
            update_fields = []
            params = []

            field_mapping = {
                'first_name': 'FirstName',
                'last_name': 'LastName',
                'gender': 'Gender',
                'date_of_birth': 'DateOfBirth',
                'guardian_name': 'GuardianName',
                'guardian_phone': 'GuardianPhone',
                'guardian_email': 'GuardianEmail',
                'address': 'Address',
                'class_name': 'Class',
                'teacher_id': 'TeacherID',
                'medical_info': 'MedicalInfo',
                'emergency_contact': 'EmergencyContact',
                'emergency_phone': 'EmergencyPhone',
                'photo': 'Photo',
                'status': 'Status'
            }

            for key, value in data.items():
                if key in field_mapping and value is not None:
                    update_fields.append(f"{field_mapping[key]} = ?")
                    params.append(value)

            if not update_fields:
                return True

            # Add UpdatedAt
            update_fields.append("UpdatedAt = ?")
            params.append(datetime.now())

            # Add WHERE clause parameter
            params.append(student_id)

            query = f'''
                UPDATE Students_114 
                SET {', '.join(update_fields)}
                WHERE ID = ?
            '''

            execute_db(query, params)
            logger.info(f"Student {student_id} updated")
            return True

        except Exception as e:
            logger.error(f"Error updating student {student_id}: {str(e)}")
            raise Exception(f"Failed to update student: {str(e)}")

    @staticmethod
    def soft_delete(student_id):
        """Soft delete student (mark as inactive)"""
        try:
            query = '''
                UPDATE Students_114 
                SET Status = 'inactive', UpdatedAt = ?
                WHERE ID = ?
            '''

            execute_db(query, (datetime.now(), student_id))
            logger.info(f"Student {student_id} soft deleted")
            return True

        except Exception as e:
            logger.error(f"Error soft deleting student {student_id}: {str(e)}")
            raise Exception("Failed to deactivate student")

    @staticmethod
    def authenticate(student_id, password):
        """Authenticate student login"""
        try:
            query = '''
                SELECT ID, StudentID, FirstName, LastName, Password, Status
                FROM Students_114 
                WHERE StudentID = ? AND Status = 'active'
            '''

            result = query_db(query, (student_id,))
            if result and check_password_hash(result[0][4], password):
                return {
                    'id': result[0][0],
                    'student_id': result[0][1],
                    'first_name': result[0][2],
                    'last_name': result[0][3]
                }
            return None

        except Exception as e:
            logger.error(f"Error authenticating student {student_id}: {str(e)}")
            return None

    @staticmethod
    def change_password(student_id, current_password, new_password):
        """Change student password"""
        try:
            # Verify current password
            query = "SELECT Password FROM Students_114 WHERE StudentID = ?"
            result = query_db(query, (student_id,))

            if not result or not check_password_hash(result[0][0], current_password):
                return False

            # Update password
            new_hash = generate_password_hash(new_password)
            update_query = '''
                UPDATE Students_114 
                SET Password = ?, UpdatedAt = ?
                WHERE StudentID = ?
            '''

            execute_db(update_query, (new_hash, datetime.now(), student_id))
            logger.info(f"Password changed for student: {student_id}")
            return True

        except Exception as e:
            logger.error(f"Error changing password for student {student_id}: {str(e)}")
            return False

    @staticmethod
    def get_all_classes():
        """Get list of all classes"""
        try:
            query = '''
                SELECT DISTINCT Class 
                FROM Students_114 
                WHERE Status = 'active' AND Class IS NOT NULL
                ORDER BY Class
            '''

            results = query_db(query)
            return [row[0] for row in results]

        except Exception as e:
            logger.error(f"Error getting classes: {str(e)}")
            return []

    @staticmethod
    def search(query_text, limit=10):
        """Search students by name, ID, or class"""
        try:
            query = '''
                SELECT 
                    ID, StudentID, FirstName, LastName, Class, Photo
                FROM Students_114
                WHERE Status = 'active' AND (
                    FirstName LIKE ? OR LastName LIKE ? OR 
                    StudentID LIKE ? OR Class LIKE ?
                )
                ORDER BY LastName, FirstName
                LIMIT ?
            '''

            search_param = f"%{query_text}%"
            results = query_db(query, (search_param, search_param, search_param, search_param, limit))

            return [{
                'id': row[0],
                'student_id': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'class_name': row[4],
                'photo': row[5]
            } for row in results]

        except Exception as e:
            logger.error(f"Error searching students: {str(e)}")
            return []

    @staticmethod
    def get_academic_history(student_id):
        """Get student's academic history"""
        try:
            query = '''
                SELECT 
                    r.Term, r.Year, r.Subject, r.Score, r.Grade,
                    r.Position, r.Remarks, r.CreatedAt
                FROM Results_114 r
                WHERE r.StudentID = (SELECT StudentID FROM Students_114 WHERE ID = ?)
                ORDER BY r.Year DESC, r.Term DESC, r.Subject
            '''

            results = query_db(query, (student_id,))
            return [{
                'term': row[0],
                'year': row[1],
                'subject': row[2],
                'score': row[3],
                'grade': row[4],
                'position': row[5],
                'remarks': row[6],
                'date': row[7]
            } for row in results]

        except Exception as e:
            logger.error(f"Error getting academic history for student {student_id}: {str(e)}")
            return []

    @staticmethod
    def get_attendance_summary(student_id):
        """Get student's attendance summary"""
        try:
            query = '''
                SELECT 
                    COUNT(*) as total_days,
                    SUM(CASE WHEN Status = 'present' THEN 1 ELSE 0 END) as present_days,
                    SUM(CASE WHEN Status = 'absent' THEN 1 ELSE 0 END) as absent_days,
                    SUM(CASE WHEN Status = 'late' THEN 1 ELSE 0 END) as late_days
                FROM Attendance_114
                WHERE StudentID = (SELECT StudentID FROM Students_114 WHERE ID = ?)
                AND YEAR(Date) = YEAR(GETDATE())
            '''

            result = query_db(query, (student_id,))
            if result:
                row = result[0]
                total = row[0] or 0
                present = row[1] or 0
                absent = row[2] or 0
                late = row[3] or 0

                attendance_rate = (present / total * 100) if total > 0 else 0

                return {
                    'total_days': total,
                    'present_days': present,
                    'absent_days': absent,
                    'late_days': late,
                    'attendance_rate': round(attendance_rate, 2)
                }

            return {
                'total_days': 0,
                'present_days': 0,
                'absent_days': 0,
                'late_days': 0,
                'attendance_rate': 0
            }

        except Exception as e:
            logger.error(f"Error getting attendance summary for student {student_id}: {str(e)}")
            return {}

    @staticmethod
    def get_current_term_results(student_id):
        """Get current term results for student"""
        try:
            query = '''
                SELECT 
                    r.Subject, r.Score, r.Grade, r.Position, r.Remarks
                FROM Results_114 r
                WHERE r.StudentID = ? 
                AND r.Year = YEAR(GETDATE())
                AND r.Term = (
                    SELECT MAX(Term) FROM Results_114 
                    WHERE StudentID = ? AND Year = YEAR(GETDATE())
                )
                ORDER BY r.Subject
            '''

            results = query_db(query, (student_id, student_id))
            return [{
                'subject': row[0],
                'score': row[1],
                'grade': row[2],
                'position': row[3],
                'remarks': row[4]
            } for row in results]

        except Exception as e:
            logger.error(f"Error getting current term results for student {student_id}: {str(e)}")
            return []

    @staticmethod
    def get_upcoming_events(student_id):
        """Get upcoming events for student"""
        try:
            query = '''
                SELECT 
                    e.Title, e.Description, e.Date, e.Location, e.Type
                FROM Events_114 e
                WHERE e.Date >= GETDATE()
                AND (e.TargetAudience = 'all' OR e.TargetAudience = 'students'
                     OR e.TargetClass = (SELECT Class FROM Students_114 WHERE ID = ?))
                ORDER BY e.Date
                LIMIT 5
            '''

            results = query_db(query, (student_id,))
            return [{
                'title': row[0],
                'description': row[1],
                'date': row[2],
                'location': row[3],
                'type': row[4]
            } for row in results]

        except Exception as e:
            logger.error(f"Error getting upcoming events for student {student_id}: {str(e)}")
            return []

    @staticmethod
    def update_status(student_id, status):
        """Update student status"""
        try:
            query = '''
                UPDATE Students_114 
                SET Status = ?, UpdatedAt = ?
                WHERE ID = ?
            '''

            execute_db(query, (status, datetime.now(), student_id))
            logger.info(f"Student {student_id} status updated to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating status for student {student_id}: {str(e)}")
            return False

    @staticmethod
    def get_for_export(class_filter='', gender_filter='', status_filter='active'):
        """Get students for export"""
        try:
            where_conditions = []
            params = []

            if status_filter:
                where_conditions.append("Status = ?")
                params.append(status_filter)

            if class_filter:
                where_conditions.append("Class = ?")
                params.append(class_filter)

            if gender_filter:
                where_conditions.append("Gender = ?")
                params.append(gender_filter)

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            query = f'''
                SELECT 
                    StudentID, FirstName, LastName, Gender, DateOfBirth,
                    Class, GuardianName, GuardianPhone, GuardianEmail,
                    Address, AdmissionDate, Status
                FROM Students_114
                WHERE {where_clause}
                ORDER BY LastName, FirstName
            '''

            results = query_db(query, params)
            return [{
                'student_id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'gender': row[3],
                'date_of_birth': row[4],
                'class_name': row[5],
                'guardian_name': row[6],
                'guardian_phone': row[7],
                'guardian_email': row[8],
                'address': row[9],
                'admission_date': row[10],
                'status': row[11]
            } for row in results]

        except Exception as e:
            logger.error(f"Error getting students for export: {str(e)}")
            return []

    @staticmethod
    def bulk_import_from_csv(file):
        """Bulk import students from CSV file"""
        try:
            # Read CSV content
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            reader = csv.DictReader(stream)

            imported = 0
            errors = 0
            error_details = []

            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                try:
                    # Validate required fields
                    required_fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'class_name']
                    missing_fields = [field for field in required_fields if not row.get(field, '').strip()]

                    if missing_fields:
                        error_details.append({
                            'row': row_num,
                            'message': f"Missing required fields: {', '.join(missing_fields)}"
                        })
                        errors += 1
                        continue

                    # Prepare student data
                    student_data = {
                        'first_name': row['first_name'].strip(),
                        'last_name': row['last_name'].strip(),
                        'gender': row['gender'].strip(),
                        'date_of_birth': row['date_of_birth'].strip(),
                        'guardian_name': row.get('guardian_name', '').strip(),
                        'guardian_phone': row.get('guardian_phone', '').strip(),
                        'guardian_email': row.get('guardian_email', '').strip(),
                        'address': row.get('address', '').strip(),
                        'class_name': row['class_name'].strip(),
                        'admission_date': row.get('admission_date', datetime.now().date()),
                        'teacher_id': row.get('teacher_id') or None,
                        'medical_info': row.get('medical_info', '').strip(),
                        'emergency_contact': row.get('emergency_contact', '').strip(),
                        'emergency_phone': row.get('emergency_phone', '').strip()
                    }

                    # Create student
                    Student.create(student_data)
                    imported += 1

                except Exception as e:
                    error_details.append({
                        'row': row_num,
                        'message': str(e)
                    })
                    errors += 1

            return {
                'success': True,
                'imported': imported,
                'errors': errors,
                'error_details': error_details
            }

        except Exception as e:
            logger.error(f"Error in bulk import: {str(e)}")
            return {
                'success': False,
                'imported': 0,
                'errors': 0,
                'error_details': []
            }

    @staticmethod
    def _generate_student_id():
        """Generate unique student ID"""
        try:
            # Get current year
            year = datetime.now().year
            year_suffix = str(year)[-2:]  # Last 2 digits of year

            # Get count of students for this year
            query = '''
                SELECT COUNT(*) FROM Students_114 
                WHERE StudentID LIKE ?
            '''

            pattern = f"STU{year_suffix}%"
            result = query_db(query, (pattern,))
            count = result[0][0] + 1

            # Generate ID: STU + YY + 4-digit sequence
            student_id = f"STU{year_suffix}{count:04d}"

            # Ensure uniqueness
            while Student._student_id_exists(student_id):
                count += 1
                student_id = f"STU{year_suffix}{count:04d}"

            return student_id

        except Exception as e:
            logger.error(f"Error generating student ID: {str(e)}")
            # Fallback to UUID-based ID
            return f"STU{str(uuid.uuid4())[:8].upper()}"

    @staticmethod
    def _student_id_exists(student_id):
        """Check if student ID already exists"""
        try:
            query = "SELECT COUNT(*) FROM Students_114 WHERE StudentID = ?"
            result = query_db(query, (student_id,))
            return result[0][0] > 0
        except:
            return False

    @staticmethod
    def _row_to_dict(row):
        """Convert database row to dictionary"""
        if not row:
            return None

        return {
            'id': row[0],
            'student_id': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'gender': row[4],
            'date_of_birth': row[5],
            'class_name': row[6],
            'guardian_name': row[7],
            'guardian_phone': row[8],
            'guardian_email': row[9] if len(row) > 9 else '',
            'address': row[10] if len(row) > 10 else '',
            'admission_date': row[11] if len(row) > 11 else '',
            'teacher_id': row[12] if len(row) > 12 else None,
            'medical_info': row[13] if len(row) > 13 else '',
            'emergency_contact': row[14] if len(row) > 14 else '',
            'emergency_phone': row[15] if len(row) > 15 else '',
            'photo': row[16] if len(row) > 16 else None,
            'status': row[17] if len(row) > 17 else 'active',
            'created_at': row[18] if len(row) > 18 else None,
            'updated_at': row[19] if len(row) > 19 else None,
            'teacher_name': row[20] if len(row) > 20 else None
        }