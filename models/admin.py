# models/admin.py - Admin model for MSSQL
from database import query_db, execute_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class Admin:
    @staticmethod
    def get_all():
        """Get all admin records"""
        query = "SELECT * FROM Admins_114 WHERE IsActive = 1 ORDER BY CreatedAt DESC"
        return query_db(query)

    @staticmethod
    def get_by_id(admin_id):
        """Get admin by ID"""
        query = "SELECT * FROM Admins_114 WHERE AdminID = ? AND IsActive = 1"
        results = query_db(query, (admin_id,))
        return results[0] if results else None

    @staticmethod
    def get_by_email(email):
        """Get admin by email"""
        query = "SELECT * FROM Admins_114 WHERE Email = ? AND IsActive = 1"
        results = query_db(query, (email,))
        return results[0] if results else None

    @staticmethod
    def email_exists(email):
        """Check if email already exists"""
        query = "SELECT COUNT(*) as count FROM Admins_114 WHERE Email = ?"
        result = query_db(query, (email,))
        return result[0]['count'] > 0 if result else False

    @staticmethod
    def create(data):
        """Create a new admin"""
        # Hash the password
        hashed_password = generate_password_hash(data['Password'])

        query = '''
            INSERT INTO Admins_114 (FirstName, LastName, Email, Password, CreatedAt, UpdatedAt)
            VALUES (?, ?, ?, ?, GETDATE(), GETDATE())
        '''
        execute_db(query, (
            data['FirstName'],
            data['LastName'],
            data['Email'],
            hashed_password
        ))

    @staticmethod
    def update(admin_id, data):
        """Update admin information"""
        # If password is being updated, hash it
        if 'Password' in data:
            data['Password'] = generate_password_hash(data['Password'])

        # Build dynamic update query
        fields = []
        values = []
        for key, value in data.items():
            if key != 'AdminID':  # Don't update the ID
                fields.append(f"{key} = ?")
                values.append(value)

        # Add UpdatedAt timestamp
        fields.append("UpdatedAt = GETDATE()")
        values.append(admin_id)  # For WHERE clause

        query = f"UPDATE Admins_114 SET {', '.join(fields)} WHERE AdminID = ?"
        execute_db(query, values)

    @staticmethod
    def delete(admin_id):
        """Soft delete admin (set IsActive to 0)"""
        query = "UPDATE Admins_114 SET IsActive = 0, UpdatedAt = GETDATE() WHERE AdminID = ?"
        execute_db(query, (admin_id,))

    @staticmethod
    def hard_delete(admin_id):
        """Permanently delete admin"""
        query = "DELETE FROM Admins_114 WHERE AdminID = ?"
        execute_db(query, (admin_id,))

    @staticmethod
    def authenticate(email, password):
        """Authenticate admin login"""
        admin = Admin.get_by_email(email)
        if admin and check_password_hash(admin['Password'], password):
            # Update last login time
            Admin.update_last_login(admin['AdminID'])
            return admin
        return None

    @staticmethod
    def update_last_login(admin_id):
        """Update last login timestamp"""
        query = "UPDATE Admins_114 SET LastLogin = GETDATE() WHERE AdminID = ?"
        execute_db(query, (admin_id,))

    @staticmethod
    def change_password(admin_id, new_password):
        """Change admin password"""
        hashed_password = generate_password_hash(new_password)
        query = "UPDATE Admins_114 SET Password = ?, UpdatedAt = GETDATE() WHERE AdminID = ?"
        execute_db(query, (hashed_password, admin_id))

    @staticmethod
    def activate(admin_id):
        """Activate admin account"""
        query = "UPDATE Admins_114 SET IsActive = 1, UpdatedAt = GETDATE() WHERE AdminID = ?"
        execute_db(query, (admin_id,))

    @staticmethod
    def deactivate(admin_id):
        """Deactivate admin account"""
        query = "UPDATE Admins_114 SET IsActive = 0, UpdatedAt = GETDATE() WHERE AdminID = ?"
        execute_db(query, (admin_id,))

    @staticmethod
    def get_active_count():
        """Get count of active admins"""
        query = "SELECT COUNT(*) as count FROM Admins_114 WHERE IsActive = 1"
        result = query_db(query)
        return result[0]['count'] if result else 0

    @staticmethod
    def search(search_term, limit=50):
        """Search admins by name or email"""
        query = '''
            SELECT * FROM Admins_114 
            WHERE IsActive = 1 
            AND (FirstName LIKE ? OR LastName LIKE ? OR Email LIKE ?)
            ORDER BY FirstName, LastName
        '''
        search_pattern = f"%{search_term}%"
        return query_db(query, (search_pattern, search_pattern, search_pattern))


# Helper function to create the first admin if none exist
def create_first_admin_if_needed():
    """Create first admin if no admins exist"""
    try:
        if Admin.get_active_count() == 0:
            Admin.create({
                'FirstName': 'System',
                'LastName': 'Administrator',
                'Email': 'admin@brightstar.edu',
                'Password': 'admin123'
            })
            print("First admin created: admin@brightstar.edu / admin123")
            return True
    except Exception as e:
        print(f"Error creating first admin: {e}")
    return False