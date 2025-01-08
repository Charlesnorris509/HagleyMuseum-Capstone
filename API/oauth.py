import requests
from requests.auth import HTTPBasicAuth

TOKEN_URL = 'https://oauth2.sky.blackbaud.com/token'
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
REDIRECT_URI = 'your_redirect_uri'
AUTH_CODE = 'authorization_code_obtained_from_blackbaud'

def get_access_token():
    response = requests.post(
        TOKEN_URL,
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        data={
            'grant_type': 'authorization_code',
            'code': AUTH_CODE,
            'redirect_uri': REDIRECT_URI
        }
    )
    return response.json().get('access_token')
