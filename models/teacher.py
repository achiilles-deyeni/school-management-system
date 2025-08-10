# models/teacher.py - Teacher model
from database import query_db, execute_db
from werkzeug.security import check_password_hash


class Teacher:
    @staticmethod
    def get_all():
        query = '''
            SELECT t.LastName, t.FirstName, t.Subjects_taught, t.Email, 
                   t.PhoneNumber, t.TeacherID, COUNT(s.StudentID) as StudentCount
            FROM Teachers_114 t
            LEFT JOIN Students_114 s ON t.TeacherID = s.TeacherID
            GROUP BY t.TeacherID, t.FirstName, t.LastName, t.Subjects_taught, t.Email, t.PhoneNumber
            ORDER BY t.LastName, t.FirstName
        '''
        return query_db(query)

    @staticmethod
    def get_by_id(teacher_id):
        query = "SELECT * FROM Teachers_114 WHERE TeacherID = ?"
        results = query_db(query, (teacher_id,))
        return results[0] if results else None

    @staticmethod
    def authenticate(email, password):
        """Authenticate teacher login with proper password hashing"""
        query = '''
            SELECT TeacherID, Email, FirstName, LastName, password
            FROM Teachers_114
            WHERE Email = ?
        '''
        results = query_db(query, (email,))
        if results:
            teacher = results[0]
            # Check if password is hashed (starts with hash methods) or plain text
            stored_password = teacher['password']
            if stored_password.startswith(('pbkdf2:', 'scrypt:', 'argon2:')):
                # Password is hashed, use proper verification
                if check_password_hash(stored_password, password):
                    return teacher
            else:
                # Password is in plain text (legacy), do direct comparison
                # This should be updated to use hashed passwords in production
                if stored_password == password:
                    return teacher
        return None
