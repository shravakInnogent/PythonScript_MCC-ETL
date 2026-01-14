import os
import time
import json
import base64
import requests
import logging
import csv
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
import re

from config import (
    QB_CLIENT_ID,
    QB_CLIENT_SECRET,
    QB_BASE_URL,
    QB_TOKEN_URL,
    QB_REALM_ID
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_column_name(key):

    # Using regex with word boundaries to match only complete abbreviations
    replacements = [
        (r'Addr(?![a-z])', 'Address'),
        (r'Ref(?![a-z])', 'Reference'),
        (r'Desc(?![a-z])', 'Description'),
        (r'Amt(?![a-z])', 'Amount'),
        (r'Acct(?![a-z])', 'Account'),
        (r'Curr(?![a-z])', 'Currency'),
        (r'Pmt(?![a-z])', 'Payment'),
        (r'Inv(?![a-z])', 'Invoice'),
        (r'Emp(?![a-z])', 'Employee'),
        (r'Cust(?![a-z])', 'Customer'),
        (r'Tel(?![a-z])', 'Telephone'),
        (r'Txn(?![a-z])', 'Transaction'),
        (r'Num(?![a-z])', 'Number')
    ]

    result = key
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result)

    # Add underscores before capitals (but not if underscore already exists)
    result = re.sub(r'(?<!_)(?=[A-Z])', '_', result)

    # Remove leading underscore if it exists
    if result.startswith('_'):
        result = result[1:]

    return result

#It converts nested dictionary into flat dictionary
def flatten_dict(d, parent_key='', sep='_'):
    items = []
    #iterate each key-value pair
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def display_table_and_save_csv(data, entity_type):
    if not data:
        print("No data to display")
        return
    flattened_data = [flatten_dict(record) for record in data]

    all_keys = set()
    for record in flattened_data:
        all_keys.update(record.keys())
    all_keys = sorted(list(all_keys))

    key_mapping = {key: format_column_name(key) for key in all_keys}
    formatted_headers = list(key_mapping.values())

    transformed_data = []
    for record in flattened_data:
        new_record  = {key_mapping[k]: v for k, v in record.items()}
        transformed_data.append(new_record)

    display_data = transformed_data[:100]
    table_data = []
    for record in display_data:
        row = [str(record.get(key, '')) if record.get(key) is not None else '' for key in formatted_headers]
        table_data.append(row)

    print(tabulate(table_data, headers=formatted_headers, tablefmt="simple"))
    
    save_dir = Path.home() / "Library" / "CloudStorage" / "OneDrive-Personal" / "QB_CSV_Files"
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{entity_type.lower()}_{timestamp}.csv"
    file_path = save_dir / filename
    
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=formatted_headers)
        writer.writeheader()
        writer.writerows(transformed_data)
    
    print(f"\nData saved to: {file_path}")
    print(f"Total records: {len(data)}")

def get_token_path():
    path = Path.home() / ".quickbooks_app"
    path.mkdir(mode=0o700, exist_ok=True)
    return path / "tokens.json"

def load_tokens():
    token_file = get_token_path()
    if not token_file.exists():
        raise FileNotFoundError("QuickBooks tokens not found")
    with open(token_file) as f:
        return json.load(f)

def save_tokens(tokens):
    token_file = get_token_path()
    with open(token_file, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(token_file, 0o600)

def refresh_access_token(refresh_token):
    auth = base64.b64encode(
        f"{QB_CLIENT_ID}:{QB_CLIENT_SECRET}".encode()
    ).decode()

    response = requests.post(
        QB_TOKEN_URL,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
    )

    if response.status_code != 200:
        raise Exception(f"Refresh failed: {response.text}")

    data = response.json()
    data["expires_at"] = int(time.time()) + data["expires_in"]
    save_tokens(data)
    return data

def get_access_token():
    tokens = load_tokens()

    if time.time() > tokens["expires_at"] - 300:
        logger.info("Refreshing QuickBooks access token")
        tokens = refresh_access_token(tokens["refresh_token"])

    return tokens["access_token"]

def qb_request(method, endpoint, params=None, data=None, max_retries=5):
    for attempt in range(max_retries + 1):
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        if data:
            headers["Content-Type"] = "application/json"
        
        url = f"{QB_BASE_URL}{endpoint}"
        
        response = requests.request(method, url, headers=headers, params=params, json=data)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning(f"Rate limit hit. Waiting {retry_after}s")
            time.sleep(retry_after)
            continue

        if response.status_code == 401 and attempt == 0:
            logger.warning("401 Unauthorized. Refreshing token...")
            refresh_access_token(load_tokens()["refresh_token"])
            continue

        if response.status_code in (500, 503) and attempt < max_retries:
            wait = 2 ** attempt
            logger.warning(f"Server error {response.status_code}. Retrying in {wait}s")
            time.sleep(wait)
            continue

        if response.status_code == 400:
            logger.error(f"Bad Request: {response.text}")
            raise Exception("Invalid QuickBooks request")

        response.raise_for_status()
        return response.json()
    
    raise Exception(f"Max retries ({max_retries}) exceeded")

def get_api_type():
    print("\nQuickBooks API Options:")
    print("1. Run Query (SQL-like queries)")
    print("2. Complete Endpoint (Full URL path)")
    
    choice = input("Select option (1-2): ").strip()
    return choice

def handle_query_api():
    method = input("Enter HTTP method (GET/POST/PUT/DELETE): ").strip().upper()
    query = input("Enter complete SQL query: ").strip()
    
    response = qb_request(
        method,
        f"/v3/company/{QB_REALM_ID}/query",
        params={"query": query}
    )

    entity = "query_result"
    if "FROM" in query.upper():
        parts = query.upper().split("FROM")
        if len(parts) > 1:
            entity = parts[1].strip().split()[0]

    records = []
    if "QueryResponse" in response:
        for key, value in response["QueryResponse"].items():
            if isinstance(value, list):
                records.extend(value)
    
    return records, entity

def handle_custom_api():
    endpoint = input("Enter complete endpoint: ").strip()
    endpoint = endpoint.replace("{realm_id}", QB_REALM_ID)
    
    method = input("Enter HTTP method (GET/POST/PUT/DELETE): ").strip().upper()
    
    response = qb_request(method, endpoint)

    if isinstance(response, dict):
        for key, value in response.items():
            if isinstance(value, list) and value:
                return value, key
            elif isinstance(value, dict):
                return [value], key
    
    return [response], "custom"


def main():
    try:
        api_type = get_api_type()
        
        if api_type == "1":
            data, entity_name = handle_query_api()
        elif api_type == "2":
            data, entity_name = handle_custom_api()
        else:
            print("Invalid choice")
            return

        if data:
            display_table_and_save_csv(data, entity_name)
        else:
            print("No data found")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
