import requests
from configparser import ConfigParser
import json
import os
from loguru import logger
from dotenv import load_dotenv

class AuthService:
    """
    Authentication Service for Blackbaud SKY API
    Responsible for handling OAuth 2.0 authentication flow and token management
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthService, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, config_file_name='app_secrets.ini'):
        if self.initialized:
            return
        
        load_dotenv()
        
        # Support both .ini and .json config files
        if config_file_name.endswith('.ini'):
            self.config = ConfigParser()
            self.config.read(os.path.join('API', 'resources', config_file_name))
            self.token_uri = 'https://oauth2.sky.blackbaud.com/token'
            self.auth_uri = 'https://oauth2.sky.blackbaud.com/authorization'
            self.redirect_uri = self.config['other']['redirect_uri']
            self.app_id = self.config['app_secrets']['app_id']
            self.app_secret = self.config['app_secrets']['app_secret']
            self.api_subscription_key = self.config['other']['api_subscription_key']
        else:
            with open(os.path.join('API', 'resources', config_file_name), 'r') as f:
                self.config = json.load(f)
            self.token_uri = 'https://oauth2.sky.blackbaud.com/token'
            self.auth_uri = 'https://oauth2.sky.blackbaud.com/authorization'
            self.redirect_uri = self.config['other']['redirect_uri']
            self.app_id = self.config['sky_app_information']['app_id']
            self.app_secret = self.config['sky_app_information']['app_secret']
            self.api_subscription_key = self.config['other']['api_subscription_key']
            
        self.tokens = {
            'access_token': None,
            'refresh_token': None
        }
        
        # Load tokens from environment if available, otherwise from config
        self.tokens['access_token'] = os.getenv('BLACKBAUD_ACCESS_TOKEN') or self._get_token_from_config('access_token')
        self.tokens['refresh_token'] = os.getenv('BLACKBAUD_REFRESH_TOKEN') or self._get_token_from_config('refresh_token')
        
        self.initialized = True

    def _get_token_from_config(self, token_type):
        """Get token from config based on file type"""
        if isinstance(self.config, ConfigParser):
            return self.config['tokens'][token_type]
        else:
            return self.config['tokens'][token_type]

    def get_authorization_url(self):
        """Generate the authorization URL for the OAuth flow"""
        auth_url = f"{self.auth_uri}?client_id={self.app_id}&response_type=code&redirect_uri={self.redirect_uri}"
        return auth_url

    def get_access_refresh_tokens(self, auth_code):
        """Exchange authorization code for access and refresh tokens"""
        logger.info("Exchanging authorization code for tokens")
        params = {
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'code': auth_code,
            'client_id': self.app_id,
            'client_secret': self.app_secret
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(self.token_uri, data=params, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200:
                logger.info("Successfully obtained tokens")
                self.tokens['access_token'] = response_data.get('access_token')
                self.tokens['refresh_token'] = response_data.get('refresh_token')
                self._update_token_storage()
                return response_data
            else:
                logger.error(f"Failed to get tokens: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting tokens: {str(e)}")
            return None

    def refresh_access_token(self):
        """Refresh the access token using the refresh token"""
        logger.info("Refreshing access token")
        if not self.tokens['refresh_token']:
            logger.error("No refresh token available")
            return None
            
        params = {
            'grant_type': 'refresh_token',
            'refresh_token': self.tokens['refresh_token'],
            'client_id': self.app_id,
            'client_secret': self.app_secret
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(self.token_uri, data=params, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200:
                logger.info("Successfully refreshed tokens")
                self.tokens['access_token'] = response_data.get('access_token')
                # Some OAuth implementations also refresh the refresh token
                if 'refresh_token' in response_data:
                    self.tokens['refresh_token'] = response_data.get('refresh_token')
                self._update_token_storage()
                return response_data
            else:
                logger.error(f"Failed to refresh token: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None

    def _update_token_storage(self):
        """Update token storage in config file"""
        if isinstance(self.config, ConfigParser):
            self.config['tokens']['access_token'] = self.tokens['access_token']
            self.config['tokens']['refresh_token'] = self.tokens['refresh_token']
            with open(os.path.join('API', 'resources', 'app_secrets.ini'), 'w') as f:
                self.config.write(f)
        else:
            self.config['tokens']['access_token'] = self.tokens['access_token']
            self.config['tokens']['refresh_token'] = self.tokens['refresh_token']
            with open(os.path.join('API', 'resources', 'app_secrets.json'), 'w') as f:
                json.dump(self.config, f, indent=4)
                
    def get_auth_headers(self):
        """Get authorization headers for API requests"""
        if not self.tokens['access_token']:
            logger.error("No access token available")
            return None
            
        return {
            'Bb-Api-Subscription-Key': self.api_subscription_key,
            'Authorization': f"Bearer {self.tokens['access_token']}"
        }