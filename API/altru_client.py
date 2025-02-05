import requests
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

class AltruAPIClient:
    def __init__(self):
        self.base_url = "https://api.sky.blackbaud.com/altru/v1"
        self.subscription_key = os.getenv('BLACKBAUD_SUBSCRIPTION_KEY')
        self.access_token = None

        # Check if the subscription key is set
        if not self.subscription_key:
            logger.error("BLACKBAUD_SUBSCRIPTION_KEY is not set in the environment variables.")
            raise ValueError("BLACKBAUD_SUBSCRIPTION_KEY is not set in the environment variables.")

    def authenticate(self):
        """Authenticate with Blackbaud OAuth2"""
        auth_url = "https://oauth2.sky.blackbaud.com/token"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': os.getenv('BLACKBAUD_CLIENT_ID'),
            'client_secret': os.getenv('BLACKBAUD_CLIENT_SECRET')
        }

        # Check if client_id and client_secret are set
        if not payload['client_id'] or not payload['client_secret']:
            logger.error("BLACKBAUD_CLIENT_ID or BLACKBAUD_CLIENT_SECRET is not set in the environment variables.")
            raise ValueError("BLACKBAUD_CLIENT_ID or BLACKBAUD_CLIENT_SECRET is not set in the environment variables.")

        response = requests.post(auth_url, data=payload)
        if response.status_code == 200:
            self.access_token = response.json().get('access_token')
            logger.info("Authentication successful")
            return True
        logger.error("Authentication failed: {}", response.text)
        return False

    def get_headers(self) -> Dict:
        """Get headers for API requests"""
        # Ensure access token is set before generating headers
        if not self.access_token:
            logger.error("Access token is not set. Please authenticate first.")
            raise ValueError("Access token is not set. Please authenticate first.")
        return {
            'Bb-Api-Subscription-Key': self.subscription_key,
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def get_constituent(self, altru_id: str) -> Dict:
        """Get constituent details from Altru"""
        endpoint = f"/constituents/{altru_id}"
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.get_headers()
        )
        if response.status_code == 200:
            logger.info("Fetched constituent details for ID: {}", altru_id)
            return response.json()
        logger.error("Failed to fetch constituent details for ID: {}", altru_id)
        return None

    def get_events(self, start_date: str, end_date: str) -> List[Dict]:
        """Get events from Altru"""
        endpoint = "/events"
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.get_headers(),
            params=params
        )
        if response.status_code == 200:
            logger.info("Fetched events from {} to {}", start_date, end_date)
            return response.json().get('value', [])
        logger.error("Failed to fetch events from {} to {}", start_date, end_date)
        return []

    def get_tickets(self, start_date: str, end_date: str) -> List[Dict]:
        """Fetch a list of ticket or wristband sales from Altru within a date range."""
        endpoint = "/registrants/tickets"
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.get_headers(),
            params=params
        )
        if response.status_code == 200:
            logger.info("Fetched ticket/wristband data from {} to {}", start_date, end_date)
            return response.json().get('value', [])
        logger.error("Failed to fetch ticket/wristband data: {}", response.text)
        return []

    def get_parking_passes(self, start_date: str, end_date: str) -> List[Dict]:
        """Fetch a list of parking passes from Altru within a date range."""
        endpoint = "/parkingpasses"
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.get_headers(),
            params=params
        )
        if response.status_code == 200:
            logger.info("Fetched parking passes from {} to {}", start_date, end_date)
            return response.json().get('value', [])
        logger.error("Failed to fetch parking passes: {}", response.text)
        return []
