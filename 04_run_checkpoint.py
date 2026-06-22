"""
Step 4 of 4 — Wire the same suite into a Checkpoint.

Run: python 04_run_checkpoint.py

A Checkpoint is GX's orchestration layer: it runs a validation definition
and then fires a list of Actions against the result. This script reuses
the exact same orders_validation built in step 2 -- nothing about the
suite or the rules changes -- but wrapping it in a Checkpoint is what
actually produces side effects:

  - UpdateDataDocsAction builds/refreshes the human-readable Data Docs
    HTML report and opens it in your browser
  - QuarantineAndAlertAction (quarantine_action.py) splits the batch into
    clean and quarantined rows, writes the bad ones to
    data/quarantined_rows.csv, and prints a pipeline-gate style report

This is the "Act" step from the talk: stop the pipeline, alert the team,
quarantine the bad data. Nothing here depends on live credentials or
network access -- everything it does is a local file write and a
terminal print, but the same unexpected_index_list mechanism is what a
real Slack/PagerDuty action or dead-letter-table write would use.
"""

import pandas as pd
from rich.console import Console
import great_expectations as gx
from great_expectations.checkpoint import UpdateDataDocsAction
from quarantine_action import QuarantineAndAlertAction

console = Console()

context = gx.get_context(mode="file", project_root_dir=".")
validation_definition = context.validation_definitions.get("orders_validation")

df = pd.read_csv("data/orders.csv", parse_dates=["order_date"])

console.print("\n[bold]Running orders_checkpoint (same suite, wired to actions)...[/bold]\n")

checkpoint = context.checkpoints.add(
    gx.Checkpoint(
        name="orders_checkpoint",
        validation_definitions=[validation_definition],
        actions=[
            QuarantineAndAlertAction(
                name="quarantine_and_alert",
                data_path="data/orders.csv",
                quarantine_path="data/quarantined_rows.csv",
            ),
            UpdateDataDocsAction(name="update_data_docs"),
        ],
        result_format="COMPLETE",
    )
)
checkpoint.run(batch_parameters={"dataframe": df})

console.print("[dim]Opening the full Data Docs report in your browser...[/dim]")
context.open_data_docs()
