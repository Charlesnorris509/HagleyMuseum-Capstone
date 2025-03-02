from loguru import logger
from mysql.connector import Error

class CustomerSyncService:
    """
    Service responsible for syncing customer data from the Blackbaud API to the local database
    """
    def __init__(self, db_service, api_connector):
        self.db_service = db_service
        self.api_connector = api_connector
        self.message_broker = None  # Will be set if event-driven

    def set_message_broker(self, message_broker):
        """Set a message broker for event-driven sync"""
        self.message_broker = message_broker

    def sync_customer(self, altru_id: str) -> bool:
        """Sync customer data from Altru to local database"""
        logger.info("Starting customer sync for Altru ID: {}", altru_id)
        
        # Get constituent from Blackbaud API
        constituent = self.api_connector.get_constituent(altru_id)
        if not constituent:
            logger.error("Failed to fetch constituent data for Altru ID: {}", altru_id)
            return False

        # Prepare query and data - now including MembershipLevel, Attended, Paid, Cancelled fields
        query = """
            INSERT INTO Customers
            (Member_id, MembershipLevel, Fname, Lname, Phone, Email, Address1, Address2,
            City, State, Zip, Attended, Paid, Cancelled, Altru_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            MembershipLevel=VALUES(MembershipLevel),
            Fname=VALUES(Fname), Lname=VALUES(Lname), Phone=VALUES(Phone),
            Email=VALUES(Email), Address1=VALUES(Address1),
            Address2=VALUES(Address2), City=VALUES(City), State=VALUES(State),
            Zip=VALUES(Zip), Attended=VALUES(Attended), Paid=VALUES(Paid), 
            Cancelled=VALUES(Cancelled)
        """

        # Extract membership level from constituent data if available
        membership_level = constituent.get('membership', {}).get('level', None)
        
        # Extract attendance and payment status from constituent data if available
        # Default values: Attended=NULL, Paid=NULL, Cancelled=NULL
        attended = constituent.get('attended', None)  
        paid = constituent.get('payment_status', {}).get('is_paid', None)
        cancelled = constituent.get('status', '') == 'Cancelled'
        
        # Convert boolean values to 0/1 for MySQL TINYINT
        attended = 1 if attended else (0 if attended is False else None)
        paid = 1 if paid else (0 if paid is False else None)
        cancelled = 1 if cancelled else 0

        data = (
            constituent.get('member_id'),
            membership_level,
            constituent.get('first_name'),
            constituent.get('last_name'),
            constituent.get('phone'),
            constituent.get('email'),
            constituent.get('address_lines', [None])[0],
            constituent.get('address_lines', [None, None])[1],
            constituent.get('city'),
            constituent.get('state'),
            constituent.get('postal_code'),
            attended,
            paid,
            cancelled,
            altru_id
        )

        # Execute the query
        result = self.db_service.execute_query(query, data)
        
        if result:
            logger.info("Successfully synced customer data for Altru ID: {}", altru_id)
            
            # Publish event for successful sync if message broker is available
            if self.message_broker:
                self.message_broker.publish_message(
                    'customer_sync_events', 
                    {
                        'event': 'customer_synced',
                        'altru_id': altru_id,
                        'status': 'success'
                    }
                )
            return True
        else:
            logger.error("Failed to sync customer data for Altru ID: {}", altru_id)
            
            # Publish event for failed sync if message broker is available
            if self.message_broker:
                self.message_broker.publish_message(
                    'customer_sync_events', 
                    {
                        'event': 'customer_sync_failed',
                        'altru_id': altru_id,
                        'status': 'failed'
                    }
                )
            return False

    def handle_customer_sync_message(self, ch, method, properties, body):
        """Handle customer sync messages from the message broker"""
        try:
            import json
            message = json.loads(body)
            logger.info("Received customer sync message: {}", message)
            
            altru_id = message.get('altru_id')
            if not altru_id:
                logger.error("No Altru ID in message")
                return
                
            self.sync_customer(altru_id)
        except Exception as e:
            logger.error("Error handling customer sync message: {}", e)