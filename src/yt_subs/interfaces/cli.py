"""Typer CLI entry point for yt-subs."""

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console

from yt_subs.domain.models import BatchRunLogEvent, JobOptions, SubtitleDownloadOptions
from yt_subs.interfaces.rendering import (
    render_batch_progress_event,
    render_batch_run_summary,
    render_inspect_result,
    render_preflight_report,
    render_subtitle_download_result,
)
from yt_subs.services.batch import BatchSubtitleOptions, run_batch_subtitle_job
from yt_subs.services.inspect import inspect_target
from yt_subs.services.preflight import run_preflight
from yt_subs.services.rerun import rerun_failed_items
from yt_subs.services.subtitles import download_subtitles

MANIFEST_PATH_ARGUMENT = typer.Argument(..., help="Path to a saved batch manifest JSON.")

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

COOKIE_HELP_TEXT = (
    "Browser to extract cookies from (e.g. chrome, firefox, safari). "
    "If omitted together with --cookies, yt-subdl auto-detects common browsers "
    "in platform order, preferring Firefox-family first; Zen uses the Firefox-compatible path."
)

COOKIE_FILE_HELP_TEXT = (
    "Path to Netscape-format cookies.txt file. "
    "Use this or --cookies-from-browser to override automatic browser cookie detection."
)

REMOTE_COMPONENTS_HELP_TEXT = (
    "Allow yt-dlp to fetch remote components when needed. Repeat to pass multiple values. "
    "Defaults to ejs:github unless --no-remote-components is set."
)


