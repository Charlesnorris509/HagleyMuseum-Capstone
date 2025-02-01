# data_sync.py
from typing import Dict, List
from datetime import datetime, timedelta
import os
import mysql.connector
from mysql.connector import Error
from altru_client import AltruAPIClient
from loguru import logger

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
            logger.error("Error connecting to database: {}", e)
            return None

    def sync_customer(self, altru_id: str) -> bool:
        """Sync customer data from Altru to local database"""
        logger.info("Starting customer sync for Altru ID: {}", altru_id)
        constituent = self.altru_client.get_constituent(altru_id)
        if not constituent:
            logger.error("Failed to fetch constituent data for Altru ID: {}", altru_id)
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
            logger.info("Successfully synced customer data for Altru ID: {}", altru_id)
            return True

        except Error as e:
            logger.error("Error syncing customer: {}", e)
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def sync_events(self, start_date: str, end_date: str) -> bool:
        """Sync events data from Altru to local database"""
        logger.info("Starting events sync from {} to {}", start_date, end_date)
        events = self.altru_client.get_events(start_date, end_date)
        if not events:
            logger.error("Failed to fetch events data from {} to {}", start_date, end_date)
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
            logger.info("Successfully synced events data from {} to {}", start_date, end_date)
            return True

        except Error as e:
            logger.error("Error syncing events: {}", e)
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def sync_wristbands(self, start_date: str, end_date: str) -> bool:
        """
        Fetch wristband (ticket) data from Altru within a specified date range 
        and store it in the Wristbands table.
        """
        logger.info("Starting wristbands sync from {} to {}", start_date, end_date)
        tickets_data = self.altru_client.get_tickets(start_date, end_date)
        if not tickets_data:
            logger.error("No wristband or ticket data returned from {} to {}", start_date, end_date)
            return False

        conn = self.connect_db()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            
            query = """
                INSERT INTO Wristbands (Event_ID, Issued)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                Issued = VALUES(Issued)
            """
            
            for ticket in tickets_data:
                data = (
                    ticket.get('event_id'),
                    ticket.get('issued_at')
                )
                cursor.execute(query, data)

            conn.commit()
            logger.info("Successfully synced wristband data from {} to {}", start_date, end_date)
            return True
        
        except Error as e:
            logger.error("Error syncing wristbands: {}", e)
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def sync_parking_passes(self, start_date: str, end_date: str) -> bool:
        """
        Fetch parking pass data from Altru within a specified date range
        and store it in the ParkingPasses table, and optionally PassTypes.
        """
        logger.info("Starting parking passes sync from {} to {}", start_date, end_date)
        passes_data = self.altru_client.get_parking_passes(start_date, end_date)
        if not passes_data:
            logger.error("No parking pass data returned from {} to {}", start_date, end_date)
            return False

        conn = self.connect_db()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            
            pass_query = """
                INSERT INTO ParkingPasses (Event_ID, Issued)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                Issued = VALUES(Issued)
            """
            
            pass_type_query = """
                INSERT INTO PassTypes (PP_id, PassType, Cost)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                PassType = VALUES(PassType), Cost = VALUES(Cost)
            """

            for ppass in passes_data:
                parking_data = (
                    ppass.get('event_id'),
                    ppass.get('issued_at')
                )
                cursor.execute(pass_query, parking_data)
                parking_pass_id = cursor.lastrowid if cursor.lastrowid != 0 else self.get_existing_pass_id(cursor)

                if ppass.get('pass_type'):
                    pass_type_data = (
                        parking_pass_id,
                        ppass.get('pass_type'),
                        ppass.get('cost', 0.00)
                    )
                    cursor.execute(pass_type_query, pass_type_data)

            conn.commit()
            logger.info("Successfully synced parking passes from {} to {}", start_date, end_date)
            return True
        
        except Error as e:
            logger.error("Error syncing parking passes: {}", e)
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def get_existing_pass_id(self, cursor):
        """Retrieve the existing ParkingPass ID if it exists"""
        cursor.execute("SELECT LAST_INSERT_ID()")
        result = cursor.fetchone()
        return result[0] if result else None

def daily_sync():
    """Function to perform daily synchronization"""
    service = DataSyncService()
    today = datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    logger.info("Performing daily sync for {}", today)
    altru_id = "example_altru_id"
    service.sync_customer(altru_id)
    service.sync_events(today, tomorrow)
    service.sync_wristbands(today, tomorrow)
    service.sync_parking_passes(today, tomorrow)

# Schedule the sync job to run every 24 hours
import schedule
import time

schedule.every(24).hours.do(daily_sync)

logger.info("Starting daily sync service...")
while True:
    schedule.run_pending()
    time.sleep(1)
