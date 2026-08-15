import os

import requests
from dotenv import load_dotenv


load_dotenv()

api_url = os.getenv("SCOPELEDGER_API_URL")

if not api_url:
    raise ValueError(
        "SCOPELEDGER_API_URL was not found in .env"
    )


response = requests.get(
    f"{api_url}/memory",
    timeout=15
)

print("HTTP status:", response.status_code)
print()
print("Response:")
print(response.json())