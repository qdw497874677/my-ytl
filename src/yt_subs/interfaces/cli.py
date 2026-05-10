"""Typer CLI entry point for yt-subs."""

from typing import Annotated, Optional

import typer
from pydantic import ValidationError
from rich.console import Console

from yt_subs.domain.models import JobOptions, SubtitleDownloadOptions, SubtitleFormat
from yt_subs.interfaces.rendering import (
    render_inspect_result,
    render_preflight_report,
    render_subtitle_download_result,
)
from yt_subs.services.inspect import inspect_target
from yt_subs.services.preflight import run_preflight
from yt_subs.services.subtitles import download_subtitles

HELP_EPILOG = """
Examples:
  yt-subdl preflight        Check downloader runtime dependencies before a job.
  yt-subdl inspect URL      Preview videos, subtitles, and planned output paths.
  yt-subdl download URL     Download subtitles in requested languages and formats.

Next steps:
  Run inspect to preview targets, then download to fetch subtitle artifacts.
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


@app.command(
    help="Download subtitles for a YouTube video.\n\n"
    "Examples:\n"
    '  yt-subdl download "https://www.youtube.com/watch?v=VIDEOID" --language en --language ja\n'
    "  yt-subdl download URL --format vtt --format srt --format txt\n"
    "  yt-subdl download URL --manual-only"
)
def download(
    url: str = typer.Argument(..., help="YouTube video URL."),
    language: Annotated[
        Optional[list[str]], typer.Option("--language", "-l", help="Subtitle language(s).")
    ] = None,
    format: Annotated[
        Optional[list[str]], typer.Option("--format", "-f", help="Output format(s): vtt, srt, txt.")
    ] = None,
    output_dir: str = typer.Option(
        "downloads", "--output-dir", "-o", help="Output directory for artifacts."
    ),
    include_automatic: bool = typer.Option(
        True, "--include-automatic/--manual-only", help="Include auto-generated captions."
    ),
) -> None:
    """Download subtitle artifacts for a single video."""

    languages = language or ["en"]
    formats = format or ["vtt"]

    try:
        options = SubtitleDownloadOptions(
            output_dir=output_dir,
            languages=languages,
            formats=[f for f in formats],
            include_automatic=include_automatic,
        )
    except ValidationError as exc:
        console.print(f"Invalid download options: {exc}")
        raise typer.Exit(code=2) from exc

    try:
        result = download_subtitles(url, options)
    except ValidationError as exc:
        console.print(f"Download failed: {exc}")
        raise typer.Exit(code=1) from exc

    render_subtitle_download_result(result, console)
