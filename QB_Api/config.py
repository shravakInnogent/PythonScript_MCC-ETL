import os
from dotenv import load_dotenv

load_dotenv()

QB_CLIENT_ID = os.getenv("QB_CLIENT_ID")
QB_CLIENT_SECRET = os.getenv("QB_CLIENT_SECRET")
QB_REALM_ID = os.getenv("QB_REALM_ID")
QB_ENV = os.getenv("QB_ENV", "sandbox")

if not all([QB_CLIENT_ID, QB_CLIENT_SECRET, QB_REALM_ID]):
    raise ValueError("Missing required environment variables: QB_CLIENT_ID, QB_CLIENT_SECRET, QB_REALM_ID")

QB_BASE_URL = (
    "https://sandbox-quickbooks.api.intuit.com"
    if QB_ENV == "sandbox"
    else "https://quickbooks.api.intuit.com"
)

QB_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"