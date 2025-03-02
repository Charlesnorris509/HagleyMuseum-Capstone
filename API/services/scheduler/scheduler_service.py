import schedule
import time
import threading
from datetime import datetime, timedelta
from loguru import logger

class SchedulerService:
    """
    Scheduler Service to orchestrate periodic and event-driven sync tasks
    """
    def __init__(self, db_service, api_connector, message_broker=None):
        self.db_service = db_service
        self.api_connector = api_connector
        self.message_broker = message_broker
        self.sync_services = {}
        self.running = False
        self.scheduler_thread = None
        self.consumer_threads = {}
        
    def register_sync_service(self, name, service):
        """Register a sync service to be used by the scheduler"""
        self.sync_services[name] = service
        # If we have a message broker, set it on the service
        if self.message_broker and hasattr(service, 'set_message_broker'):
            service.set_message_broker(self.message_broker)
        return self
            
    def daily_sync(self):
        """Perform a daily sync of all registered services"""
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info("Starting daily sync for {}", today)
        
        # If we have a message broker, publish sync events instead of calling directly
        if self.message_broker:
            self.message_broker.publish_message('sync_queue', {'event': 'daily_sync_started', 'date': today})
            
            # Customer sync
            if 'customer' in self.sync_services:
                self.message_broker.publish_message(
                    'sync_queue', 
                    {
                        'type': 'customer_sync',
                        'altru_id': "example_altru_id"
                    }
                )
            
            # Events sync
            if 'event' in self.sync_services:
                self.message_broker.publish_message(
                    'sync_queue',
                    {
                        'type': 'event_sync',
                        'start_date': today,
                        'end_date': tomorrow
                    }
                )
            
            # Wristbands sync
            if 'wristband' in self.sync_services:
                self.message_broker.publish_message(
                    'sync_queue',
                    {
                        'type': 'wristband_sync',
                        'start_date': today,
                        'end_date': tomorrow
                    }
                )
            
            # Parking passes sync
            if 'parking_pass' in self.sync_services:
                self.message_broker.publish_message(
                    'sync_queue',
                    {
                        'type': 'parking_pass_sync',
                        'start_date': today,
                        'end_date': tomorrow
                    }
                )
                
            self.message_broker.publish_message('sync_queue', {'event': 'daily_sync_scheduled', 'date': today})
        else:
            # Direct sync without message broker
            if 'customer' in self.sync_services:
                self.sync_services['customer'].sync_customer("example_altru_id")
            
            if 'event' in self.sync_services:
                self.sync_services['event'].sync_events(today, tomorrow)
            
            if 'wristband' in self.sync_services:
                self.sync_services['wristband'].sync_wristbands(today, tomorrow)
            
            if 'parking_pass' in self.sync_services:
                self.sync_services['parking_pass'].sync_parking_passes(today, tomorrow)
                
            logger.info("Daily sync completed for {}", today)
    
    def handle_sync_message(self, ch, method, properties, body):
        """Handle sync messages from the message broker"""
        import json
        try:
            message = json.loads(body)
            logger.info("Received sync message: {}", message)
            
            message_type = message.get('type')
            
            if message_type == 'customer_sync':
                if 'customer' in self.sync_services:
                    altru_id = message.get('altru_id', "example_altru_id")
                    self.sync_services['customer'].sync_customer(altru_id)
            
            elif message_type == 'event_sync':
                if 'event' in self.sync_services:
                    start_date = message.get('start_date')
                    end_date = message.get('end_date')
                    if start_date and end_date:
                        self.sync_services['event'].sync_events(start_date, end_date)
            
            elif message_type == 'wristband_sync':
                if 'wristband' in self.sync_services:
                    start_date = message.get('start_date')
                    end_date = message.get('end_date')
                    if start_date and end_date:
                        self.sync_services['wristband'].sync_wristbands(start_date, end_date)
            
            elif message_type == 'parking_pass_sync':
                if 'parking_pass' in self.sync_services:
                    start_date = message.get('start_date')
                    end_date = message.get('end_date')
                    if start_date and end_date:
                        self.sync_services['parking_pass'].sync_parking_passes(start_date, end_date)
            
            elif message_type == 'full_sync':
                self.daily_sync()
                
        except Exception as e:
            logger.error("Error handling sync message: {}", e)
    
    def start_scheduler(self):
        """Start the scheduler in its own thread"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        self.running = True
        
        # Set up the schedule
        schedule.every().day.at("00:00").do(self.daily_sync)
        
        # Run the scheduler in a separate thread
        def run_scheduler():
            logger.info("Starting scheduler thread")
            while self.running:
                schedule.run_pending()
                time.sleep(1)
                
        self.scheduler_thread = threading.Thread(target=run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        # If we have a message broker, start the consumer threads
        if self.message_broker:
            self.start_consumers()
            
        logger.info("Scheduler started")
    
    def start_consumers(self):
        """Start the message broker consumers"""
        if not self.message_broker:
            logger.warning("No message broker available, can't start consumers")
            return
            
        # Start consumer for sync queue
        def run_sync_consumer():
            logger.info("Starting sync queue consumer")
            self.message_broker.declare_queue('sync_queue')
            self.message_broker.consume_messages('sync_queue', self.handle_sync_message)
            
        sync_thread = threading.Thread(target=run_sync_consumer)
        sync_thread.daemon = True
        sync_thread.start()
        self.consumer_threads['sync'] = sync_thread
        
        logger.info("Consumers started")
    
    def stop(self):
        """Stop the scheduler and consumers"""
        self.running = False
        
        if self.message_broker:
            self.message_broker.stop_consuming()
            self.message_broker.close()
            
        logger.info("Scheduler stopped")