"""Typer CLI entry point for yt-subs."""

import typer
from pydantic import ValidationError
from rich.console import Console

from yt_subs.domain.models import JobOptions
from yt_subs.interfaces.rendering import render_inspect_result, render_preflight_report
from yt_subs.services.inspect import inspect_target
from yt_subs.services.preflight import run_preflight

HELP_EPILOG = """
Examples:
  yt-subdl preflight        Check downloader runtime dependencies before a job.
  yt-subdl inspect URL      Preview videos, subtitles, and planned output paths.

Next steps:
  Run inspect after preflight to preview targets before downloads are implemented.
"""

app = typer.Typer(
    help="Inspectable YouTube subtitle job setup tools.\n\n" + HELP_EPILOG,
    no_args_is_help=True,
)
console = Console(width=160)


@app.callback(invoke_without_command=True)
def main() -> None:
    """Inspectable YouTube subtitle job setup tools.

    Examples:
      yt-subdl preflight        Check downloader runtime dependencies before a job.
      yt-subdl inspect URL      Preview targets before download.
    """


@app.command(help="Check local downloader dependencies before inspecting or downloading.")
def preflight() -> None:
    """Run runtime dependency checks and render actionable output."""

    report = run_preflight()
    render_preflight_report(report, console)
    if not report.required_passed:
        raise typer.Exit(code=1)


@app.command(
    help="Preview a YouTube video or playlist before download.\n\n"
    "Examples:\n"
    "  yt-subdl inspect https://www.youtube.com/watch?v=VIDEO --output-dir downloads"
)
def inspect(
    url: str = typer.Argument(..., help="YouTube video, Shorts, share, or playlist URL."),
    output_dir: str = typer.Option(
        "downloads",
        "--output-dir",
        "-o",
        help="Directory where future artifacts would be planned.",
    ),
) -> None:
    """Preview target items, subtitle availability, and planned output paths."""

    try:
        report = inspect_target(url, JobOptions(output_dir=output_dir))
    except ValidationError as exc:
        console.print(f"Unsupported URL or options: {exc}")
        raise typer.Exit(code=2) from exc
    render_inspect_result(report, console)
