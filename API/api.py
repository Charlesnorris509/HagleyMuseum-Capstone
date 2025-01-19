from fastapi import FastAPI, HTTPException
from typing import List
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
    success = sync_service.sync_events(
        event_sync.start_date,
        event_sync.end_date
    )
    if not success:
        logger.error("Failed to sync events from {} to {}", event_sync.start_date, event_sync.end_date)
        raise HTTPException(status_code=400, detail="Failed to sync events")
    logger.info("Successfully synced events from {} to {}", event_sync.start_date, event_sync.end_date)
    return {"status": "success", "message": "Events synced successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check endpoint called")
    return {"status": "healthy"}
