# altru_client.py
import requests
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

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
            return True
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
        return response.json() if response.status_code == 200 else None

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
        return response.json()['value'] if response.status_code == 200 else []

    def get_employee(self, employee_id: str) -> Dict:
        """Get employee details from Altru"""
        endpoint = f"/employees/{employee_id}"
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else None
