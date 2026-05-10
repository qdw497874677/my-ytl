from yt_subs.infrastructure import preflight as infra_preflight
from yt_subs.services.preflight import run_preflight


def test_preflight_reports_installed_yt_dlp_version(monkeypatch) -> None:
    monkeypatch.setattr(infra_preflight, "package_version", lambda name: "2026.3.17")
    monkeypatch.setattr(infra_preflight.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(infra_preflight, "_read_command_version", lambda path: "version-output")

    report = run_preflight()
    yt_dlp = report.by_name("yt-dlp")

    assert yt_dlp.available is True
    assert yt_dlp.version == "2026.3.17"
    assert report.required_passed is True


def test_missing_ffmpeg_or_ffprobe_is_failed_check_without_crashing(monkeypatch) -> None:
    monkeypatch.setattr(infra_preflight, "package_version", lambda name: "2026.3.17")
    monkeypatch.setattr(
        infra_preflight.shutil,
        "which",
        lambda name: None if name in {"ffmpeg", "ffprobe"} else f"/usr/bin/{name}",
    )
    monkeypatch.setattr(infra_preflight, "_read_command_version", lambda path: "version-output")

    report = run_preflight()

    assert report.by_name("ffmpeg").available is False
    assert report.by_name("ffprobe").available is False
    assert report.required_passed is False


def test_one_js_runtime_candidate_satisfies_recommended_check(monkeypatch) -> None:
    monkeypatch.setattr(infra_preflight, "package_version", lambda name: "2026.3.17")
    monkeypatch.setattr(
        infra_preflight.shutil,
        "which",
        lambda name: "/usr/bin/node" if name == "node" else f"/usr/bin/{name}"
        if name in {"ffmpeg", "ffprobe"}
        else None,
    )
    monkeypatch.setattr(infra_preflight, "_read_command_version", lambda path: "version-output")

    report = run_preflight()
    js_runtime = report.by_name("js-runtime")

    assert js_runtime.available is True
    assert js_runtime.path == "/usr/bin/node"
    assert js_runtime.severity == "recommended"