def _progress_renderer(event: BatchRunLogEvent) -> None:
    render_batch_progress_event(event, console)


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
    "  yt-subdl inspect https://www.youtube.com/watch?v=VIDEO --output-dir downloads\n"
    "  yt-subdl inspect URL --remote-components ejs:github\n"
    "  yt-subdl inspect URL --cookies-from-browser chrome\n"
    "  yt-subdl inspect URL --cookies-from-browser zen  # Zen uses Firefox-compatible cookies"
)
def inspect(
    url: str = typer.Argument(..., help="YouTube video, Shorts, share, or playlist URL."),
    output_dir: str = typer.Option(
        "downloads",
        "--output-dir",
        "-o",
        help="Directory where future artifacts would be planned.",
    ),
    cookies_from_browser: str = typer.Option(
        None,
        "--cookies-from-browser",
        help=COOKIE_HELP_TEXT,
    ),
    cookies: str = typer.Option(
        None,
        "--cookies",
        help=COOKIE_FILE_HELP_TEXT,
    ),
    remote_components: Annotated[
        list[str] | None,
        typer.Option("--remote-components", help=REMOTE_COMPONENTS_HELP_TEXT),
    ] = None,
    no_remote_components: bool = typer.Option(
        False,
        "--no-remote-components",
        help="Disable all remote component fetching, including the default ejs:github.",
    ),
) -> None:
    """Preview target items, subtitle availability, and planned output paths."""

    from yt_subs.infrastructure.yt_dlp_adapter import YtDlpInspector

    try:
        inspector = YtDlpInspector(
            cookies_from_browser=cookies_from_browser,
            cookies_file=cookies,
            remote_components=remote_components,
            disable_remote_components=no_remote_components,
        )
        report = inspect_target(url, JobOptions(output_dir=output_dir), inspector=inspector)
    except ValidationError as exc:
        console.print(f"Unsupported URL or options: {exc}")
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        console.print(f"[bold red]Inspect failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    render_inspect_result(report, console)


@app.command(
    help="Download subtitles for a YouTube video.\n\n"
    "Examples:\n"
    '  yt-subdl download "https://www.youtube.com/watch?v=VIDEOID" --language en --language ja\n'
    "  yt-subdl download URL --format vtt --format srt --format txt\n"
    "  yt-subdl download URL --remote-components ejs:github\n"
    "  yt-subdl download URL --manual-only\n"
    "  yt-subdl download URL --cookies-from-browser chrome\n"
    "  yt-subdl download URL --cookies-from-browser zen  # Zen uses Firefox-compatible cookies"
)
def download(
    url: str = typer.Argument(..., help="YouTube video URL."),
    language: Annotated[
        list[str] | None, typer.Option("--language", "-l", help="Subtitle language(s).")
    ] = None,
    format: Annotated[
        list[str] | None, typer.Option("--format", "-f", help="Output format(s): vtt, srt, txt.")
    ] = None,
    output_dir: str = typer.Option(
        "downloads", "--output-dir", "-o", help="Output directory for artifacts."
    ),
    include_automatic: bool = typer.Option(
        True, "--include-automatic/--manual-only", help="Include auto-generated captions."
    ),
    cookies_from_browser: str = typer.Option(
        None,
        "--cookies-from-browser",
        help=COOKIE_HELP_TEXT,
    ),
    cookies: str = typer.Option(
        None,
        "--cookies",
        help=COOKIE_FILE_HELP_TEXT,
    ),
    remote_components: Annotated[
        list[str] | None,
        typer.Option("--remote-components", help=REMOTE_COMPONENTS_HELP_TEXT),
    ] = None,
    no_remote_components: bool = typer.Option(
        False,
        "--no-remote-components",
        help="Disable all remote component fetching, including the default ejs:github.",
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
        result = download_subtitles(
            url,
            options,
            cookies_from_browser=cookies_from_browser,
            cookies_file=cookies,
            remote_components=remote_components,
            disable_remote_components=no_remote_components,
        )
    except ValidationError as exc:
        console.print(f"Download failed: {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print(f"[bold red]Download failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    render_subtitle_download_result(result, console)


@app.command(
    help="Run a resilient playlist subtitle batch job.\n\n"
    "Examples:\n"
    "  yt-subdl batch URL --language en --format vtt --format srt --output-dir downloads\n"
    "  yt-subdl batch URL --remote-components ejs:github\n"
    "  yt-subdl batch URL --json-summary\n"
    "  yt-subdl batch URL --cookies-from-browser chrome\n"
    "  yt-subdl batch URL --cookies-from-browser zen  # Zen uses Firefox-compatible cookies"
)
def batch(
    url: str = typer.Argument(..., help="YouTube video or playlist URL."),
    language: Annotated[
        list[str] | None, typer.Option("--language", "-l", help="Subtitle language(s).")
    ] = None,
    format: Annotated[
        list[str] | None, typer.Option("--format", "-f", help="Output format(s): vtt, srt, txt.")
    ] = None,
    output_dir: str = typer.Option(
        "downloads", "--output-dir", "-o", help="Output directory for artifacts."
    ),
    include_automatic: bool = typer.Option(
        True, "--include-automatic/--manual-only", help="Include auto-generated captions."
    ),
    json_summary: bool = typer.Option(
        False, "--json-summary", help="Print machine-readable summary JSON."
    ),
    cookies_from_browser: str = typer.Option(
        None,
        "--cookies-from-browser",
        help=COOKIE_HELP_TEXT,
    ),
    cookies: str = typer.Option(
        None,
        "--cookies",
        help=COOKIE_FILE_HELP_TEXT,
    ),
    remote_components: Annotated[
        list[str] | None,
        typer.Option("--remote-components", help=REMOTE_COMPONENTS_HELP_TEXT),
    ] = None,
    no_remote_components: bool = typer.Option(
        False,
        "--no-remote-components",
        help="Disable all remote component fetching, including the default ejs:github.",
    ),
) -> None:
    """Run a playlist-scale subtitle batch job."""

    from yt_subs.infrastructure.yt_dlp_adapter import YtDlpInspector

    try:
        options = BatchSubtitleOptions(
            output_dir=output_dir,
            languages=language or ["en"],
            formats=format or ["vtt"],
            include_automatic=include_automatic,
        )
    except ValidationError as exc:
        console.print(f"Invalid batch options: {exc}")
        raise typer.Exit(code=2) from exc

    try:
        progress_callback = None
        if not json_summary:
            progress_callback = _progress_renderer
        inspector = YtDlpInspector(
            cookies_from_browser=cookies_from_browser,
            cookies_file=cookies,
            remote_components=remote_components,
            disable_remote_components=no_remote_components,
        )
        summary = run_batch_subtitle_job(
            url,
            options,
            inspector=inspector,
            progress_callback=progress_callback,
        )
    except ValidationError as exc:
        console.print(f"Batch failed: {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print(f"[bold red]Batch job failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    if json_summary:
        summary_json = json.dumps(
            summary.model_dump(mode="json"), ensure_ascii=False, sort_keys=True
        )
        console.print(summary_json)
    else:
        render_batch_run_summary(summary, console)


@app.command(
    help="Rerun retryable failures from a saved batch manifest.\n\n"
    "Examples:\n"
    "  yt-subdl rerun downloads/batch-jobs/JOB/manifest.json\n"
    "  yt-subdl rerun MANIFEST_PATH --json-summary"
)
def rerun(
    manifest_path: Path = MANIFEST_PATH_ARGUMENT,
    json_summary: bool = typer.Option(
        False, "--json-summary", help="Print machine-readable summary JSON."
    ),
) -> None:
    """Rerun only retryable failed items from a saved manifest."""

    try:
        progress_callback = None
        if not json_summary:
            progress_callback = _progress_renderer
        summary = rerun_failed_items(
            manifest_path,
            progress_callback=progress_callback,
        )
    except ValidationError as exc:
        console.print(f"Rerun failed: {exc}")
        raise typer.Exit(code=1) from exc

    if json_summary:
        summary_json = json.dumps(
            summary.model_dump(mode="json"), ensure_ascii=False, sort_keys=True
        )
        console.print(summary_json)
    else:
        render_batch_run_summary(summary, console)
