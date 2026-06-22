"""
Step 3 of 4 — Run the suite and look at the raw result.

Run: python 03_validate_and_report.py

This is *just* validation: it loads the suite built in step 2, runs it
against data/orders.csv once, and prints what comes back -- a colored
pass/fail table and a spotlight on what the statistical check caught that
a hand-set range rule missed.

Deliberately not included here: Data Docs, alerts, quarantine, anything
else with a side effect. A bare validation run only ever gives you back a
Python result object -- nothing else happens unless you wire that result
into a Checkpoint, which is what step 4 (04_run_checkpoint.py) does next.
"""

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import great_expectations as gx

console = Console()

context = gx.get_context(mode="file", project_root_dir=".")
validation_definition = context.validation_definitions.get("orders_validation")

df = pd.read_csv("data/orders.csv", parse_dates=["order_date"])

console.print("\n[bold]Running orders_suite against data/orders.csv...[/bold]\n")
validation_result = validation_definition.run(
    batch_parameters={"dataframe": df}, result_format="COMPLETE"
)

table = Table(title="Validation summary")
table.add_column("Expectation")
table.add_column("Result")
table.add_column("Unexpected count")

for r in validation_result["results"]:
    column = r["expectation_config"]["kwargs"].get("column", "")
    exp_type = r["expectation_config"]["type"]
    label = f"{exp_type}({column})"
    if r["success"]:
        table.add_row(label, "[green]PASS[/green]", "-")
    else:
        count = r["result"].get("unexpected_count", "?")
        table.add_row(label, "[red]FAIL[/red]", str(count))

console.print(table)

stats = validation_result["statistics"]
console.print(
    f"\n[bold]{stats['successful_expectations']}/{stats['evaluated_expectations']} "
    f"expectations passed[/bold] ({stats['success_percent']:.0f}%)\n"
)

# spotlight: what did the statistical check catch that the hand-set range
# rule missed?
range_result = next(
    (r for r in validation_result["results"]
     if r["expectation_config"]["type"] == "expect_column_values_to_be_between"
     and r["expectation_config"]["kwargs"].get("column") == "item_price"),
    None,
)
zscore_result = next(
    (r for r in validation_result["results"]
     if r["expectation_config"]["type"] == "expect_column_value_z_scores_to_be_less_than"),
    None,
)

if range_result and zscore_result:
    range_caught = set(range_result["result"].get("partial_unexpected_list") or [])
    zscore_caught = set(zscore_result["result"].get("partial_unexpected_list") or [])
    only_zscore = sorted(zscore_caught - range_caught)
    if only_zscore:
        console.print(Panel(
            f"The $0-$500 range rule alone would have let these prices through: "
            f"[bold]{only_zscore}[/bold]\n"
            f"They're technically inside the allowed range -- but statistically far "
            f"outside the normal spread of order values. The z-score expectation "
            f"catches them anyway, with no hard-coded threshold for 'too high.'",
            title="[bold yellow]What the statistical check caught that the range rule missed[/bold yellow]",
            border_style="yellow",
        ))

console.print(
    "[dim]The raw validation object is a Python object, nothing more. "
    "No report was built, nothing was alerted, no file was written. "
    "Run 04_run_checkpoint.py next to see what a Checkpoint adds.[/dim]\n"
)
