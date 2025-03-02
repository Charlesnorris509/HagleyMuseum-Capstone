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
        
        # Set reconnect strategy
        self.db_config['autocommit'] = True
        self.db_config['reconnect'] = True
        self.db_config['connection_timeout'] = 30
        self.db_config['buffered'] = True
        
        self.initialized = True

    def connect_db(self):
        """Create database connection with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                connection = mysql.connector.connect(**self.db_config)
                if connection.is_connected():
                    logger.debug("Connected to MySQL database")
                    return connection
            except Error as e:
                retry_count += 1
                logger.warning(f"Connection attempt {retry_count} failed: {e}")
                if retry_count >= max_retries:
                    logger.error(f"Failed to connect after {max_retries} attempts: {e}")
                    return None
                import time
                time.sleep(1)  # Wait before retrying
        
        return None

    def execute_query(self, query, params=None, fetch=False):
        """
        Execute a query with parameters and return results if needed
        
        For INSERT operations, returns the last inserted ID
        For UPDATE or DELETE, returns the number of affected rows
        For SELECT with fetch=True, returns the fetched rows
        For other operations, returns True on success
        """
        conn = self.connect_db()
        if not conn:
            return None
        
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            operation = query.strip().upper().split(' ')[0]
            
            if operation == 'INSERT':
                # For INSERT, get the auto-generated ID
                last_id = cursor.lastrowid
                if last_id:
                    conn.commit()
                    return last_id
                conn.commit()
                return True
                
            elif operation in ('UPDATE', 'DELETE'):
                # For UPDATE/DELETE, get the number of affected rows
                affected_rows = cursor.rowcount
                conn.commit()
                return affected_rows
                
            elif fetch:
                # For SELECT with fetch, get the results
                return cursor.fetchall()
                
            # For other cases, just return success
            conn.commit()
            return True
            
        except Error as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            if params:
                logger.error(f"Params: {params}")
            
            if conn.is_connected():
                try:
                    conn.rollback()
                    logger.info("Transaction rolled back")
                except:
                    pass
            return None
            
        finally:
            if cursor:
                cursor.close()
            if conn.is_connected():
                conn.close()

    def execute_many(self, query, params_list):
        """Execute the same query with different parameters for batch operations"""
        if not params_list or len(params_list) == 0:
            logger.warning("No parameters provided for execute_many")
            return True
        
        conn = self.connect_db()
        if not conn:
            return False
        
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return True
            
        except Error as e:
            logger.error(f"Error executing batch query: {e}")
            if conn.is_connected():
                try:
                    conn.rollback()
                    logger.info("Transaction rolled back")
                except:
                    pass
            return False
            
        finally:
            if cursor:
                cursor.close()
            if conn.is_connected():
                conn.close()

    def get_existing_pass_id(self, event_id):
        """
        Retrieve the existing ParkingPass ID if it exists for an event
        
        This handles cases where a pass was previously created and we need 
        to find its ID to update associated records (like PassTypes)
        """
        conn = self.connect_db()
        if not conn:
            return None
        
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT PP_id FROM ParkingPasses WHERE Event_ID = %s ORDER BY PP_id DESC LIMIT 1", 
                (event_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
            
        except Error as e:
            logger.error(f"Error getting pass ID: {e}")
            return None
            
        finally:
            if cursor:
                cursor.close()
            if conn.is_connected():
                conn.close()
                
    def get_auto_increment_fields(self):
        """
        Get information about auto-increment fields in the database
        This can be useful for understanding the database schema
        """
        conn = self.connect_db()
        if not conn:
            return None
        
        cursor = None
        try:
            cursor = conn.cursor()
            db_name = self.db_config['database']
            
            query = """
                SELECT TABLE_NAME, COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                AND EXTRA = 'auto_increment'
                ORDER BY TABLE_NAME
            """
            
            cursor.execute(query, (db_name,))
            result = cursor.fetchall()
            
            auto_increment_fields = {}
            for table, column in result:
                auto_increment_fields[table] = column
                
            return auto_increment_fields
            
        except Error as e:
            logger.error(f"Error getting auto-increment fields: {e}")
            return None
            
        finally:
            if cursor:
                cursor.close()
            if conn.is_connected():
                conn.close()