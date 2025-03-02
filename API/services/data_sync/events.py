from loguru import logger
from mysql.connector import Error

class EventSyncService:
    """
    Service responsible for syncing events data from the Blackbaud API to the local database
    """
    def __init__(self, db_service, api_connector):
        self.db_service = db_service
        self.api_connector = api_connector
        self.message_broker = None  # Will be set if event-driven

    def set_message_broker(self, message_broker):
        """Set a message broker for event-driven sync"""
        self.message_broker = message_broker

    def sync_events(self, start_date: str, end_date: str) -> bool:
        """Sync events data from Altru to local database"""
        logger.info("Starting events sync from {} to {}", start_date, end_date)
        
        # Get events from Blackbaud API
        events = self.api_connector.get_events(start_date, end_date)
        if not events:
            logger.error("Failed to fetch events data from {} to {}", start_date, end_date)
            return False

        success_count = 0
        failed_count = 0

        # Insert each event
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

            result = self.db_service.execute_query(query, data)
            if result:
                success_count += 1
                
                # Notify that an event was synced
                if self.message_broker:
                    self.message_broker.publish_message(
                        'event_sync_events',
                        {
                            'event': 'event_synced',
                            'event_id': event.get('id'),
                            'status': 'success',
                            'name': event.get('name')
                        }
                    )
            else:
                failed_count += 1
                
                # Notify that an event sync failed
                if self.message_broker:
                    self.message_broker.publish_message(
                        'event_sync_events',
                        {
                            'event': 'event_sync_failed',
                            'event_id': event.get('id'),
                            'status': 'failed',
                            'name': event.get('name')
                        }
                    )

        total = success_count + failed_count
        logger.info("Synced {}/{} events from {} to {}", success_count, total, start_date, end_date)
        
        # Publish summary event
        if self.message_broker:
            self.message_broker.publish_message(
                'event_sync_events',
                {
                    'event': 'events_sync_completed',
                    'start_date': start_date,
                    'end_date': end_date,
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'total': total
                }
            )
        
        return failed_count == 0

    def handle_event_sync_message(self, ch, method, properties, body):
        """Handle event sync messages from the message broker"""
        try:
            import json
            message = json.loads(body)
            logger.info("Received event sync message: {}", message)
            
            start_date = message.get('start_date')
            end_date = message.get('end_date')
            
            if not start_date or not end_date:
                logger.error("Missing start_date or end_date in message")
                return
                
            self.sync_events(start_date, end_date)
        except Exception as e:
            logger.error("Error handling event sync message: {}", e)