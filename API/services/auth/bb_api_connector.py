import requests
import json
import os
from loguru import logger
from dotenv import load_dotenv
from .auth_service import AuthService

class BbApiConnector:
    """
    Blackbaud API Connector service that provides a session for API requests
    This service integrates with the AuthService for token management
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BbApiConnector, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, config_file_name='app_secrets.json'):
        if self.initialized:
            return
            
        load_dotenv()
        
        self.config_file_name = config_file_name
        self.auth_service = AuthService(config_file_name)
        
        # Load config for test endpoint
        if config_file_name.endswith('.ini'):
            from configparser import ConfigParser
            config = ConfigParser()
            config.read(os.path.join('API', 'resources', config_file_name))
            self.test_api_endpoint = config['other']['test_api_endpoint']
        else:
            with open(os.path.join('API', 'resources', config_file_name), 'r') as f:
                config = json.load(f)
            self.test_api_endpoint = config['other']['test_api_endpoint']
        
        self.session = None
        self.initialized = True

    def get_session(self):
        """
        Get an authenticated session for API requests
        The session includes proper headers and token refresh mechanism
        """
        logger.info("Creating API session")
        
        # Create session if it doesn't exist
        if not self.session:
            self.session = requests.Session()
        
        # Set headers with current token
        headers = self.auth_service.get_auth_headers()
        if not headers:
            logger.error("Failed to get authentication headers")
            return None
            
        self.session.headers.update(headers)
        
        # Test the session with a request
        self._validate_and_refresh_session()
        
        return self.session

    def _validate_and_refresh_session(self):
        """
        Validate session by making a test request
        If the token is expired, refresh it
        """
        if not self.session:
            logger.error("No session available to validate")
            return False
            
        try:
            logger.debug("Testing session with endpoint: {}", self.test_api_endpoint)
            test_result = self.session.get(self.test_api_endpoint)
            
            if test_result.status_code == 401:
                logger.info("401: Unauthorized. Refreshing access token...")
                refresh_result = self.auth_service.refresh_access_token()
                
                if refresh_result:
                    # Update session headers with new token
                    self.session.headers.update(self.auth_service.get_auth_headers())
                    return self._validate_and_refresh_session()
                else:
                    logger.error("Failed to refresh access token")
                    return False
                    
            elif test_result.status_code == 200:
                logger.info("200: Session is valid")
                return True
                
            else:
                logger.error(f"Unexpected status code: {test_result.status_code}")
                logger.error(f"Response: {test_result.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return False

    def make_request(self, method, url, **kwargs):
        """
        Make a request to the Blackbaud API with automatic token refresh
        """
        session = self.get_session()
        if not session:
            return None
            
        try:
            response = session.request(method, url, **kwargs)
            
            # Handle token expiration
            if response.status_code == 401:
                logger.info("401: Unauthorized. Refreshing access token...")
                refresh_result = self.auth_service.refresh_access_token()
                
                if refresh_result:
                    # Update session headers with new token and retry request
                    session.headers.update(self.auth_service.get_auth_headers())
                    return session.request(method, url, **kwargs)
                else:
                    logger.error("Failed to refresh access token")
                    return None
                    
            return response
            
        except Exception as e:
            logger.error(f"Error making request: {str(e)}")
            return None
            
    def get_constituent(self, altru_id):
        """Get constituent details from Blackbaud API"""
        url = f"https://api.sky.blackbaud.com/altru/v1/constituents/{altru_id}"
        response = self.make_request("GET", url)
        
        if response and response.status_code == 200:
            return response.json()
        return None
        
    def get_events(self, start_date, end_date):
        """Get events from Blackbaud API"""
        url = "https://api.sky.blackbaud.com/altru/v1/events"
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        response = self.make_request("GET", url, params=params)
        
        if response and response.status_code == 200:
            return response.json().get('value', [])
        return []
        
    def get_tickets(self, start_date, end_date):
        """Get ticket/wristband data from Blackbaud API"""
        url = "https://api.sky.blackbaud.com/altru/v1/registrants/tickets"
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        response = self.make_request("GET", url, params=params)
        
        if response and response.status_code == 200:
            return response.json().get('value', [])
        return []
        
    def get_parking_passes(self, start_date, end_date):
        """Get parking pass data from Blackbaud API"""
        url = "https://api.sky.blackbaud.com/altru/v1/parkingpasses"
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        response = self.make_request("GET", url, params=params)
        
        if response and response.status_code == 200:
            return response.json().get('value', [])
        return []