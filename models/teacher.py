# models/teacher.py - Teacher model
from database import query_db, execute_db


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
        query = '''
            SELECT TeacherID, Email, FirstName, LastName
            FROM Teachers_114
            WHERE Email = ? AND password = ?
        '''
        results = query_db(query, (email, password))
        return results[0] if results else None
