"""
Generates data/orders.csv: a synthetic e-commerce orders dataset with
deliberately seeded data quality issues, used as the demo dataset for the
Great Expectations walkthrough.

This script is NOT part of the live demo. The CSV it produces is already
committed to the repo so the dataset is identical every time someone clones
it. Re-run this only if you want to regenerate or modify the seeded issues.

Seeded issues (documented here so you can narrate them confidently live):
  - 3 order_id values are reused on a second row   -> uniqueness failure
  - 3 customer_email values are null                -> not-null failure
  - 2 customer_email values are malformed            -> regex failure
  - 2 order_date values are in the future (> 2026-06-01) -> range failure
  - 3 item_price values are negative                 -> range failure
  - 3 item_price values exceed 500                   -> range failure
  - 2 item_price values are unusually high but still inside 0-500, so the
    range expectation does NOT catch them -> only a z-score (statistical
    outlier) expectation catches these
  - 3 quantity values are 0                           -> range failure
  - 2 shipping_country values are invalid codes      -> value-set failure
  - 2 status values are outside the allowed enum     -> value-set failure

Clean item_price values are clustered tightly (uniform $15-$85, typical
order value) specifically so the 2 "unusually high but in-range" rows
stand out statistically even though they pass the hard $0-$500 rule.

Total: 160 clean rows + 25 dirty rows = 185 rows, shuffled so the bad rows
aren't visually clustered at the bottom of the file.
"""

import random
import pandas as pd
import datetime as dt

random.seed(42)

FIRST_NAMES = ["Maria", "James", "Aiko", "Liam", "Sofia", "Noah", "Priya",
                "Lucas", "Hana", "Mateo", "Grace", "Omar", "Elena", "Sam",
                "Tariq", "Nora", "Diego", "Yuki", "Anika", "Felix"]
LAST_NAMES = ["Garcia", "Smith", "Tanaka", "Murphy", "Rossi", "Khan", "Patel",
               "Mueller", "Suzuki", "Lopez", "Kim", "Nguyen", "Dubois",
               "Andersson", "Silva", "Cohen", "Novak", "Hassan", "Brown", "Park"]
DOMAINS = ["gmail.com", "outlook.com", "yahoo.com", "proton.me", "icloud.com"]
COUNTRIES = ["US", "CA", "GB", "DE", "FR", "JP", "AU", "BR", "IN", "MX"]
STATUSES = ["pending", "shipped", "delivered", "cancelled"]

ANCHOR_DATE = dt.date(2026, 6, 1)  # "today" for the purposes of this dataset


def random_date():
    days_back = random.randint(0, 365)
    return ANCHOR_DATE - dt.timedelta(days=days_back)


def make_clean_row(order_num):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return {
        "order_id": f"ORD-{order_num:05d}",
        "customer_email": f"{first.lower()}.{last.lower()}@{random.choice(DOMAINS)}",
        "order_date": random_date().isoformat(),
        "item_price": round(random.uniform(15, 85), 2),
        "quantity": random.randint(1, 6),
        "shipping_country": random.choice(COUNTRIES),
        "status": random.choice(STATUSES),
    }


rows = [make_clean_row(1000 + i) for i in range(160)]

# --- seed the dirty rows -----------------------------------------------

dirty = []

# 3 duplicate order_id rows (reuse an existing id on a brand-new row)
for i in range(3):
    src = rows[i * 10].copy()
    src["customer_email"] = f"dupe{i}@gmail.com"
    dirty.append(src)  # order_id is intentionally reused, not changed

# 3 null customer_email
for i in range(3):
    row = make_clean_row(2000 + i)
    row["customer_email"] = None
    dirty.append(row)

# 2 malformed customer_email
malformed_emails = ["bob.smithgmail.com", "alice@@nodomain"]
for i, bad_email in enumerate(malformed_emails):
    row = make_clean_row(2100 + i)
    row["customer_email"] = bad_email
    dirty.append(row)

# 2 future order_date
future_dates = ["2027-01-15", "2026-12-31"]
for i, bad_date in enumerate(future_dates):
    row = make_clean_row(2200 + i)
    row["order_date"] = bad_date
    dirty.append(row)

# 3 negative item_price
for i, bad_price in enumerate([-19.99, -5.00, -120.50]):
    row = make_clean_row(2300 + i)
    row["item_price"] = bad_price
    dirty.append(row)

# 3 item_price over the 500 ceiling
for i, bad_price in enumerate([612.00, 899.99, 1450.00]):
    row = make_clean_row(2400 + i)
    row["item_price"] = bad_price
    dirty.append(row)

# 2 item_price values that are unusually high but still pass the 0-500
# range rule -- these are only catchable with a statistical (z-score) check
for i, odd_price in enumerate([410.00, 445.00]):
    row = make_clean_row(2450 + i)
    row["item_price"] = odd_price
    dirty.append(row)

# 3 zero quantity
for i in range(3):
    row = make_clean_row(2500 + i)
    row["quantity"] = 0
    dirty.append(row)

# 2 invalid shipping_country
for i, bad_country in enumerate(["XX", "ZZ"]):
    row = make_clean_row(2600 + i)
    row["shipping_country"] = bad_country
    dirty.append(row)

# 2 invalid status
for i, bad_status in enumerate(["refunded", "returned"]):
    row = make_clean_row(2700 + i)
    row["status"] = bad_status
    dirty.append(row)

all_rows = rows + dirty
random.shuffle(all_rows)

df = pd.DataFrame(all_rows)
df.to_csv("data/orders.csv", index=False)

print(f"Wrote data/orders.csv with {len(df)} rows ({len(dirty)} seeded as dirty)")
