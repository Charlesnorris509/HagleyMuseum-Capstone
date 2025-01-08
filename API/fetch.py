// Retrieve customer data to populate the Customers table.
def fetch_constituents(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://api.sky.blackbaud.com/constituent/v1/constituents', headers=headers)
    return response.json().get('value', [])


//  Retrieve event data to populate the Events table.
def fetch_events(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://api.sky.blackbaud.com/event/v1/events', headers=headers)
    return response.json().get('value', [])
