"""One-off: create sample vendor records for the specialties not yet
covered (only Plumbing exists from earlier manual testing) -- one vendor
per remaining specialty option, each linked to every property currently
in the base.

Uses Airtable's regular Data API (not the Metadata/schema API used by
provision_airtable_base.py) since this writes records, not schema -- no
computed-field restrictions to work around here.

Setup: same .env as provision_airtable_base.py (AIRTABLE_TOKEN,
AIRTABLE_BASE_ID), run from the project root:
    python scripts/seed_vendors.py
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


def get_all_property_ids() -> list[str]:
    response = httpx.get(f"https://api.airtable.com/v0/{BASE_ID}/Properties", headers=HEADERS, timeout=30)
    response.raise_for_status()
    return [record["id"] for record in response.json()["records"]]


def main() -> int:
    property_ids = get_all_property_ids()
    if not property_ids:
        print("No records found in Properties table -- add at least one property first.", file=sys.stderr)
        return 1
    print(f"Linking new vendors to {len(property_ids)} existing propert{'y' if len(property_ids) == 1 else 'ies'}.")

    vendors = [
        {"Vendor Name": "BrightSpark Electrical Co.", "Specialty": "Electrical",
         "Phone": "+1 555-330-2211", "Email": "dispatch@brightsparkelectrical.example.com"},
        {"Vendor Name": "ComfortZone HVAC Services", "Specialty": "HVAC",
         "Phone": "+1 555-440-7788", "Email": "service@comfortzonehvac.example.com"},
        {"Vendor Name": "Reliable Appliance Repair", "Specialty": "Appliance",
         "Phone": "+1 555-550-9922", "Email": "repairs@reliableappliance.example.com"},
        {"Vendor Name": "SolidBuild Contractors", "Specialty": "Structural",
         "Phone": "+1 555-660-4433", "Email": "jobs@solidbuildcontractors.example.com"},
        {"Vendor Name": "CritterGuard Pest Control", "Specialty": "Pest",
         "Phone": "+1 555-770-1155", "Email": "dispatch@critterguardpest.example.com"},
        {"Vendor Name": "Handy Property Services", "Specialty": "General",
         "Phone": "+1 555-880-6644", "Email": "requests@handypropertyservices.example.com"},
    ]

    records = [{"fields": {**v, "Assigned Properties": property_ids, "Active": True}} for v in vendors]

    response = httpx.post(
        f"https://api.airtable.com/v0/{BASE_ID}/Vendors",
        headers=HEADERS, json={"records": records}, timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Failed to create vendors: {response.status_code} {response.text}")

    for r in response.json()["records"]:
        print(f"Created vendor: {r['fields']['Vendor Name']} ({r['fields']['Specialty']}) -> {r['id']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
