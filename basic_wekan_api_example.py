import json
import os
from dotenv import load_dotenv
import requests

# Basic example of authenticating and making an API call to Wekan
# - https://wekan.fi/api/v7.93/#wekan-rest-api

# Replace with your Wekan instance and credentials
load_dotenv()  # Loads variables from .env into environment
load_dotenv(dotenv_path=".secrets.env")  # Loads secrets from .secrets.env into environment
base_url = os.getenv('WEKAN_URL')
username = os.getenv('WEKAN_USERNAME')
password = os.getenv('WEKAN_PASSWORD')

# Get auth token
headers = {
    'Content-Type': 'application/json',
    'Accept': '*/*'
    }
login = requests.post(
    f"{base_url}/users/login",
    json={"username": username, "password": password},
    headers=headers
)
token = login.json()["token"]

# Check if login was successful
if not token:
    print("Login failed:", login.json())
    exit(1)
else:
    print("Login successful as", username)
    print("Auth token:", f'Bearer {token}')

headers = {
  'Accept': 'application/json',
  'Authorization': f'Bearer {token}'
}

# Make an authenticated GET request
r = requests.get(f"{base_url}/api/boards_count", params={}, headers=headers)

try:
    print(r.json())
except json.JSONDecodeError:
    if r.status_code in (200, 201, 204) and not r.text:
        print("Answer was empty") # Return empty dict for success with no content
    if r.status_code == 500:
        print('ERROR')