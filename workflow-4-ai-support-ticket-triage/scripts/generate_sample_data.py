"""
Generates a synthetic batch of DTC support tickets / reviews for local
testing of the triage pipeline, without needing a live Gorgias/Shopify export.

Usage:
    python scripts/generate_sample_data.py --rows 300 --out data/sample_tickets.csv
"""

import argparse
import csv
import random
from pathlib import Path

FIRST_NAMES = [
    "Maria", "James", "Aisha", "Liam", "Sofia", "Noah", "Elena", "Mateo",
    "Grace", "Diego", "Priya", "Ethan", "Chloe", "Kenji", "Amara", "Lucas",
]
LAST_NAMES = [
    "Reyes", "Smith", "Khan", "Garcia", "Novak", "Cruz", "Kim", "Patel",
    "Dela Cruz", "Rossi", "Okafor", "Nguyen", "Santos", "Brown", "Lopez",
]
PRODUCTS = [
    "Everyday Tote", "Trail Runner Sneakers", "Ceramic Pour-Over Kettle",
    "Weighted Blanket", "Bamboo Cutting Board Set", "Wireless Earbuds Pro",
    "Linen Bedsheet Set", "Insulated Water Bottle", "Standing Desk Mat",
    "Cast Iron Skillet",
]

TEMPLATES = [
    # (category, urgency, sentiment, text_template)
    ("shipping", "high", "negative",
     "It's been {days} days and my order #{order} still shows 'label created'. I needed the {product} for a trip this weekend. What is going on?"),
    ("shipping", "medium", "negative",
     "Tracking for order #{order} hasn't updated in {days} days. Can someone check on the {product}?"),
    ("defect", "high", "negative",
     "The {product} I received (order #{order}) arrived broken/cracked. This is unacceptable for the price. I want a replacement or refund."),
    ("defect", "medium", "negative",
     "My {product} from order #{order} stopped working after {days} days of light use. Really disappointed."),
    ("refund", "high", "negative",
     "I want to cancel order #{order} and get a full refund. The {product} is not what was advertised."),
    ("refund", "medium", "neutral",
     "Requesting a refund for order #{order}, the {product} doesn't fit as expected. What's your return policy?"),
    ("praise", "low", "positive",
     "Just wanted to say the {product} I got (order #{order}) exceeded expectations! Fast shipping too."),
    ("praise", "low", "positive",
     "Five stars for the {product}. Ordered a second one already. Great customer service on order #{order}."),
    ("question", "low", "neutral",
     "Does the {product} come in other colors? Thinking about ordering another one after order #{order}."),
    ("question", "medium", "neutral",
     "Can I change the shipping address for order #{order}? It hasn't shipped yet I think."),
    ("account", "medium", "neutral",
     "I can't log into my account to check order #{order}. Password reset email never arrives."),
    ("praise", "medium", "positive",
     "The {product} from order #{order} was a great gift idea, my mom loved it!"),
    ("defect", "high", "negative",
     "Order #{order}: the {product} caught a weird smell out of the box and part of it is discolored. Is this even safe to use?"),
    ("shipping", "low", "neutral",
     "Just checking the ETA on order #{order}, the {product} page said 5-7 days."),
    ("ambiguous", "high", "negative",
     "This is the THIRD time I'm emailing about order #{order}. If this isn't resolved by Friday I'm disputing the charge with my bank and posting about it."),
]


def generate_rows(n: int) -> list[dict]:
    rows = []
    for i in range(n):
        category, urgency, sentiment, template = random.choice(TEMPLATES)
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        product = random.choice(PRODUCTS)
        order = random.randint(100000, 999999)
        days = random.randint(2, 21)
        text = template.format(order=order, product=product, days=days)
        rows.append({
            "ticket_id": f"T-{1000 + i}",
            "customer_name": name,
            "email": f"{name.lower().replace(' ', '.')}@example.com",
            "channel": random.choice(["email", "shopify_review", "gorgias", "instagram_dm"]),
            "text": text,
            # ground-truth labels kept only for eyeballing accuracy, not fed to the model
            "_expected_category": category,
            "_expected_urgency": urgency,
            "_expected_sentiment": sentiment,
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=300)
    parser.add_argument("--out", type=str, default="data/sample_tickets.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    rows = generate_rows(args.rows)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} synthetic tickets to {out_path}")


if __name__ == "__main__":
    main()
