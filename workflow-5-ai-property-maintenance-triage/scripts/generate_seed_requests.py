"""One-off: generate 150 synthetic Maintenance Requests rows, already
"classified" (no Claude API calls), for bulk-pasting into Airtable to
seed volume/history without spending on live classification.

Status distribution (fixed counts, then shuffled so they're not grouped
in sequential blocks): 70 Vendor Assigned, 30 Scheduled, 25 Completed,
20 Pending Review, 5 No Vendor Available.

Internal consistency rules mirrored from the real system:
- Pending Review -> Needs Human Review true, Urgency Emergency (or
  Urgent w/ low confidence), Assigned Vendor blank.
- No Vendor Available -> Needs Human Review false, Assigned Vendor blank.
- Vendor Assigned / Scheduled / Completed -> Needs Human Review false,
  Assigned Vendor set to the vendor matching Category, Urgency
  Routine/Urgent (never Emergency, since Emergency always trips review).

Output is tab-separated (out/seed_requests.tsv) -- Airtable's grid view
accepts a direct paste of tab-separated data, with linked-record columns
(Property, Assigned Vendor) auto-matching by the linked record's primary
field text, no record IDs needed.

Usage:
    python scripts/generate_seed_requests.py
"""

from __future__ import annotations

import random
from pathlib import Path

random.seed(42)  # reproducible output

OUT_PATH = Path("out/seed_requests.tsv")

PROPERTIES = [
    "Riverside Apartments", "Maple Grove Townhomes", "Harbor View Lofts",
    "Cedar Ridge Apartments", "Sunstone Commons",
]

VENDOR_BY_CATEGORY = {
    "Plumbing": "QuickFix Plumbing & Heating",
    "Electrical": "BrightSpark Electrical Co.",
    "HVAC": "ComfortZone HVAC Services",
    "Appliance": "Reliable Appliance Repair",
    "Structural": "SolidBuild Contractors",
    "Pest": "CritterGuard Pest Control",
    "General": "Handy Property Services",
    # "Other" has no dedicated vendor by design -- it's the genuine
    # catch-all for things that don't fit any specialty, distinct from
    # "General" (handyman-doable tasks Handy Property Services covers).
}
CATEGORIES = list(VENDOR_BY_CATEGORY.keys())

FIRST_NAMES = [
    "Sarah", "Marcus", "James", "Elena", "Grace", "Chloe", "Aisha", "Priya",
    "Diego", "Mateo", "Sofia", "Ethan", "Liam", "Nadia", "Owen", "Lily",
    "Derek", "Maya", "Isaac", "Felix", "Ella", "Tom", "Rachel", "Ben",
    "Carlos", "Whitney", "Aaron", "Jordan", "Nina", "Victor", "Hana", "Leo",
]
LAST_NAMES = [
    "Mitchell", "Webb", "Nguyen", "Reyes", "Santos", "Smith", "Khan", "Garcia",
    "Brown", "Okafor", "Rossi", "Novak", "Kim", "Ferris", "Brooks", "Park",
    "Cho", "Alston", "Torres", "Newman", "Liu", "Grant", "Sharma", "Whitfield",
    "Simmons", "Mendez", "Foster", "Blake", "Ellis", "Chen", "Patel", "Diaz",
]

# (description_template, category, urgency, confidence_range, is_emergency)
ROUTINE_ISSUES = [
    ("The kitchen faucet has a slow drip, not urgent but wanted to flag it", "Plumbing", "Routine", (0.85, 0.97)),
    ("Toilet keeps running after flushing, wastes a lot of water", "Plumbing", "Routine", (0.8, 0.95)),
    ("Bathroom sink is leaking under the cabinet, small puddle forming", "Plumbing", "Routine", (0.82, 0.95)),
    ("Shower drain is really slow, water pools around my feet", "Plumbing", "Urgent", (0.75, 0.9)),
    ("Ceiling fan in the living room stopped working, switch does nothing", "Electrical", "Routine", (0.85, 0.96)),
    ("One of the outlets in the bedroom doesn't work anymore", "Electrical", "Routine", (0.8, 0.94)),
    ("Light fixture in the hallway keeps flickering", "Electrical", "Routine", (0.75, 0.92)),
    ("Smoke detector keeps chirping, think the battery died", "Electrical", "Routine", (0.85, 0.97)),
    ("AC hasn't been cooling for two days now, it's really hot in here", "HVAC", "Urgent", (0.78, 0.93)),
    ("Heater is making a loud rattling noise when it kicks on", "HVAC", "Routine", (0.75, 0.9)),
    ("Thermostat display is blank, can't adjust the temperature", "HVAC", "Routine", (0.8, 0.94)),
    ("Vents are blowing warm air even though AC is set to cool", "HVAC", "Urgent", (0.75, 0.92)),
    ("Dishwasher won't drain, water just sits at the bottom", "Appliance", "Routine", (0.82, 0.95)),
    ("Refrigerator is making a loud buzzing sound, food isn't staying cold", "Appliance", "Urgent", (0.78, 0.93)),
    ("Washing machine won't spin, clothes come out soaking wet", "Appliance", "Routine", (0.8, 0.94)),
    ("Garbage disposal makes a horrible grinding noise and smells bad", "Appliance", "Routine", (0.78, 0.92)),
    ("Oven won't heat up past 200 degrees no matter what I set it to", "Appliance", "Routine", (0.8, 0.93)),
    ("Front door lock is sticking, takes forever to get in", "Structural", "Routine", (0.78, 0.92)),
    ("Window won't close all the way, cold air coming in", "Structural", "Routine", (0.8, 0.94)),
    ("Ceiling in the bathroom has a water stain that's getting bigger", "Structural", "Urgent", (0.75, 0.9)),
    ("Closet door fell off the track and won't slide anymore", "Structural", "Routine", (0.82, 0.95)),
    ("Bedroom carpet has a soft spot, feels like the subfloor is damaged", "Structural", "Urgent", (0.7, 0.88)),
    ("There's a swarm of ants in my kitchen near the pantry", "Pest", "Routine", (0.85, 0.96)),
    ("I've seen a couple mice in the past week, please help", "Pest", "Urgent", (0.78, 0.92)),
    ("Found a wasp nest forming near the balcony railing", "Pest", "Urgent", (0.8, 0.93)),
    ("Cockroaches showed up in the bathroom the last few nights", "Pest", "Urgent", (0.78, 0.92)),
    ("Mailbox key doesn't work anymore, can't get my mail", "General", "Routine", (0.8, 0.93)),
    ("Parking spot line markings have faded, hard to tell where to park", "General", "Routine", (0.82, 0.94)),
    ("Would like to request a replacement doormat, mine got worn out", "General", "Routine", (0.85, 0.96)),
]

