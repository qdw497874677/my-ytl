"""Rich renderers for normalized interface reports."""

from rich.console import Console
from rich.table import Table

from yt_subs.domain.models import InspectItem, OutputIdentity
from yt_subs.services.inspect import InspectReport
from yt_subs.services.preflight import PreflightReport
from yt_subs.services.subtitles import SubtitleDownloadResult


def render_preflight_report(report: PreflightReport, console: Console) -> None:
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


def _subtitle_label(item: InspectItem) -> str:
    if not item.subtitles:
        return "none discovered"
    return ", ".join(f"{track.language_code} ({track.kind})" for track in item.subtitles)


def render_inspect_result(report: InspectReport, console: Console) -> None:
    """Render normalized inspect items and output identities, never raw yt-dlp dictionaries."""

    table = Table(title=f"Inspect preview: {report.target.kind}")
    table.add_column("#")
    table.add_column("Video ID")
    table.add_column("Title")
    table.add_column("Subtitles")
    table.add_column("Planned bundle")

    for index, planned in enumerate(report.items, start=1):
        item: InspectItem = planned.item
        identity: OutputIdentity = planned.identity
        row_number = str(item.playlist_index or index)
        table.add_row(
            row_number,
            identity.video_id,
            item.title or "-",
            _subtitle_label(item),
            str(identity.bundle_dir),
        )
    console.print(table)


def render_subtitle_download_result(result: SubtitleDownloadResult, console: Console) -> None:
    """Render subtitle download artifacts and missing-language outcomes."""

    # Artifacts table
    if result.artifacts:
        table = Table(title="Subtitle artifacts")
        table.add_column("Language")
        table.add_column("Kind")
        table.add_column("Format")
        table.add_column("Path")
        table.add_column("Source")

        for artifact in result.artifacts:
            table.add_row(
                artifact.language_code,
                artifact.kind,
                artifact.format,
                str(artifact.path),
                str(artifact.provenance.source_path),
            )
        console.print(table)

    # Missing subtitles
    if result.missing_subtitles:
        console.print("\n[bold]Missing subtitles:[/bold]")
        for missing in result.missing_subtitles:
            console.print(f"  {missing.language_code}: {missing.reason}")

    # Metadata path
    console.print(f"\nMetadata: {result.metadata_path}")
