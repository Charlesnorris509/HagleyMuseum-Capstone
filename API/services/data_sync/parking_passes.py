from loguru import logger
from mysql.connector import Error

class ParkingPassSyncService:
    """
    Service responsible for syncing parking pass data from the Blackbaud API to the local database
    """
    def __init__(self, db_service, api_connector):
        self.db_service = db_service
        self.api_connector = api_connector
        self.message_broker = None  # Will be set if event-driven

    def set_message_broker(self, message_broker):
        """Set a message broker for event-driven sync"""
        self.message_broker = message_broker

    def sync_parking_passes(self, start_date: str, end_date: str) -> bool:
        """
        Sync parking pass data from Altru to local database
        """
        logger.info("Starting parking passes sync from {} to {}", start_date, end_date)
        
        # Get parking passes from Blackbaud API
        passes_data = self.api_connector.get_parking_passes(start_date, end_date)
        if not passes_data:
            logger.error("No parking pass data returned from {} to {}", start_date, end_date)
            
            # Publish event for empty data if message broker is available
            if self.message_broker:
                self.message_broker.publish_message(
                    'parking_pass_sync_events', 
                    {
                        'event': 'parking_pass_sync_empty',
                        'start_date': start_date,
                        'end_date': end_date,
                        'status': 'no_data'
                    }
                )
            return False

        success_count = 0
        failed_count = 0

        # Process each parking pass
        for ppass in passes_data:
            # First insert the parking pass
            pass_query = """
                INSERT INTO ParkingPasses (Event_ID, Issued)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                Issued = VALUES(Issued)
            """

            parking_data = (
                ppass.get('event_id'),
                ppass.get('issued_at')
            )
            
            # Execute the parking pass query and get the ID
            pass_id = self.db_service.execute_query(pass_query, parking_data)
            
            if not pass_id:
                failed_count += 1
                
                # Notify that a parking pass sync failed if message broker is available
                if self.message_broker:
                    self.message_broker.publish_message(
                        'parking_pass_sync_events', 
                        {
                            'event': 'parking_pass_sync_failed',
                            'event_id': ppass.get('event_id'),
                            'status': 'failed'
                        }
                    )
                continue
                
            # If the parking pass has a type, insert it into the PassTypes table
            if ppass.get('pass_type'):
                pass_type_query = """
                    INSERT INTO PassTypes (PP_id, PassTypes, Cost)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    PassTypes = VALUES(PassTypes), Cost = VALUES(Cost)
                """

                pass_type_data = (
                    pass_id,
                    ppass.get('pass_type'),
                    ppass.get('cost', 0.00)
                )
                
                # Execute the pass type query
                type_result = self.db_service.execute_query(pass_type_query, pass_type_data)
                
                if not type_result:
                    # We had a partial failure (pass was inserted but type wasn't)
                    logger.warning("Parking pass inserted but type failed for pass ID: {}", pass_id)
                    
                    # Notify of partial failure if message broker is available
                    if self.message_broker:
                        self.message_broker.publish_message(
                            'parking_pass_sync_events', 
                            {
                                'event': 'parking_pass_type_sync_failed',
                                'parking_pass_id': pass_id,
                                'event_id': ppass.get('event_id'),
                                'status': 'partial_failure'
                            }
                        )
                    
                    # Still count it as a success for the pass itself
                    success_count += 1
                    continue
            
            # If we got here, everything succeeded
            success_count += 1
            
            # Notify that a parking pass was synced if message broker is available
            if self.message_broker:
                self.message_broker.publish_message(
                    'parking_pass_sync_events', 
                    {
                        'event': 'parking_pass_synced',
                        'parking_pass_id': pass_id,
                        'event_id': ppass.get('event_id'),
                        'status': 'success',
                        'pass_type': ppass.get('pass_type')
                    }
                )

        total = success_count + failed_count
        logger.info("Synced {}/{} parking passes from {} to {}", success_count, total, start_date, end_date)
        
        # Publish summary event if message broker is available
        if self.message_broker:
            self.message_broker.publish_message(
                'parking_pass_sync_events',
                {
                    'event': 'parking_pass_sync_completed',
                    'start_date': start_date,
                    'end_date': end_date,
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'total': total,
                    'status': 'success' if failed_count == 0 else 'partial_failure'
                }
            )
        
        return failed_count == 0

    def handle_parking_pass_sync_message(self, ch, method, properties, body):
        """Handle parking pass sync messages from the message broker"""
        try:
            import json
            message = json.loads(body)
            logger.info("Received parking pass sync message: {}", message)
            
            start_date = message.get('start_date')
            end_date = message.get('end_date')
            
            if not start_date or not end_date:
                logger.error("Missing start_date or end_date in message")
                return
                
            self.sync_parking_passes(start_date, end_date)
        except Exception as e:
            logger.error("Error handling parking pass sync message: {}", e)