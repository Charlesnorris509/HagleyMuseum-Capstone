from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from loguru import logger
import uvicorn
import os
from dotenv import load_dotenv

# Import our services
from API.services.db.db_service import DBService
from API.services.message_broker.broker_service import MessageBroker
from API.services.data_sync.customers import CustomerSyncService
from API.services.data_sync.events import EventSyncService
from API.services.scheduler.scheduler_service import SchedulerService
from API.BbApiConnector.BbApiConnector import BbApiConnector

app = FastAPI(
    title="Hagley Museum OLAP API",
    description="API for syncing data between Blackbaud SKY API and local database",
    version="1.0.0"
)

# Models for API requests
class SyncRange(BaseModel):
    start_date: str
    end_date: str

class CustomerSync(BaseModel):
    altru_id: str

# Initialize services
db_service = None
message_broker = None
api_connector = None
scheduler_service = None
customer_sync_service = None
event_sync_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize services when the API starts"""
    global db_service, message_broker, api_connector, scheduler_service, customer_sync_service, event_sync_service
    
    load_dotenv()
    
    # Initialize the database service
    logger.info("Initializing database service")
    db_service = DBService()
    
    # Initialize the message broker
    logger.info("Initializing message broker")
    message_broker = MessageBroker()
    
    # Initialize the API connector
    logger.info("Initializing Blackbaud API connector")
    config_path = os.getenv("BB_CONFIG_PATH", "API/resources/app_secrets.json")
    api_connector = BbApiConnector(config_file_name=config_path)
    
    # Initialize the sync services
    logger.info("Initializing sync services")
    customer_sync_service = CustomerSyncService(db_service, api_connector)
    event_sync_service = EventSyncService(db_service, api_connector)
    
    # Initialize the scheduler service
    logger.info("Initializing scheduler service")
    scheduler_service = SchedulerService(db_service, api_connector, message_broker)
    
    # Register the sync services with the scheduler
    scheduler_service.register_sync_service('customer', customer_sync_service)
    scheduler_service.register_sync_service('event', event_sync_service)
    
    # Start the scheduler in the background
    scheduler_service.start_scheduler()
    
    logger.info("API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the API shuts down"""
    global scheduler_service, message_broker
    
    if scheduler_service:
        logger.info("Stopping scheduler service")
        scheduler_service.stop()
    
    if message_broker:
        logger.info("Closing message broker connection")
        message_broker.close()
    
    logger.info("API shutdown complete")

@app.get("/")
async def root():
    """API root endpoint"""
    return {"status": "online", "message": "Hagley Museum OLAP API is running"}

@app.post("/sync/all")
async def sync_all(sync_range: SyncRange, background_tasks: BackgroundTasks):
    """
    Endpoint to sync all data from Altru
    This uses the event-driven architecture to trigger sync tasks
    """
    logger.info("Received request to sync all data from {} to {}", sync_range.start_date, sync_range.end_date)
    
    if not message_broker:
        raise HTTPException(status_code=503, detail="Message broker service is not available")
    
    # Use the message broker to publish sync events
    background_tasks.add_task(
        message_broker.publish_message,
        'sync_queue',
        {
            'type': 'full_sync',
            'start_date': sync_range.start_date,
            'end_date': sync_range.end_date
        }
    )
    
    return {
        "status": "accepted",
        "message": "Sync tasks scheduled",
        "start_date": sync_range.start_date,
        "end_date": sync_range.end_date
    }

@app.post("/sync/customer")
async def sync_customer(customer: CustomerSync, background_tasks: BackgroundTasks):
    """
    Endpoint to sync a specific customer from Altru
    """
    logger.info("Received request to sync customer with Altru ID: {}", customer.altru_id)
    
    if not message_broker:
        raise HTTPException(status_code=503, detail="Message broker service is not available")
    
    # Use the message broker to publish a customer sync event
    background_tasks.add_task(
        message_broker.publish_message,
        'sync_queue',
        {
            'type': 'customer_sync',
            'altru_id': customer.altru_id
        }
    )
    
    return {
        "status": "accepted",
        "message": f"Customer sync scheduled for Altru ID: {customer.altru_id}"
    }

@app.post("/sync/events")
async def sync_events(sync_range: SyncRange, background_tasks: BackgroundTasks):
    """
    Endpoint to sync events from Altru
    """
    logger.info("Received request to sync events from {} to {}", sync_range.start_date, sync_range.end_date)
    
    if not message_broker:
        raise HTTPException(status_code=503, detail="Message broker service is not available")
    
    # Use the message broker to publish an event sync event
    background_tasks.add_task(
        message_broker.publish_message,
        'sync_queue',
        {
            'type': 'event_sync',
            'start_date': sync_range.start_date,
            'end_date': sync_range.end_date
        }
    )
    
    return {
        "status": "accepted",
        "message": "Events sync scheduled",
        "start_date": sync_range.start_date,
        "end_date": sync_range.end_date
    }

if __name__ == "__main__":
    uvicorn.run("API:app", host="0.0.0.0", port=8000, reload=True)
