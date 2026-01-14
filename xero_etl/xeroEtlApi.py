import os
import requests
import base64
import time
import json
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from config import XERO_BASE_URL, XERO_CLIENT_ID, XERO_CLIENT_SECRET

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_secure_token_path():
    """Store tokens in user's secure directory"""
    secure_dir = Path.home() / ".xero_app"
    secure_dir.mkdir(mode=0o700, exist_ok=True)
    return secure_dir / "tokens.json"


TOKEN_URL = "https://identity.xero.com/connect/token"
CONNECTIONS_URL = "https://api.xero.com/connections"
CLIENT_ID = XERO_CLIENT_ID
CLIENT_SECRET = XERO_CLIENT_SECRET

class XeroAPIError(Exception):
    """Custom exception for Xero API errors"""
    pass

class XeroConnectionError(Exception):
    """Custom exception for Xero connection errors"""
    pass

def load_tokens():
    token_file = get_secure_token_path()
    try:
        with open(token_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Token file not found at {token_file}. Please ensure tokens are saved.")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in token file")

def save_tokens(tokens):
    token_file = get_secure_token_path()
    with open(token_file, "w") as f:
        json.dump(tokens, f, indent=2)
    # Set restrictive permissions - only user can read/write
    os.chmod(token_file, 0o600)
    logger.info(f"Tokens saved securely to {token_file}")

def refresh_access_tokens(refresh_token):
    auth = base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    ).decode()

    response = requests.post(TOKEN_URL,
                             headers={"Authorization": f"Basic {auth}",
                             "Content-Type": "application/x-www-form-urlencoded"
                                      },
                             data={"grant_type": "refresh_token",
                                   "refresh_token": refresh_token
                                   }
                             )
    if response.status_code == 429:
        wait = int(response.headers.get("Retry-After", 60))
        logger.warning(f"Rate limited. Waiting {wait} seconds...")
        time.sleep(wait)
        return refresh_access_tokens(refresh_token)

    if response.status_code != 200:
        logger.error(f"Refresh token failed with status: {response.status_code}")
        raise XeroAPIError(f"Refresh token failed: {response.status_code}")

    data = response.json()
    data["expires_at"] = int(time.time()) + data["expires_in"]
    save_tokens(data)
    return data

def get_access_token():
    tokens = load_tokens()
    if time.time() < tokens["expires_at"] - 300:
        return tokens["access_token"]

    logger.info("Refreshing access token...")
    new_tokens = refresh_access_tokens(tokens["refresh_token"])
    return new_tokens["access_token"]

def get_tenant_id(access_token):
    response = requests.get(
        CONNECTIONS_URL,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()
    connections = response.json()
    if not connections:
        raise XeroConnectionError("No Xero connections found")
    return connections[1]["tenantId"]

def fetch_xero_api(endpoint, access_token, tenant_id, params=None):
    offset  = 0
    all_items = []
    max_iteration  = 1000
    iteration = 0

    while iteration < max_iteration:
        url = f"{XERO_BASE_URL}/{endpoint}"

        current_params = params.copy()  if params else {}
        if endpoint.lower() == 'journals':
            current_params['offset'] = offset
        else:
            current_params['page'] = (offset//100) + 1

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Xero-tenant-id": tenant_id,
            "Accept": "application/json"
         }

        response = requests.get(url, headers=headers, params=current_params)

        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 60))
            logger.warning(f"Rate limited. Waiting {wait} seconds...")
            time.sleep(wait)
            continue

        response.raise_for_status()
        data = response.json()
        items = data.get(endpoint, [])

        if not items or len(items) == 0:
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        offset += len(items)
        iteration +=1
    if iteration >= max_iteration:
        logger.warning(f"Reached maximum iterations ({max_iteration}). Stopping fetch.")
    return {endpoint: all_items}

def get_safe_onedrive_path():
    possible_paths = [
        Path.home() / "OneDrive",
        Path.home() / "Library" / "CloudStorage" / "OneDrive-Personal"
    ]
    
    for path in possible_paths:
        if path.exists():
            return path

    logger.warning("OneDrive not found. Saving to current directory.")
    return Path(".")

def save_to_csv(data, endpoint):

    items = data.get(endpoint, [])
    if not items:
        logger.info(f"No data found for {endpoint}")
        return
    

    base_path = get_safe_onedrive_path()
    xero_folder = base_path / "Xero_Data"
    xero_folder.mkdir(exist_ok=True)


    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{endpoint}_{timestamp}.csv"
    filepath = xero_folder / filename


    df = pd.DataFrame(items)
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(items)} {endpoint} records to: {filepath}")

def display_data(data, endpoint):
    items = data.get(endpoint, [])
    if not items:
        logger.info(f"No data found for {endpoint}")
        return
    
    df = pd.DataFrame(items)
    print(f"\n{endpoint} Data:")
    print("=" * 50)
    print(df.to_string(index=False))

def process_endpoint_data(endpoint, access_token, tenant_id):
    try:
        fetched_data = fetch_xero_api(endpoint, access_token, tenant_id)
        display_data(fetched_data, endpoint)
        save_to_csv(fetched_data, endpoint)
    except Exception as e:
        logger.error(f"Error processing {endpoint}: {str(e)}")

def main():
    try:
        print("Available Xero endpoints: Journals, Invoices, Contacts, Items, Accounts, BankTransactions, etc.")
        endpoint = input("Enter endpoint to fetch (default: Invoices): ").strip()
        

        if not endpoint:
            endpoint = "Invoices"
        
        access_token = get_access_token()
        tenant_id = get_tenant_id(access_token)
        process_endpoint_data(endpoint, access_token, tenant_id)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    main()