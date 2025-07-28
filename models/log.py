# models/log.py - Log model
from database import query_db, execute_db
from datetime import datetime

class Log:
    @staticmethod
    def get_all(limit=100):
        """Get all logs with optional limit, ordered by most recent first"""
        query = "SELECT * FROM Logs_114 ORDER BY Timestamp DESC LIMIT ?"
        return query_db(query, (limit,))

    @staticmethod
    def get_by_id(log_id):
        """Get a specific log entry by ID"""
        query = "SELECT * FROM Logs_114 WHERE LogID = ?"
        results = query_db(query, (log_id,))
        return results[0] if results else None

    @staticmethod
    def get_by_user(user_email, limit=50):
        """Get logs for a specific user"""
        query = "SELECT * FROM Logs_114 WHERE UserEmail = ? ORDER BY Timestamp DESC LIMIT ?"
        return query_db(query, (user_email, limit))

    @staticmethod
    def get_by_action(action, limit=50):
        """Get logs for a specific action type"""
        query = "SELECT * FROM Logs_114 WHERE Action = ? ORDER BY Timestamp DESC LIMIT ?"
        return query_db(query, (action, limit))

    @staticmethod
    def get_by_table(table_name, limit=50):
        """Get logs for a specific table"""
        query = "SELECT * FROM Logs_114 WHERE TableName = ? ORDER BY Timestamp DESC LIMIT ?"
        return query_db(query, (table_name, limit))

    @staticmethod
    def get_by_date_range(start_date, end_date, limit=100):
        """Get logs within a date range"""
        query = """
            SELECT * FROM Logs_114 
            WHERE DATE(Timestamp) BETWEEN ? AND ? 
            ORDER BY Timestamp DESC LIMIT ?
        """
        return query_db(query, (start_date, end_date, limit))

    @staticmethod
    def create(user_email, action, table_name, record_id=None, details=None):
        """Create a new log entry"""
        query = '''
            INSERT INTO Logs_114 (UserEmail, Action, TableName, RecordID, Details, Timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        execute_db(query, (
            user_email,
            action,
            table_name,
            record_id,
            details,
            timestamp
        ))

    @staticmethod
    def delete_old_logs(days=90):
        """Delete logs older than specified days"""
        query = "DELETE FROM Logs_114 WHERE Timestamp < datetime('now', '-' || ? || ' days')"
        execute_db(query, (days,))

    @staticmethod
    def get_activity_summary():
        """Get summary of activities by action type"""
        query = """
            SELECT Action, COUNT(*) as Count, MAX(Timestamp) as LastActivity
            FROM Logs_114 
            GROUP BY Action 
            ORDER BY Count DESC
        """
        return query_db(query)

    @staticmethod
    def get_user_activity_summary():
        """Get summary of activities by user"""
        query = """
            SELECT UserEmail, COUNT(*) as Count, MAX(Timestamp) as LastActivity
            FROM Logs_114 
            GROUP BY UserEmail 
            ORDER BY Count DESC
        """
        return query_db(query)

    @staticmethod
    def search_logs(search_term, limit=50):
        """Search logs by details or user email"""
        query = """
            SELECT * FROM Logs_114 
            WHERE Details LIKE ? OR UserEmail LIKE ? 
            ORDER BY Timestamp DESC LIMIT ?
        """
        search_pattern = f"%{search_term}%"
        return query_db(query, (search_pattern, search_pattern, limit))

# Helper function to log system activities
def log_activity(user_email, action, table_name, record_id=None, details=None):
    """Convenience function to log activities"""
    try:
        Log.create(user_email, action, table_name, record_id, details)
    except Exception as e:
        # Log to system logger if database logging fails
        import logging
        logging.error(f"Failed to log activity: {e}")