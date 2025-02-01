from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from data_sync import DataSyncService
from loguru import logger

app = FastAPI()
sync_service = DataSyncService()

class CustomerSync(BaseModel):
    altru_id: str

class EventSync(BaseModel):
    start_date: str
    end_date: str

class SyncRange(BaseModel):
    start_date: str
    end_date: str

@app.post("/sync/customer")
async def sync_customer(customer: CustomerSync):
    """Endpoint to sync customer data from Altru"""
    logger.info("Received request to sync customer with Altru ID: {}", customer.altru_id)
    success = sync_service.sync_customer(customer.altru_id)
    if not success:
        logger.error("Failed to sync customer with Altru ID: {}", customer.altru_id)
        raise HTTPException(status_code=400, detail="Failed to sync customer")
    logger.info("Successfully synced customer with Altru ID: {}", customer.altru_id)
    return {"status": "success", "message": "Customer synced successfully"}

@app.post("/sync/events")
async def sync_events(event_sync: EventSync):
    """Endpoint to sync events data from Altru"""
    logger.info("Received request to sync events from {} to {}", event_sync.start_date, event_sync.end_date)
    success = sync_service.sync_events(event_sync.start_date, event_sync.end_date)
    if not success:
        logger.error("Failed to sync events from {} to {}", event_sync.start_date, event_sync.end_date)
        raise HTTPException(status_code=400, detail="Failed to sync events")
    logger.info("Successfully synced events from {} to {}", event_sync.start_date, event_sync.end_date)
    return {"status": "success", "message": "Events synced successfully"}

@app.post("/sync/wristbands")
async def sync_wristbands(sync_range: SyncRange):
    """Endpoint to sync wristband/ticket data from Altru"""
    logger.info("Received request to sync wristbands from {} to {}", sync_range.start_date, sync_range.end_date)
    success = sync_service.sync_wristbands(sync_range.start_date, sync_range.end_date)
    if not success:
        logger.error("Failed to sync wristbands from {} to {}", sync_range.start_date, sync_range.end_date)
        raise HTTPException(status_code=400, detail="Failed to sync wristbands")
    logger.info("Successfully synced wristbands from {} to {}", sync_range.start_date, sync_range.end_date)
    return {"status": "success", "message": "Wristbands synced successfully"}

@app.post("/sync/parkingpasses")
async def sync_parking_passes(sync_range: SyncRange):
    """Endpoint to sync parking passes from Altru"""
    logger.info("Received request to sync parking passes from {} to {}", sync_range.start_date, sync_range.end_date)
    success = sync_service.sync_parking_passes(sync_range.start_date, sync_range.end_date)
    if not success:
        logger.error("Failed to sync parking passes from {} to {}", sync_range.start_date, sync_range.end_date)
        raise HTTPException(status_code=400, detail="Failed to sync parking passes")
    logger.info("Successfully synced parking passes from {} to {}", sync_range.start_date, sync_range.end_date)
    return {"status": "success", "message": "Parking passes synced successfully"}
