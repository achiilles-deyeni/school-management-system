# database.py - Database connection and utilities
import pyodbc
import logging
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)


def test_connection(conn_str, timeout=10):
    """Test a single connection string"""
    try:
        logger.info(f"Testing connection: {conn_str[:50]}...")
        conn = pyodbc.connect(conn_str, timeout=timeout)

        # Test with a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()

        conn.close()
        logger.info("✅ Connection test successful!")
        return True
    except Exception as e:
        logger.warning(f"❌ Connection test failed: {str(e)}")
        return False


def get_working_connection_string():
    """Find a working connection string"""
    # Try primary connection string first
    if test_connection(Config.DB_CONNECTION_STRING):
        logger.info("Using primary connection string")
        return Config.DB_CONNECTION_STRING

    # Try backup connection strings
    logger.info("Primary connection failed, trying backup options...")
    for i, backup_conn_str in enumerate(Config.BACKUP_CONNECTION_STRINGS, 1):
        logger.info(f"Trying backup connection {i}...")
        if test_connection(backup_conn_str):
            logger.info(f"✅ Backup connection {i} successful!")
            return backup_conn_str

    # If all fail, raise an error with diagnostics
    logger.error("❌ All connection attempts failed!")
    raise Exception("No working database connection found. Check SQL Server service and configuration.")


# def get_db():
#     """Get database connection with fallback logic"""
#     try:
#         working_conn_str = get_working_connection_string()
#         conn = pyodbc.connect(working_conn_str)
#         return conn
#     except Exception as e:
#         logger.error(f"Database connection error: {str(e)}")
#         print_diagnostics()
#         raise

# Database connection settings
def get_db():
    """Get database connection using Config settings"""
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}}; SERVER={Config.DB_SERVER}; DATABASE={Config.DB_NAME}; Trusted_Connection=yes'
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception:
        # Fallback to older driver if ODBC Driver 17 is not available
        fallback_conn_str = f'DRIVER={{SQL Server}}; SERVER={Config.DB_SERVER}; DATABASE={Config.DB_NAME}; Trusted_Connection=yes'
        conn = pyodbc.connect(fallback_conn_str)
        return conn


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = get_db()
        yield conn
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


def init_db():
    """Initialize database connection on app startup"""
    try:
        logger.info("Initializing database connection...")

        with get_db_connection() as conn:
            logger.info("✅ Database connection successful")

            # Test a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT GETDATE()")
            result = cursor.fetchone()
            logger.info(f"✅ Database query test successful. Server time: {result[0]}")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise


def query_db(query, params=None, fetchone=False):
    """Execute a query and return results"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetchone:
                result = cursor.fetchone()
                if result:
                    columns = [column[0] for column in cursor.description]
                    return dict(zip(columns, result))
                return None
            else:
                results = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in results]

    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise


def execute_db(query, params=None, commit=True):
    """Execute a query (INSERT, UPDATE, DELETE)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if commit:
                conn.commit()

            return cursor.rowcount

    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise


def print_diagnostics():
    """Print diagnostic information"""
    print("\n" + "=" * 50)
    print("🔍 SQL SERVER DIAGNOSTICS")
    print("=" * 50)

    # Check available drivers
    print("Available ODBC drivers:")
    drivers = [x for x in pyodbc.drivers() if 'SQL Server' in x]
    for driver in drivers:
        print(f"  ✅ {driver}")

    if not drivers:
        print("  ❌ No SQL Server ODBC drivers found!")
        print("  💡 Install 'Microsoft ODBC Driver 17 for SQL Server'")
        return

    print(f"\nDatabase Configuration:")
    print(f"  Server: {Config.DB_SERVER}")
    print(f"  Database: {Config.DB_NAME}")

    print(f"\nConnection String Details:")
    print(f"  Primary: {Config.DB_CONNECTION_STRING}")

    print(f"\n💡 Troubleshooting Steps:")
    print(f"  1. Check if SQL Server service is running:")
    print(f"     - Open Services (services.msc)")
    print(f"     - Look for 'SQL Server (SQLEXPRESS)'")
    print(f"     - Ensure it's started")
    print(f"  2. Verify instance name:")
    print(f"     - Open SQL Server Management Studio")
    print(f"     - Check connection server name")
    print(f"  3. Enable TCP/IP in SQL Server Configuration Manager")
    print(f"  4. Check Windows Firewall settings")
    print(f"  5. Verify database '{Config.DB_NAME}' exists")
    print("=" * 50)


# Test function that can be run standalone
def test_all_connections():
    """Test all connection strings"""
    print("Testing all connection strings...\n")

    print("1. Testing primary connection:")
    if test_connection(Config.DB_CONNECTION_STRING):
        print("✅ Primary connection works!")
        return Config.DB_CONNECTION_STRING

    print("\n2. Testing backup connections:")
    for i, backup_conn in enumerate(Config.BACKUP_CONNECTION_STRINGS, 1):
        print(f"   Testing backup {i}:")
        if test_connection(backup_conn):
            print(f"   ✅ Backup {i} works!")
            return backup_conn

    print("\n❌ No working connections found!")
    print_diagnostics()
    return None


if __name__ == "__main__":
    # Run connection tests
    working_conn = test_all_connections()
    if working_conn:
        print(f"\n🎉 SUCCESS! Working connection found.")
        print(f"You can now start your Flask app.")
    else:
        print(f"\n💥 FAILED! No working connection found.")
        print(f"Please check SQL Server setup and try again.")