# "Other" has no dedicated vendor -- used specifically for No Vendor
# Available rows below, genuinely hard-to-categorize requests.
OTHER_ISSUES = [
    ("Just wanted to say the new paint job looks great, no issues here", "Other", "Routine", (0.9, 0.98)),
    ("Neighbor's noise complaints keep coming up, not sure who to talk to about it", "Other", "Routine", (0.55, 0.7)),
    ("There's a strange musty smell in the storage closet, can't tell what's causing it", "Other", "Routine", (0.5, 0.68)),
    ("Package kept getting left outside instead of in the mailroom, not sure if that's on us or the carrier", "Other", "Routine", (0.55, 0.72)),
    ("Some kind of shared amenity billing question, not really a repair but wasn't sure where else to ask", "Other", "Routine", (0.5, 0.65)),
    ("Not sure if this is the right form, but wanted to flag an issue with the shared laundry room access code", "Other", "Routine", (0.55, 0.7)),
]

EMERGENCY_ISSUES = [
    ("I think there's a gas leak, I can smell it strongly near the stove, please send someone immediately", "Plumbing", 0.85),
    ("No hot water at all this morning, whole apartment, and I hear a hissing sound near the water heater", "Plumbing", 0.72),
    ("Outlet in my bedroom sparked when I plugged in my lamp, kind of scared to use it now", "Electrical", 0.8),
    ("I smell something burning near the electrical panel in the hallway closet", "Electrical", 0.78),
    ("Water is actively flooding from under the sink, it won't stop, please send someone now", "Plumbing", 0.88),
    ("Ceiling is sagging and dripping water, I'm worried it's going to collapse", "Structural", 0.65),
    ("This is the third time I've reported the elevator being broken, still not fixed, considering withholding rent", "Structural", 0.55),
    ("My smoke detector went off and there's a burning smell coming from the kitchen wall outlet", "Electrical", 0.7),
    ("Someone in the unit has a severe allergic reaction and we think it's from a pest treatment smell, need help now", "Pest", 0.6),
    ("The front door won't lock at all, anyone could just walk in, this feels unsafe", "Structural", 0.75),
]


def _tenant() -> tuple[str, str]:
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    email = name.lower().replace(" ", ".") + f"{random.randint(1, 99)}@example.com"
    return name, email


def _unit() -> str:
    return f"{random.randint(1, 12)}{random.choice(['A', 'B', 'C', 'D', ''])}"


def _row(status: str) -> dict:
    tenant, email = _tenant()
    property_ = random.choice(PROPERTIES)
    unit = _unit()

    if status == "Pending Review":
        desc, category, confidence = random.choice(EMERGENCY_ISSUES)
        urgency = "Emergency"
        needs_review = "checked"
        vendor = ""
    elif status == "No Vendor Available":
        desc, category, urgency, conf_range = random.choice(OTHER_ISSUES)
        confidence = round(random.uniform(*conf_range), 2)
        needs_review = ""
        vendor = ""
    else:
        desc, category, urgency, conf_range = random.choice(ROUTINE_ISSUES)
        confidence = round(random.uniform(*conf_range), 2)
        needs_review = ""
        vendor = VENDOR_BY_CATEGORY[category]

    summary = f"Tenant {tenant} in Unit {unit} reports: {desc[0].lower()}{desc[1:]}."

    return {
        "Tenant Name": tenant,
        "Property": property_,
        "Unit Number": unit,
        "Description": desc,
        "Submitted At": "",
        "Urgency": urgency,
        "Category": category,
        "AI Summary": summary,
        "AI Confidence": confidence,
        "Needs Human Review": needs_review,
        "Status": status,
        "Assigned Vendor": vendor,
        "Tenant Contact": email,
        "Notes": "",
    }


def main() -> int:
    statuses = (
        ["Vendor Assigned"] * 70
        + ["Scheduled"] * 30
        + ["Completed"] * 25
        + ["Pending Review"] * 20
        + ["No Vendor Available"] * 5
    )
    random.shuffle(statuses)

    rows = [_row(status) for status in statuses]

    columns = [
        "Tenant Name", "Property", "Unit Number", "Description", "Submitted At",
        "Urgency", "Category", "AI Summary", "AI Confidence", "Needs Human Review",
        "Status", "Assigned Vendor", "Tenant Contact", "Notes",
    ]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        f.write("\t".join(columns) + "\n")
        for row in rows:
            f.write("\t".join(str(row[col]) for col in columns) + "\n")

    print(f"Wrote {len(rows)} rows to {OUT_PATH}")
    counts = {s: statuses.count(s) for s in set(statuses)}
    for status, count in sorted(counts.items()):
        print(f"  {status}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
