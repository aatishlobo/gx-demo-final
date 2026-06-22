"""
Step 1 of 3 — Look at the raw data.

Run: python 01_inspect_data.py

This script doesn't use Great Expectations at all yet. The point is to show
the audience a normal-looking pandas DataFrame and ask: "does this data look
okay to you?" Skimming a printed table will not reliably catch the planted
issues (a handful of nulls, a duplicate ID, a price typo) buried in 183 rows
-- which is exactly the problem GX exists to solve. Scripts 2 and 3 pick up
from here.
"""

from rich.console import Console
from rich.table import Table
import pandas as pd

console = Console()

df = pd.read_csv("data/orders.csv")

console.print(f"\n[bold]Loaded[/bold] data/orders.csv — {len(df)} rows, {len(df.columns)} columns\n")

table = Table(title="orders.csv (first 12 rows)", show_lines=False)
for col in df.columns:
    table.add_column(col)
for _, row in df.head(12).iterrows():
    table.add_row(*[str(v) for v in row])
console.print(table)

console.print(
    "\n[dim]Skimming this table won't reliably catch what's wrong with it — "
    "183 rows is already too many to eyeball. That's the problem we're about "
    "to hand off to Great Expectations.[/dim]\n"
)
