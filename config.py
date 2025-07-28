# config.py - Configuration settings
import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')

    # Database settings
    DB_SERVER = 'CHILOO\\SQLEXPRESS'
    DB_NAME = 'Bright_Star'

    # Primary connection string with timeout settings
    DB_CONNECTION_STRING = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"Trusted_Connection=yes;"
        f"Connection Timeout=30;"
        f"Login Timeout=30;"
        f"Connect Timeout=30;"
    )

    # Backup connection strings to try if primary fails
    BACKUP_CONNECTION_STRINGS = [
        # Option 1: Using (local) instead of computer name
        (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER=(local)\\SQLEXPRESS;"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
            f"Connection Timeout=30;"
            f"Login Timeout=30;"
        ),

        # Option 2: Using TCP/IP
        (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER=tcp:{DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
            f"Connection Timeout=30;"
            f"Login Timeout=30;"
        ),

        # Option 3: Named pipe connection
        (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER=np:\\\\{DB_SERVER}\\pipe\\sql\\query;"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
            f"Connection Timeout=30;"
            f"Login Timeout=30;"
        ),

        # Option 4: Force network library
        (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
            f"Network Library=DBMSSOCN;"
            f"Connection Timeout=30;"
            f"Login Timeout=30;"
        ),
    ]


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# Default config
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}