"""
A custom Great Expectations Checkpoint Action.

This is the "Act" step from the Define -> Validate -> Report -> Act model:
when validation fails, something should actually happen, not just get
logged. Built-in actions exist for real alerting (SlackNotificationAction,
PagerdutyAlertAction, EmailAction, etc.) but those need live webhook
credentials -- not something to depend on mid-presentation. This action
does something real and self-contained instead: it splits the batch into
clean rows and quarantined rows based on which rows actually failed an
expectation, writes the quarantined rows to their own CSV, and prints a
pipeline-gate style report.

In a real deployment, "quarantine bad rows" might mean writing to a
dead-letter table, and "alert team" might mean this same report going to
Slack instead of the terminal. The mechanism here -- inspecting
unexpected_index_list per failed expectation -- is the same either way.
"""

from typing import Literal
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from great_expectations.checkpoint import ValidationAction

console = Console()


class QuarantineAndAlertAction(ValidationAction):
    """Quarantines rows that failed any expectation; reports pass/fail status."""

    type: Literal["quarantine_and_alert"] = "quarantine_and_alert"
    data_path: str
    quarantine_path: str = "data/quarantined_rows.csv"

    def run(self, checkpoint_result, action_context=None) -> dict:
        df = pd.read_csv(self.data_path)

        bad_indices = set()
        failed_rules = []
        for validation_result in checkpoint_result.run_results.values():
            for r in validation_result["results"]:
                if not r["success"]:
                    column = r["expectation_config"]["kwargs"].get("column", "")
                    failed_rules.append(f"{r['expectation_config']['type']}({column})")
                    bad_indices.update(r["result"].get("unexpected_index_list") or [])

        clean_count = len(df) - len(bad_indices)

        if bad_indices:
            quarantined = df.loc[sorted(bad_indices)]
            quarantined.to_csv(self.quarantine_path, index=False)

            rules_list = "\n".join(f"  - {rule}" for rule in sorted(set(failed_rules)))
            console.print(Panel(
                f"[bold red]PIPELINE GATE: BLOCKED[/bold red]\n\n"
                f"[bold]{len(bad_indices)}[/bold] of [bold]{len(df)}[/bold] rows failed at least "
                f"one expectation and were written to [bold]{self.quarantine_path}[/bold].\n"
                f"[bold]{clean_count}[/bold] clean rows would be safe to promote downstream.\n\n"
                f"Failed rules:\n{rules_list}\n\n"
                f"[dim]In a real pipeline this is the moment Great Expectations would stop "
                f"the DAG, page on-call, and hand the rest of the pipeline only the clean "
                f"rows -- this same unexpected_index_list mechanism is what a real "
                f"Slack/PagerDuty action or a dead-letter table write would use.[/dim]",
                title="[bold yellow]Checkpoint Action: quarantine_and_alert[/bold yellow]",
                border_style="red",
            ))
        else:
            console.print(Panel(
                "[bold green]PIPELINE GATE: CLEARED[/bold green]\n"
                "All rows passed every expectation. Safe to promote to the next layer.",
                title="[bold yellow]Checkpoint Action: quarantine_and_alert[/bold yellow]",
                border_style="green",
            ))

        return {"quarantined_count": len(bad_indices), "clean_count": clean_count}
