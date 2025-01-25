# altru_client.py
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

    def authenticate(self):
        """Authenticate with Blackbaud OAuth2"""
        auth_url = "https://oauth2.sky.blackbaud.com/token"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': os.getenv('BLACKBAUD_CLIENT_ID'),
            'client_secret': os.getenv('BLACKBAUD_CLIENT_SECRET')
        }
        
        response = requests.post(auth_url, data=payload)
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
            logger.info("Authentication successful")
            return True
        logger.error("Authentication failed: {}", response.text)
        return False

    def get_headers(self) -> Dict:
        """Get headers for API requests"""
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
            return response.json()['value']
        logger.error("Failed to fetch events from {} to {}", start_date, end_date)
        return []

    def get_employee(self, employee_id: str) -> Dict:
        """Get employee details from Altru"""
        endpoint = f"/employees/{employee_id}"
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.get_headers()
        )
        if response.status_code == 200:
            logger.info("Fetched employee details for ID: {}", employee_id)
            return response.json()
        logger.error("Failed to fetch employee details for ID: {}", employee_id)
        return None

    def get_tickets(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch a list of ticket or wristband sales from Altru within a date range.
        Adjust the endpoint and parameters as needed for your Altru environment.
        """
        endpoint = "/path/to/tickets/or/passes"
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
            logger.info("Fetched ticket/wristband data for {} to {}", start_date, end_date)
            return response.json().get('value', [])
        logger.error("Failed to fetch ticket/wristband data: {}", response.text)
        return []

    def get_parking_passes(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch a list of parking passes from Altru within a date range.
        Adjust endpoint and parameters to match your Altru configuration.
        """
        endpoint = "/path/to/parkingpasses"
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
            logger.info("Fetched parking pass data for {} to {}", start_date, end_date)
            return response.json().get('value', [])
        logger.error("Failed to fetch parking pass data: {}", response.text)
        return []
