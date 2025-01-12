from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel
from datetime import datetime
from data_sync import DataSyncService

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
    success = sync_service.sync_customer(customer.altru_id)
    if not success:
        raise HTTPException(status_code=400, message="Failed to sync customer")
    return {"status": "success", "message": "Customer synced successfully"}

@app.post("/sync/events")
async def sync_events(event_sync: EventSync):
    """Endpoint to sync events data from Altru"""
    success = sync_service.sync_events(
        event_sync.start_date,
        event_sync.end_date
    )
    if not success:
        raise HTTPException(status_code=400, message="Failed to sync events")
    return {"status": "success", "message": "Events synced successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
