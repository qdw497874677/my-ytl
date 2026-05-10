from typer.testing import CliRunner

from yt_subs.interfaces import cli
from yt_subs.interfaces.cli import app
from yt_subs.services.preflight import PreflightCheck, PreflightReport


def test_help_shows_subcommands_and_operation_examples() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "preflight" in result.output
    assert "Examples" in result.output
    assert "yt-subdl preflight" in result.output


def test_preflight_command_calls_service_and_exits_zero(monkeypatch) -> None:
    called = False

    def fake_run_preflight() -> PreflightReport:
        nonlocal called
        called = True
        return PreflightReport(
            checks=[
                PreflightCheck(
                    name="yt-dlp",
                    available=True,
                    severity="required",
                    version="2026.3.17",
                )
            ]
        )

    monkeypatch.setattr(cli, "run_preflight", fake_run_preflight)

    result = CliRunner().invoke(app, ["preflight"])

    assert result.exit_code == 0
    assert called is True
    assert "yt-dlp" in result.output


def test_preflight_command_exits_nonzero_for_required_failures(monkeypatch) -> None:
    def fake_run_preflight() -> PreflightReport:
        return PreflightReport(
            checks=[
                PreflightCheck(
                    name="ffmpeg",
                    available=False,
                    severity="required",
                    remediation="Install ffmpeg",
                )
            ]
        )

    monkeypatch.setattr(cli, "run_preflight", fake_run_preflight)

    result = CliRunner().invoke(app, ["preflight"])

    assert result.exit_code == 1
    assert "ffmpeg" in result.output
    assert "Install ffmpeg" in result.output
