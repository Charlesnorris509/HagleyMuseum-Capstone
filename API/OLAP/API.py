from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from data_sync import DataSyncService
from loguru import logger

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    global sync_service
    sync_service = DataSyncService()  # Initialize the sync service at startup

class SyncRange(BaseModel):
    start_date: str
    end_date: str

@app.post("/sync/all")
async def sync_all(sync_range: SyncRange):
    """Endpoint to sync all data from Altru"""
    logger.info("Received request to sync all data from {} to {}", sync_range.start_date, sync_range.end_date)

    # Sync customer data
    altru_id = "example_altru_id"
    if not sync_service.sync_customer(altru_id):
        logger.error("Failed to sync customer with Altru ID: {}", altru_id)
        raise HTTPException(status_code=400, detail="Failed to sync customer")

    # Sync events data
    if not sync_service.sync_events(sync_range.start_date, sync_range.end_date):
        logger.error("Failed to sync events from {} to {}", sync_range.start_date, sync_range.end_date)
        raise HTTPException(status_code=400, detail="Failed to sync events")

    # Sync wristbands data
    if not sync_service.sync_wristbands(sync_range.start_date, sync_range.end_date):
        logger.error("Failed to sync wristbands from {} to {}", sync_range.start_date, sync_range.end_date)
        raise HTTPException(status_code=400, detail="Failed to sync wristbands")

    # Sync parking passes data
    if not sync_service.sync_parking_passes(sync_range.start_date, sync_range.end_date):
        logger.error("Failed to sync parking passes from {} to {}", sync_range.start_date, sync_range.end_date)
        raise HTTPException(status_code=400, detail="Failed to sync parking passes")

    logger.info("Successfully synced all data from {} to {}", sync_range.start_date, sync_range.end_date)
    return {"status": "success", "message": "All data synced successfully"}
