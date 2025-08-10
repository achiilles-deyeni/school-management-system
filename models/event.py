# models/event.py - Event model
from database import query_db, execute_db

class Event:
    @staticmethod
    def get_all():
        query = "SELECT * FROM Events ORDER BY EventDate DESC"
        return query_db(query)

    @staticmethod
    def get_by_id(event_id):
        query = "SELECT * FROM Events WHERE EventID = ?"
        results = query_db(query, (event_id,))
        return results[0] if results else None

    @staticmethod
    def create(data):
        query = '''
            INSERT INTO Events (Title, Description, EventDate, Location)
            VALUES (?, ?, ?, ?)
        '''
        execute_db(query, (
            data['Title'],
            data['Description'],
            data['EventDate'],
            data['Location']
        ))

    @staticmethod
    def update(event_id, data):
        query = '''
            UPDATE Events
            SET Title = ?, Description = ?, EventDate = ?, Location = ?
            WHERE EventID = ?
        '''
        execute_db(query, (
            data['Title'],
            data['Description'],
            data['EventDate'],
            data['Location'],
            event_id
        ))

    @staticmethod
    def delete(event_id):
        query = "DELETE FROM Events WHERE EventID = ?"
        execute_db(query, (event_id,))