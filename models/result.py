# models/result.py
from database import query_db, execute_db

class Result:
    @staticmethod
    def get_all():
        query = '''
            SELECT * FROM Results_114 ORDER BY AcademicYear DESC, Term
        '''
        return query_db(query)

    @staticmethod
    def get_by_id(result_id):
        query = "SELECT * FROM Results_114 WHERE ResultID = ?"
        results = query_db(query, (result_id,))
        return results[0] if results else None

    @staticmethod
    def get_by_student(student_id):
        query = '''
            SELECT * FROM Results_114
            WHERE StudentID = ?
            ORDER BY AcademicYear DESC, Term
        '''
        return query_db(query, (student_id,))

    @staticmethod
    def create(data):
        query = '''
            INSERT INTO Results_114 (StudentID, AcademicYear, Term, Subject, Score, Grade, Remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            data['StudentID'],
            data['AcademicYear'],
            data['Term'],
            data['Subject'],
            data['Score'],
            data['Grade'],
            data['Remarks']
        )
        return execute_db(query, params)

    @staticmethod
    def update(result_id, data):
        query = '''
            UPDATE Results_114
            SET AcademicYear = ?, Term = ?, Subject = ?, Score = ?, Grade = ?, Remarks = ?
            WHERE ResultID = ?
        '''
        params = (
            data['AcademicYear'],
            data['Term'],
            data['Subject'],
            data['Score'],
            data['Grade'],
            data['Remarks'],
            result_id
        )
        return execute_db(query, params)

    @staticmethod
    def delete(result_id):
        query = "DELETE FROM Results_114 WHERE ResultID = ?"
        return execute_db(query, (result_id,))