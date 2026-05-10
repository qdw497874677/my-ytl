"""Typer CLI entry point for yt-subs."""

import typer
from rich.console import Console
from rich.table import Table

from yt_subs.services.preflight import PreflightReport, run_preflight

HELP_EPILOG = """
Examples:
  yt-subdl preflight        Check downloader runtime dependencies before a job.

Next steps:
  Run inspect after preflight once inspection commands are available.
"""

app = typer.Typer(
    help="Inspectable YouTube subtitle job setup tools.\n\n" + HELP_EPILOG,
    no_args_is_help=True,
)
console = Console()


@app.callback(invoke_without_command=True)
def main() -> None:
    """Inspectable YouTube subtitle job setup tools.

    Examples:
      yt-subdl preflight        Check downloader runtime dependencies before a job.
    """


def _render_report(report: PreflightReport) -> None:
    table = Table(title="Downloader runtime preflight")
    table.add_column("Check")
    table.add_column("Severity")
    table.add_column("Status")
    table.add_column("Version/Path")
    table.add_column("Action")

    for check in report.checks:
        status = "OK" if check.available else "MISSING"
        version_path = check.version or check.path or "-"
        action = check.remediation or check.detail or "-"
        table.add_row(check.name, check.severity, status, version_path, action)
    console.print(table)


@app.command(help="Check local downloader dependencies before inspecting or downloading.")
def preflight() -> None:
    """Run runtime dependency checks and render actionable output."""

    report = run_preflight()
    _render_report(report)
    if not report.required_passed:
        raise typer.Exit(code=1)
