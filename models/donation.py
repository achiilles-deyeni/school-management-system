# models/donation.py
from database import query_db, execute_db
from datetime import datetime

class Donation:
    @staticmethod
    def get_all():
        query = """
            SELECT * FROM Donations_114 ORDER BY DonationDate DESC
        """
        return query_db(query)

    @staticmethod
    def get_by_id(donation_id):
        query = "SELECT * FROM Donations_114 WHERE DonationID = ?"
        results = query_db(query, (donation_id,))
        return results[0] if results else None

    @staticmethod
    def create(data):
        query = """
            INSERT INTO Donations_114 (DonorName, Amount, DonationDate, Purpose)
            VALUES (?, ?, ?, ?)
        """
        params = (data['DonorName'], data['Amount'], data['DonationDate'], data['Purpose'])
        return execute_db(query, params)

    @staticmethod
    def update(donation_id, data):
        query = """
            UPDATE Donations_114
            SET DonorName = ?, Amount = ?, DonationDate = ?, Purpose = ?
            WHERE DonationID = ?
        """
        params = (data['DonorName'], data['Amount'], data['DonationDate'], data['Notes'], donation_id)
        return execute_db(query, params)

    @staticmethod
    def delete(donation_id):
        query = "DELETE FROM Donations_114 WHERE DonationID = ?"
        return execute_db(query, (donation_id,))