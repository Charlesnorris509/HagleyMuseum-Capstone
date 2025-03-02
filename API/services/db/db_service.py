import os
import mysql.connector
from mysql.connector import Error
from loguru import logger
from dotenv import load_dotenv

class DBService:
    """
    Database Service class to handle all database interactions
    This service abstracts away database-specific code from the rest of the application
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBService, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        
        load_dotenv()
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME')
        }

        # Check if all database configuration values are set
        if not all(self.db_config.values()):
            logger.error("Database configuration is incomplete. Please check environment variables.")
            raise ValueError("Database configuration is incomplete. Please check environment variables.")
        
        self.initialized = True

    def connect_db(self):
        """Create database connection"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            if connection.is_connected():
                logger.debug("Connected to MySQL database")
                return connection
        except Error as e:
            logger.error("Error connecting to database: {}", e)
            return None

    def execute_query(self, query, params=None, fetch=False):
        """Execute a query with parameters and return results if needed"""
        conn = self.connect_db()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                conn.commit()
                if cursor.lastrowid:
                    return cursor.lastrowid
                else:
                    return cursor.rowcount
            
            if fetch:
                return cursor.fetchall()
            return True
            
        except Error as e:
            logger.error("Error executing query: {}", e)
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def execute_many(self, query, params_list):
        """Execute the same query with different parameters for batch operations"""
        conn = self.connect_db()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return True
        except Error as e:
            logger.error("Error executing batch query: {}", e)
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def get_existing_pass_id(self, event_id):
        """Retrieve the existing ParkingPass ID if it exists"""
        conn = self.connect_db()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT PP_id FROM ParkingPasses WHERE Event_ID = %s ORDER BY PP_id DESC LIMIT 1", 
                          (event_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            logger.error("Error getting pass ID: {}", e)
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()