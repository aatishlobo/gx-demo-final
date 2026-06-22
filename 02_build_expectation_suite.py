"""
Step 2 of 3 — Define what "good data" means.

Run: python 02_build_expectation_suite.py

This creates a local GX project (a ./gx folder) and an Expectation Suite:
a named, saved set of rules describing what we expect to be true about the
orders data. Nothing is validated yet -- this script only declares the
rules. Step 3 runs the actual check.
"""

import datetime as dt
from rich.console import Console
import great_expectations as gx
from great_expectations.expectations import (
    ExpectColumnValuesToNotBeNull,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToMatchRegex,
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToBeInSet,
    ExpectColumnValueZScoresToBeLessThan,
)

console = Console()

# A local, file-based GX project in the current directory (./gx).
# File-based (rather than in-memory/ephemeral) so the suite persists and
# script 3 can reload it in a separate process, exactly like a real pipeline.
context = gx.get_context(mode="file", project_root_dir=".")

data_source = context.data_sources.add_pandas(name="orders_source")
data_asset = data_source.add_dataframe_asset(name="orders_asset")
batch_definition = data_asset.add_batch_definition_whole_dataframe(name="orders_batch")

suite = context.suites.add(gx.ExpectationSuite(name="orders_suite"))

EXPECTATIONS = [
    ("order_id is never null",
     ExpectColumnValuesToNotBeNull(column="order_id")),
    ("order_id is unique",
     ExpectColumnValuesToBeUnique(column="order_id")),
    ("customer_email is never null",
     ExpectColumnValuesToNotBeNull(column="customer_email")),
    ("customer_email looks like an email address",
     ExpectColumnValuesToMatchRegex(column="customer_email", regex=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")),
    ("order_date is between 2020-01-01 and today (2026-06-01)",
     ExpectColumnValuesToBeBetween(column="order_date",
                                    min_value=dt.datetime(2020, 1, 1),
                                    max_value=dt.datetime(2026, 6, 1))),
    ("item_price is between $0 and $500",
     ExpectColumnValuesToBeBetween(column="item_price", min_value=0, max_value=500)),
    ("quantity is at least 1",
     ExpectColumnValuesToBeBetween(column="quantity", min_value=1, max_value=None)),
    ("shipping_country is a known country code",
     ExpectColumnValuesToBeInSet(column="shipping_country",
                                  value_set=["US", "CA", "GB", "DE", "FR", "JP", "AU", "BR", "IN", "MX"])),
    ("status is a known order status",
     ExpectColumnValuesToBeInSet(column="status",
                                  value_set=["pending", "shipped", "delivered", "cancelled"])),
    # This one is different from the other nine: it's not a hand-set threshold,
    # it's a statistical test. It flags any item_price more than 2.5 standard
    # deviations from the column's mean -- which catches prices that are
    # technically inside the $0-$500 range (so rule #6 lets them through) but
    # are still way outside the normal spread of order values.
    ("item_price has no statistical outliers (z-score < 2.5)",
     ExpectColumnValueZScoresToBeLessThan(column="item_price", threshold=2.5, double_sided=True)),
]

for label, expectation in EXPECTATIONS:
    suite.add_expectation(expectation)
    console.print(f"  [green]+[/green] {label}")

context.validation_definitions.add(
    gx.ValidationDefinition(name="orders_validation", data=batch_definition, suite=suite)
)

console.print(f"\n[bold green]Suite 'orders_suite' saved[/bold green] with {len(EXPECTATIONS)} expectations.")
console.print("[dim]Nothing has been checked yet -- run 03_validate_and_report.py next.[/dim]\n")
