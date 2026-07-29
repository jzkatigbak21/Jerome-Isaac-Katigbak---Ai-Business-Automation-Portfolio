"""One-off: provision the property-management maintenance-triage Airtable
base via the API, instead of manually clicking through field types in the
UI. Run once against an empty base you've already created.

Creates the Maintenance Requests table only -- Properties and Vendors
already exist from an earlier run, and this script hardcodes their real
table IDs (PROPERTIES_ID / VENDORS_ID below) so it doesn't try to
recreate them.

Two field types Airtable's docs show example JSON for but the API
actually rejects creating (they're computed, UI-only): autoNumber and
createdTime -- confirmed live via a 422 UNSUPPORTED_FIELD_TYPE_FOR_CREATE
when the first attempt included a "Request ID" (autoNumber) and
"Submitted At" (createdTime) field. Both are dropped here; add them by
hand afterward in the Airtable UI (Autonumber and Created time field
types respectively) -- the UI allows them even though the API doesn't.
That also meant "Request ID" could no longer be the first field, since
it was acting as this table's primary field and autoNumber isn't a
valid primary field type via the API either -- Tenant Name is the
primary field now instead.

Setup:
    1. Create an empty base in Airtable (just the container, no tables).
    2. Get its Base ID from the URL (airtable.com/appXXXXXXXXXXXXXX/...)
       or from the API docs page for that base.
    3. Create a Personal Access Token at airtable.com/create/tokens with
       scope schema.bases:write, and give it access to this specific base.
    4. Put both in a .env file at the project root -- i.e.
       workflow-5-ai-property-maintenance-triage/.env, same convention as
       workflow-4 (never paste them into chat):
           AIRTABLE_TOKEN=pat...
           AIRTABLE_BASE_ID=app...
    5. pip install httpx python-dotenv
    6. Run from the project root (not from inside scripts/), same as
       workflow-4, so python-dotenv finds the .env file:
           cd workflow-5-ai-property-maintenance-triage
           python scripts/provision_airtable_base.py

Usage:
    python scripts/provision_airtable_base.py
"""

from __future__ import annotations

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["AIRTABLE_TOKEN"]
BASE_ID = os.environ["AIRTABLE_BASE_ID"]

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
TABLES_URL = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"

# Already created by the first run -- real IDs from that run's output.
PROPERTIES_ID = "tbl9Kb7ju4erFl78n"
VENDORS_ID = "tblWvK8TmKuj4BWL0"


def create_table(name: str, fields: list[dict]) -> str:
    response = httpx.post(TABLES_URL, headers=HEADERS, json={"name": name, "fields": fields}, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Failed to create table '{name}': {response.status_code} {response.text}")
    table_id = response.json()["id"]
    print(f"Created table '{name}' -> {table_id}")
    return table_id


def main() -> int:
    create_table("Maintenance Requests", [
        {"name": "Tenant Name", "type": "singleLineText"},
        {"name": "Property", "type": "multipleRecordLinks", "options": {"linkedTableId": PROPERTIES_ID}},
        {"name": "Unit Number", "type": "singleLineText"},
        {"name": "Description", "type": "multilineText"},
        {"name": "Urgency", "type": "singleSelect", "options": {"choices": [
            {"name": "Emergency"}, {"name": "Urgent"}, {"name": "Routine"},
        ]}},
        {"name": "Category", "type": "singleSelect", "options": {"choices": [
            {"name": "Plumbing"}, {"name": "Electrical"}, {"name": "HVAC"}, {"name": "Appliance"},
            {"name": "Structural"}, {"name": "Pest"}, {"name": "Other"},
        ]}},
        {"name": "AI Summary", "type": "multilineText"},
        {"name": "AI Confidence", "type": "number", "options": {"precision": 2}},
        {"name": "Needs Human Review", "type": "checkbox", "options": {"color": "redBright", "icon": "check"}},
        {"name": "Status", "type": "singleSelect", "options": {"choices": [
            {"name": "New"}, {"name": "Pending Review"}, {"name": "Vendor Assigned"},
            {"name": "Scheduled"}, {"name": "Completed"}, {"name": "Escalated"},
        ]}},
        {"name": "Assigned Vendor", "type": "multipleRecordLinks", "options": {"linkedTableId": VENDORS_ID}},
        {"name": "Tenant Contact", "type": "singleLineText"},
        {"name": "Notes", "type": "multilineText"},
    ])

    print("\nDone -- Maintenance Requests table created.")
    print("Now add these two fields by hand in the Airtable UI (the API can't create them):")
    print('  - "Request ID"   -> field type: Autonumber')
    print('  - "Submitted At" -> field type: Created time')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
