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
        
    def get_pass_type_limits(self):
        """Get the limits for each pass type from the database"""
        # This could be stored in a configuration table or hardcoded based on business rules
        return {
            'General': 800,
            'Premium': 60,
            'Catering': 30,
            'Buck Road': 40
        }

    def check_pass_type_availability(self, event_id, pass_type):
        """Check if there is still availability for a specific pass type"""
        limits = self.get_pass_type_limits()
        
        if pass_type not in limits:
            # If no limit defined for this pass type, assume it's available
            return True
            
        # Count how many passes of this type already exist for this event
        query = """
            SELECT COUNT(pt.PT_id) 
            FROM PassTypes pt
            JOIN ParkingPasses pp ON pt.PP_id = pp.PP_id
            WHERE pp.Event_ID = %s AND pt.PassTypes = %s
        """
        
        data = (event_id, pass_type)
        result = self.db_service.execute_query(query, data, fetch=True)
        
        if not result or not result[0]:
            return True
            
        current_count = result[0][0]
        return current_count < limits[pass_type]

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
        limit_reached_count = 0

        # Process each parking pass
        for ppass in passes_data:
            event_id = ppass.get('event_id')
            pass_type = ppass.get('pass_type')
            
            # Check if we've reached the limit for this pass type
            if pass_type and not self.check_pass_type_availability(event_id, pass_type):
                logger.warning("Limit reached for pass type {} for event ID {}", pass_type, event_id)
                limit_reached_count += 1
                
                # Notify about limit reached if message broker is available
                if self.message_broker:
                    self.message_broker.publish_message(
                        'parking_pass_sync_events', 
                        {
                            'event': 'parking_pass_limit_reached',
                            'event_id': event_id,
                            'pass_type': pass_type,
                            'status': 'limit_reached'
                        }
                    )
                continue
                
            # First insert the parking pass
            pass_query = """
                INSERT INTO ParkingPasses (Event_ID, Issued)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                Issued = VALUES(Issued)
            """

            parking_data = (
                event_id,
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
                            'event_id': event_id,
                            'status': 'failed'
                        }
                    )
                continue
                
            # If this was an ON DUPLICATE KEY UPDATE, we need to get the actual PP_id
            if isinstance(pass_id, int) and pass_id <= 0:
                pass_id = self.db_service.get_existing_pass_id(event_id)
                if not pass_id:
                    logger.error("Failed to retrieve existing parking pass ID for event ID: {}", event_id)
                    failed_count += 1
                    continue
                
            # If the parking pass has a type, insert it into the PassTypes table
            if pass_type:
                pass_type_query = """
                    INSERT INTO PassTypes (PP_id, PassTypes, Cost)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    PassTypes = VALUES(PassTypes), Cost = VALUES(Cost)
                """

                pass_type_data = (
                    pass_id,
                    pass_type,
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
                                'event_id': event_id,
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
                        'event_id': event_id,
                        'status': 'success',
                        'pass_type': pass_type
                    }
                )

        total = success_count + failed_count + limit_reached_count
        logger.info(
            "Synced {}/{} parking passes from {} to {} (Failed: {}, Limit reached: {})", 
            success_count, total, start_date, end_date, failed_count, limit_reached_count
        )
        
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
                    'limit_reached_count': limit_reached_count,
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