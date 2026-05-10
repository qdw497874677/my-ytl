"""Runtime dependency probes for downloader-related tooling."""

import shutil
import subprocess
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

from yt_subs.services.preflight import PreflightCheck

JS_RUNTIME_CANDIDATES = ("deno", "node", "bun", "quickjs")


def _read_command_version(path: str) -> str | None:
    try:
        result = subprocess.run(
            [path, "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (result.stdout or result.stderr).splitlines()
    return output[0] if output else None


def _python_package_check() -> PreflightCheck:
    try:
        detected_version = package_version("yt-dlp")
    except PackageNotFoundError:
        return PreflightCheck(
            name="yt-dlp",
            available=False,
            severity="required",
            remediation="Install project dependencies with `uv sync`.",
        )
    return PreflightCheck(
        name="yt-dlp", available=True, severity="required", version=detected_version
    )


def _binary_check(name: str, *, severity: str = "required") -> PreflightCheck:
    path = shutil.which(name)
    if path is None:
        return PreflightCheck(
            name=name,
            available=False,
            severity=severity,
            remediation=f"Install `{name}` and ensure it is on PATH.",
        )
    return PreflightCheck(
        name=name,
        available=True,
        severity=severity,
        path=path,
        version=_read_command_version(path),
    )


def _js_runtime_check() -> PreflightCheck:
    for candidate in JS_RUNTIME_CANDIDATES:
        path = shutil.which(candidate)
        if path is not None:
            return PreflightCheck(
                name="js-runtime",
                available=True,
                severity="recommended",
                path=path,
                version=_read_command_version(path),
                detail=f"Using {candidate} for yt-dlp JavaScript helpers when needed.",
            )
    return PreflightCheck(
        name="js-runtime",
        available=False,
        severity="recommended",
        remediation="Install one of deno, node, bun, or quickjs for fuller YouTube support.",
    )


def collect_preflight_checks() -> list[PreflightCheck]:
    """Collect downloader runtime checks without raising for missing tools."""

    return [
        _python_package_check(),
        _binary_check("ffmpeg"),
        _binary_check("ffprobe"),
        _js_runtime_check(),
    ]
