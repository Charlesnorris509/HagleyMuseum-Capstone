from typing import Dict, List
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from altru_client import AltruAPIClient

class DataSyncService:
    def __init__(self):
        self.altru_client = AltruAPIClient()
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME')
        }

    def connect_db(self):
        """Create database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Error as e:
            print(f"Error connecting to database: {e}")
            return None

    def sync_customer(self, altru_id: str) -> bool:
        """Sync customer data from Altru to local database"""
        constituent = self.altru_client.get_constituent(altru_id)
        if not constituent:
            return False

        conn = self.connect_db()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO Customers 
                (Member_id, Fname, Lname, Phone, Email, Address1, Address2, 
                 City, State, Zip, Altru_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                Fname=VALUES(Fname), Lname=VALUES(Lname), Phone=VALUES(Phone),
                Email=VALUES(Email), Address1=VALUES(Address1), 
                Address2=VALUES(Address2), City=VALUES(City), State=VALUES(State),
                Zip=VALUES(Zip)
            """
            
            data = (
                constituent.get('member_id'),
                constituent.get('first_name'),
                constituent.get('last_name'),
                constituent.get('phone'),
                constituent.get('email'),
                constituent.get('address_lines', [None])[0],
                constituent.get('address_lines', [None, None])[1],
                constituent.get('city'),
                constituent.get('state'),
                constituent.get('postal_code'),
                altru_id
            )
            
            cursor.execute(query, data)
            conn.commit()
            return True

        except Error as e:
            print(f"Error syncing customer: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def sync_events(self, start_date: str, end_date: str) -> bool:
        """Sync events data from Altru to local database"""
        events = self.altru_client.get_events(start_date, end_date)
        if not events:
            return False

        conn = self.connect_db()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            for event in events:
                query = """
                    INSERT INTO Events (C_id, Name, EventDate)
                    VALUES (
                        (SELECT C_id FROM Customers WHERE Altru_id = %s),
                        %s, %s)
                    ON DUPLICATE KEY UPDATE
                    Name=VALUES(Name), EventDate=VALUES(EventDate)
                """
                
                data = (
                    event.get('constituent_id'),
                    event.get('name'),
                    event.get('start_date')
                )
                
                cursor.execute(query, data)
            
            conn.commit()
            return True

        except Error as e:
            print(f"Error syncing events: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
