"""Tests for yt-dlp subtitle-only downloader adapter."""

from pathlib import Path

from yt_subs.infrastructure import yt_dlp_adapter
from yt_subs.infrastructure.yt_dlp_adapter import YtDlpSubtitleDownloader


class FakeDownloadYoutubeDL:
    """Fake YoutubeDL that records download calls and writes VTT stubs."""

    instances: list["FakeDownloadYoutubeDL"] = []
    download_calls: list[list[str]] = []

    def __init__(self, options: dict) -> None:
        self.options = options
        self._paths_template = options.get("outtmpl", {})
        FakeDownloadYoutubeDL.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def download(self, url_list: list[str]) -> int:
        FakeDownloadYoutubeDL.download_calls.append(url_list)
        # Simulate yt-dlp writing a VTT file based on the subtitle template
        subtitle_tmpl = self._paths_template.get("subtitle", "")
        if subtitle_tmpl:
            vtt_path = Path(substitute_template(subtitle_tmpl, "abc123", "en", "vtt"))
            vtt_path.parent.mkdir(parents=True, exist_ok=True)
            vtt_path.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nTest\n", encoding="utf-8")
        return 0


def substitute_template(template: str, video_id: str, lang: str, ext: str) -> str:
    """Simplistic %(key)s substitution for test purposes."""
    return (
        template.replace("%(id)s", video_id)
        .replace("%(language)s", lang)
        .replace("%(ext)s", ext)
    )


def setup_function():
    """Reset fake state between tests."""
    FakeDownloadYoutubeDL.instances = []
    FakeDownloadYoutubeDL.download_calls = []


def test_adapter_configures_skip_download_and_subtitle_options(monkeypatch) -> None:
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeDownloadYoutubeDL)
    tmp = Path("/tmp/test_subs")
    downloader = YtDlpSubtitleDownloader()
    downloader.download_subtitles("https://www.youtube.com/watch?v=abc123", tmp, ["en"])

    opts = FakeDownloadYoutubeDL.instances[0].options
    assert opts["skip_download"] is True
    assert opts["writesubtitles"] is True
    assert opts["writeautomaticsub"] is True
    assert opts["subtitlesformat"] == "vtt"
    assert opts["subtitleslangs"] == ["en"]


def test_adapter_calls_download_not_extract_info(monkeypatch) -> None:
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeDownloadYoutubeDL)
    tmp = Path("/tmp/test_subs2")
    downloader = YtDlpSubtitleDownloader()
    downloader.download_subtitles("https://www.youtube.com/watch?v=abc123", tmp, ["en"])

    assert FakeDownloadYoutubeDL.download_calls == [["https://www.youtube.com/watch?v=abc123"]]


def test_adapter_returns_discovered_vtt_paths(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeDownloadYoutubeDL)
    downloader = YtDlpSubtitleDownloader()
    result = downloader.download_subtitles(
        "https://www.youtube.com/watch?v=abc123", tmp_path, ["en"]
    )

    assert len(result) >= 1
    assert all(p.suffix == ".vtt" for p in result)


def test_adapter_include_automatic_false(monkeypatch) -> None:
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeDownloadYoutubeDL)
    tmp = Path("/tmp/test_subs3")
    downloader = YtDlpSubtitleDownloader()
    downloader.download_subtitles(
        "https://www.youtube.com/watch?v=abc123", tmp, ["en"], include_automatic=False
    )

    opts = FakeDownloadYoutubeDL.instances[0].options
    assert opts["writeautomaticsub"] is False


def test_downloader_auto_cookie_fallback_tries_browsers_then_plain_download(
    monkeypatch, tmp_path: Path
) -> None:
    class FlakyDownloadYoutubeDL(FakeDownloadYoutubeDL):
        def download(self, url_list: list[str]) -> int:
            browser = self.options.get("cookiesfrombrowser", (None, None))[0]
            if browser is not None:
                raise RuntimeError(f"cookie lookup failed for {browser}")
            return super().download(url_list)

    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FlakyDownloadYoutubeDL)
    monkeypatch.setattr(
        yt_dlp_adapter,
        "auto_cookie_browser_order",
        lambda platform=None: ["firefox", "chrome"],
    )

    downloader = YtDlpSubtitleDownloader()
    result = downloader.download_subtitles(
        "https://www.youtube.com/watch?v=abc123", tmp_path, ["en"]
    )

    attempted = [
        instance.options.get("cookiesfrombrowser")
        for instance in FakeDownloadYoutubeDL.instances
    ]
    assert attempted == [
        ("firefox", None, None, None),
        ("chrome", None, None, None),
        None,
    ]
    assert result


def test_downloader_enables_default_remote_components(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeDownloadYoutubeDL)

    downloader = YtDlpSubtitleDownloader()
    downloader.download_subtitles("https://www.youtube.com/watch?v=abc123", tmp_path, ["en"])

    assert FakeDownloadYoutubeDL.instances[0].options["remote_components"] == ["ejs:github"]


def test_downloader_can_disable_remote_components(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeDownloadYoutubeDL)

    downloader = YtDlpSubtitleDownloader(disable_remote_components=True)
    downloader.download_subtitles("https://www.youtube.com/watch?v=abc123", tmp_path, ["en"])

    assert FakeDownloadYoutubeDL.instances[0].options["remote_components"] == []


def test_downloader_passes_default_network_stability_options(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeDownloadYoutubeDL)

    downloader = YtDlpSubtitleDownloader()
    downloader.download_subtitles("https://www.youtube.com/watch?v=abc123", tmp_path, ["en"])

    opts = FakeDownloadYoutubeDL.instances[0].options
    assert opts["source_address"] == "0.0.0.0"
    assert opts["retries"] == 5
    assert opts["extractor_retries"] == 5


def test_downloader_can_override_network_stability_options(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeDownloadYoutubeDL)

    downloader = YtDlpSubtitleDownloader(force_ipv4=False, retries=8, extractor_retries=11)
    downloader.download_subtitles("https://www.youtube.com/watch?v=abc123", tmp_path, ["en"])

    opts = FakeDownloadYoutubeDL.instances[0].options
    assert "source_address" not in opts
    assert opts["retries"] == 8
    assert opts["extractor_retries"] == 11
