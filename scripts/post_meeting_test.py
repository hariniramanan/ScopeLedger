import os

import requests
from dotenv import load_dotenv


load_dotenv()


API_URL = os.getenv(
    "SCOPELEDGER_API_URL"
)

WRITE_KEY = os.getenv(
    "SCOPELEDGER_WRITE_KEY"
)


if not API_URL:
    raise ValueError(
        "SCOPELEDGER_API_URL is missing."
    )


if not WRITE_KEY:
    raise ValueError(
        "SCOPELEDGER_WRITE_KEY is missing."
    )


meeting = {
    "title": "Website Redesign - Delivery Check",
    "meetingDate": "2026-08-18",
    "rawNotes": """
Meeting: Website Redesign - Delivery Check
Date: August 18, 2026

The client confirmed that the September 30 launch
deadline remains unchanged.

John confirmed that authentication is complete.

The client requested an analytics dashboard for
the initial release.

The analytics dashboard has not yet been approved.

Sarah estimated that the analytics dashboard could
require approximately four additional development days.
""".strip()
}


response = requests.post(
    f"{API_URL}/meetings",

    headers={
        "x-scopeledger-key":
            WRITE_KEY
    },

    json=meeting,

    timeout=20,
)


print(
    "HTTP status:",
    response.status_code
)

print()

print(
    "Response:"
)

print(
    response.json()
)