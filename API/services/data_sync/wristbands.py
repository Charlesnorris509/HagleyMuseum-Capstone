from loguru import logger
from mysql.connector import Error

class WristbandSyncService:
    """
    Service responsible for syncing wristband (ticket) data from the Blackbaud API to the local database
    """
    def __init__(self, db_service, api_connector):
        self.db_service = db_service
        self.api_connector = api_connector
        self.message_broker = None  # Will be set if event-driven

    def set_message_broker(self, message_broker):
        """Set a message broker for event-driven sync"""
        self.message_broker = message_broker

    def sync_wristbands(self, start_date: str, end_date: str) -> bool:
        """
        Sync wristband (ticket) data from Altru to local database
        """
        logger.info("Starting wristbands sync from {} to {}", start_date, end_date)
        
        # Get tickets from Blackbaud API
        tickets_data = self.api_connector.get_tickets(start_date, end_date)
        if not tickets_data:
            logger.error("No wristband or ticket data returned from {} to {}", start_date, end_date)
            
            # Publish event for empty data if message broker is available
            if self.message_broker:
                self.message_broker.publish_message(
                    'wristband_sync_events', 
                    {
                        'event': 'wristband_sync_empty',
                        'start_date': start_date,
                        'end_date': end_date,
                        'status': 'no_data'
                    }
                )
            return False

        success_count = 0
        failed_count = 0

        # Process each ticket/wristband
        for ticket in tickets_data:
            query = """
                INSERT INTO Wristbands (Event_ID, Issued)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                Issued = VALUES(Issued)
            """

            data = (
                ticket.get('event_id'),
                ticket.get('issued_at')
            )
            
            result = self.db_service.execute_query(query, data)
            
            if result:
                success_count += 1
                # Notify that a wristband was synced if message broker is available
                if self.message_broker:
                    self.message_broker.publish_message(
                        'wristband_sync_events', 
                        {
                            'event': 'wristband_synced',
                            'wristband_id': result,  # This would be the last inserted ID
                            'event_id': ticket.get('event_id'),
                            'status': 'success'
                        }
                    )
            else:
                failed_count += 1
                # Notify that a wristband sync failed if message broker is available
                if self.message_broker:
                    self.message_broker.publish_message(
                        'wristband_sync_events', 
                        {
                            'event': 'wristband_sync_failed',
                            'event_id': ticket.get('event_id'),
                            'status': 'failed'
                        }
                    )

        total = success_count + failed_count
        logger.info("Synced {}/{} wristbands from {} to {}", success_count, total, start_date, end_date)
        
        # Publish summary event if message broker is available
        if self.message_broker:
            self.message_broker.publish_message(
                'wristband_sync_events',
                {
                    'event': 'wristbands_sync_completed',
                    'start_date': start_date,
                    'end_date': end_date,
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'total': total,
                    'status': 'success' if failed_count == 0 else 'partial_failure'
                }
            )
        
        return failed_count == 0

    def handle_wristband_sync_message(self, ch, method, properties, body):
        """Handle wristband sync messages from the message broker"""
        try:
            import json
            message = json.loads(body)
            logger.info("Received wristband sync message: {}", message)
            
            start_date = message.get('start_date')
            end_date = message.get('end_date')
            
            if not start_date or not end_date:
                logger.error("Missing start_date or end_date in message")
                return
                
            self.sync_wristbands(start_date, end_date)
        except Exception as e:
            logger.error("Error handling wristband sync message: {}", e)