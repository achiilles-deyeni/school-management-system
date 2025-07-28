# models/expense.py
from database import query_db, execute_db

class Expense:
    @staticmethod
    def get_all():
        query = "SELECT * FROM Expenses_114 ORDER BY ExpenseDate DESC"
        return query_db(query)

    @staticmethod
    def get_by_id(expense_id):
        query = "SELECT * FROM Expenses_114 WHERE ExpenseID = ?"
        results = query_db(query, (expense_id,))
        return results[0] if results else None

    @staticmethod
    def create(data):
        query = """
            INSERT INTO Expenses_114 (Title, Amount, ExpenseDate, Category, Notes)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (data['Title'], data['Amount'], data['ExpenseDate'], data['Category'], data['Notes'])
        return execute_db(query, params)

    @staticmethod
    def update(expense_id, data):
        query = """
            UPDATE Expenses_114
            SET Title = ?, Amount = ?, ExpenseDate = ?, Category = ?, Notes = ?
            WHERE ExpenseID = ?
        """
        params = (data['Title'], data['Amount'], data['ExpenseDate'], data['Category'], data['Notes'], expense_id)
        return execute_db(query, params)

    @staticmethod
    def delete(expense_id):
        query = "DELETE FROM Expenses_114 WHERE ExpenseID = ?"
        return execute_db(query, (expense_id,))