"""
Worker Service for processing sync tasks asynchronously.
This service can be run independently from the API to process events from the message queue.
"""

import os
import json
import signal
import sys
from threading import Thread, Event
from loguru import logger
from dotenv import load_dotenv

# Import our services
from API.services.db.db_service import DBService
from API.services.message_broker.broker_service import MessageBroker
from API.services.data_sync.customers import CustomerSyncService
from API.services.data_sync.events import EventSyncService
from API.services.data_sync.wristbands import WristbandSyncService
from API.services.data_sync.parking_passes import ParkingPassSyncService
from API.BbApiConnector.BbApiConnector import BbApiConnector

class Worker:
    """
    Worker service that consumes messages from the queue and processes them.
    This enables scaling the processing of sync tasks independently from the API.
    """
    def __init__(self):
        load_dotenv()
        
        # Initialize services
        self.db_service = DBService()
        self.message_broker = MessageBroker()
        
        # Initialize the API connector
        config_path = os.getenv("BB_CONFIG_PATH", "API/resources/app_secrets.json")
        self.api_connector = BbApiConnector(config_file_name=config_path)
        
        # Initialize sync services
        self.customer_sync_service = CustomerSyncService(self.db_service, self.api_connector)
        self.event_sync_service = EventSyncService(self.db_service, self.api_connector)
        self.wristband_sync_service = WristbandSyncService(self.db_service, self.api_connector)
        self.parking_pass_sync_service = ParkingPassSyncService(self.db_service, self.api_connector)
        
        # Set the message broker on each service
        self.customer_sync_service.set_message_broker(self.message_broker)
        self.event_sync_service.set_message_broker(self.message_broker)
        self.wristband_sync_service.set_message_broker(self.message_broker)
        self.parking_pass_sync_service.set_message_broker(self.message_broker)
        
        # Threading controls
        self.stop_event = Event()
        self.threads = []
        
        # Queues to consume from
        self.queues = [
            ('sync_queue', self.handle_sync_message),
            ('customer_sync_events', self.customer_sync_service.handle_customer_sync_message),
            ('event_sync_events', self.event_sync_service.handle_event_sync_message),
            ('wristband_sync_events', self.wristband_sync_service.handle_wristband_sync_message),
            ('parking_pass_sync_events', self.parking_pass_sync_service.handle_parking_pass_sync_message)
        ]
    
    def handle_sync_message(self, ch, method, properties, body):
        """
        Handle messages from the sync queue.
        This is the main entry point for synchronization tasks.
        """
        try:
            message = json.loads(body)
            logger.info(f"Worker received sync message: {message}")
            
            message_type = message.get('type')
            
            if message_type == 'customer_sync':
                altru_id = message.get('altru_id', "example_altru_id")
                self.customer_sync_service.sync_customer(altru_id)
            
            elif message_type == 'event_sync':
                start_date = message.get('start_date')
                end_date = message.get('end_date')
                if start_date and end_date:
                    self.event_sync_service.sync_events(start_date, end_date)
            
            elif message_type == 'wristband_sync':
                start_date = message.get('start_date')
                end_date = message.get('end_date')
                if start_date and end_date:
                    self.wristband_sync_service.sync_wristbands(start_date, end_date)
            
            elif message_type == 'parking_pass_sync':
                start_date = message.get('start_date')
                end_date = message.get('end_date')
                if start_date and end_date:
                    self.parking_pass_sync_service.sync_parking_passes(start_date, end_date)
            
            elif message_type == 'full_sync':
                from datetime import datetime
                today = datetime.now().strftime('%Y-%m-%d')
                start_date = message.get('start_date', today)
                end_date = message.get('end_date', today)
                
                self.customer_sync_service.sync_customer("example_altru_id")
                self.event_sync_service.sync_events(start_date, end_date)
                self.wristband_sync_service.sync_wristbands(start_date, end_date)
                self.parking_pass_sync_service.sync_parking_passes(start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error handling sync message: {e}")
    
    def start_consumer(self, queue_name, callback):
        """Start a consumer for a specific queue in a separate thread"""
        def consumer_thread():
            try:
                logger.info(f"Starting consumer for queue: {queue_name}")
                self.message_broker.declare_queue(queue_name)
                self.message_broker.consume_messages(queue_name, callback)
            except Exception as e:
                logger.error(f"Error in consumer for queue {queue_name}: {e}")
                if not self.stop_event.is_set():
                    logger.info(f"Restarting consumer for queue: {queue_name}")
                    self.start_consumer(queue_name, callback)
        
        thread = Thread(target=consumer_thread)
        thread.daemon = True
        thread.start()
        self.threads.append(thread)
        return thread
    
    def start(self):
        """Start all consumers"""
        logger.info("Starting worker service")
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start consumers for all queues
        for queue_name, callback in self.queues:
            self.start_consumer(queue_name, callback)
        
        # Keep the main thread alive
        try:
            while not self.stop_event.is_set():
                self.stop_event.wait(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.stop()
    
    def signal_handler(self, sig, frame):
        """Handle termination signals"""
        logger.info(f"Signal {sig} received, shutting down...")
        self.stop()
    
    def stop(self):
        """Stop all consumers and cleanup"""
        logger.info("Stopping worker service")
        self.stop_event.set()
        
        if self.message_broker:
            self.message_broker.stop_consuming()
            self.message_broker.close()
        
        logger.info("Worker service stopped")
        sys.exit(0)

if __name__ == "__main__":
    logger.info("Initializing worker service")
    worker = Worker()
    worker.start()