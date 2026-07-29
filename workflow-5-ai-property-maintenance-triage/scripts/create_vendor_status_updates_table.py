"""One-off: create the Vendor Status Updates table via Airtable's Metadata
API -- the staging table vendors submit to via a public form, since forms
can only create records, not update the existing Maintenance Requests
record. A separate automation relays the update across (see the base's
Automations tab).

Reuses the same .env as provision_airtable_base.py (AIRTABLE_TOKEN,
AIRTABLE_BASE_ID). Run from the project root:
    python scripts/create_vendor_status_updates_table.py
"""

from __future__ import annotations

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["AIRTABLE_TOKEN"]
BASE_ID = os.environ["AIRTABLE_BASE_ID"]

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
TABLES_URL = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"


def main() -> int:
    response = httpx.post(TABLES_URL, headers=HEADERS, json={
        "name": "Vendor Status Updates",
        "fields": [
            {"name": "Request ID", "type": "number", "options": {"precision": 0}},
            {"name": "New Status", "type": "singleSelect", "options": {"choices": [
                {"name": "Scheduled"}, {"name": "Completed"},
            ]}},
            {"name": "Notes", "type": "multilineText"},
        ],
    }, timeout=30)

    if response.status_code >= 400:
        raise RuntimeError(f"Failed to create table: {response.status_code} {response.text}")

    table_id = response.json()["id"]
    print(f"Created table 'Vendor Status Updates' -> {table_id}")
    print("\nNext: build a Form view on this table in the Airtable UI (Request ID, New Status, Notes),")
    print("then add the automation that relays the update to Maintenance Requests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
