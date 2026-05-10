from pathlib import Path

from yt_subs.domain.models import InspectItem, JobOptions, SubtitleTrack
from yt_subs.infrastructure import yt_dlp_adapter
from yt_subs.infrastructure.yt_dlp_adapter import YtDlpInspector


class FakeYoutubeDL:
    instances = []

    def __init__(self, options):
        self.options = options
        self.extract_calls = []
        FakeYoutubeDL.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def extract_info(self, url, download=False):
        self.extract_calls.append((url, download))
        return {
            "id": "abc123",
            "title": "Example video",
            "webpage_url": url,
            "subtitles": {"en": [{"ext": "vtt", "name": "English"}]},
            "automatic_captions": {"ja": [{"ext": "vtt", "name": "Japanese"}]},
        }

    def sanitize_info(self, info):
        return info


def test_adapter_calls_extract_info_with_download_false(monkeypatch) -> None:
    FakeYoutubeDL.instances = []
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeYoutubeDL)

    items = YtDlpInspector().inspect("https://www.youtube.com/watch?v=abc123")

    assert FakeYoutubeDL.instances[0].extract_calls == [
        ("https://www.youtube.com/watch?v=abc123", False)
    ]
    assert items[0].video_id == "abc123"


def test_adapter_normalizes_single_video_subtitle_tracks(monkeypatch) -> None:
    FakeYoutubeDL.instances = []
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeYoutubeDL)

    item = YtDlpInspector().inspect("https://www.youtube.com/watch?v=abc123")[0]

    assert item.subtitles == [
        SubtitleTrack(
            language_code="en", language_name="English", kind="manual", source_format="vtt"
        ),
        SubtitleTrack(
            language_code="ja",
            language_name="Japanese",
            kind="automatic",
            source_format="vtt",
        ),
    ]


def test_adapter_normalizes_playlist_entries(monkeypatch) -> None:
    class PlaylistYoutubeDL(FakeYoutubeDL):
        def extract_info(self, url, download=False):
            self.extract_calls.append((url, download))
            return {
                "_type": "playlist",
                "entries": [
                    {"id": "one", "title": "One", "webpage_url": "https://youtu.be/one"},
                    {"id": "two", "title": "Two", "webpage_url": "https://youtu.be/two"},
                ],
            }

    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", PlaylistYoutubeDL)

    items = YtDlpInspector().inspect("https://www.youtube.com/playlist?list=PL")

    assert [item.video_id for item in items] == ["one", "two"]
    assert [item.playlist_index for item in items] == [1, 2]


class FakeInspector:
    def inspect(self, url: str):
        return [
            InspectItem(
                video_id="abc123",
                title="Example video",
                webpage_url=url,
                playlist_index=1,
                subtitles=[SubtitleTrack(language_code="en", kind="manual", source_format="vtt")],
            )
        ]


def test_inspect_target_returns_items_with_subtitle_tracks(tmp_path: Path) -> None:
    from yt_subs.services.inspect import inspect_target

    result = inspect_target(
        "https://www.youtube.com/watch?v=abc123",
        JobOptions(output_dir=tmp_path),
        inspector=FakeInspector(),
    )

    assert result.items[0].item.subtitles[0].language_code == "en"


def test_inspect_target_attaches_video_id_based_output_plan(tmp_path: Path) -> None:
    from yt_subs.services.inspect import inspect_target

    result = inspect_target(
        "https://www.youtube.com/watch?v=abc123",
        JobOptions(output_dir=tmp_path),
        inspector=FakeInspector(),
    )

    planned = result.items[0].identity
    assert planned.video_id == "abc123"
    assert "abc123" in planned.item_key
    assert planned.bundle_dir == tmp_path / "items" / planned.item_key


def test_inspect_target_preserves_playlist_order(tmp_path: Path) -> None:
    from yt_subs.services.inspect import inspect_target

    result = inspect_target(
        "https://www.youtube.com/watch?v=abc123&list=PL",
        JobOptions(output_dir=tmp_path),
        inspector=FakeInspector(),
    )

    assert result.items[0].item.playlist_index == 1


def test_auto_cookie_browser_order_prefers_firefox_family_first() -> None:
    assert yt_dlp_adapter.auto_cookie_browser_order("linux") == [
        "firefox",
        "chrome",
        "chromium",
        "edge",
    ]
    assert yt_dlp_adapter.auto_cookie_browser_order("darwin") == [
        "firefox",
        "chrome",
        "chromium",
        "edge",
        "safari",
    ]


def test_zen_browser_alias_uses_firefox_cookie_backend() -> None:
    options = yt_dlp_adapter._build_ydl_cookie_options(cookies_from_browser="zen:Default")

    assert options["cookiesfrombrowser"] == ("firefox", "Default", None, None)


def test_default_remote_components_enable_ejs_github() -> None:
    options = yt_dlp_adapter._build_remote_component_options()

    assert options["remote_components"] == ["ejs:github"]


def test_no_remote_components_clears_defaults() -> None:
    options = yt_dlp_adapter._build_remote_component_options(disable_remote_components=True)

    assert options["remote_components"] == []


def test_custom_remote_components_override_default() -> None:
    options = yt_dlp_adapter._build_remote_component_options(["ejs:npm"])

    assert options["remote_components"] == ["ejs:npm"]


def test_network_stability_defaults_match_known_good_cli() -> None:
    options = yt_dlp_adapter._build_network_stability_options()

    assert options["source_address"] == "0.0.0.0"
    assert options["retries"] == 5
    assert options["extractor_retries"] == 5


def test_network_stability_can_disable_ipv4_and_override_retries() -> None:
    options = yt_dlp_adapter._build_network_stability_options(
        force_ipv4=False,
        retries=8,
        extractor_retries=11,
    )

    assert "source_address" not in options
    assert options["retries"] == 8
    assert options["extractor_retries"] == 11


def test_resolve_zen_profile_prefers_profiles_ini_default(tmp_path: Path) -> None:
    zen_root = tmp_path / "Library" / "Application Support" / "zen"
    profiles_dir = zen_root / "Profiles"
    preferred = profiles_dir / "abcd.Default (release)"
    fallback = profiles_dir / "xyz.other"
    preferred.mkdir(parents=True)
    fallback.mkdir(parents=True)
    (zen_root / "profiles.ini").write_text(
        "[Install123]\nDefault=Profiles/abcd.Default (release)\n\n"
        "[Profile0]\nName=default\nIsRelative=1\nPath=Profiles/abcd.Default (release)\n\n"
        "[Profile1]\nName=other\nIsRelative=1\nPath=Profiles/xyz.other\n",
        encoding="utf-8",
    )
    original_platform = yt_dlp_adapter.sys.platform
    yt_dlp_adapter.sys.platform = "darwin"

    try:
        resolved = yt_dlp_adapter._resolve_zen_profile(None, home=tmp_path)
    finally:
        yt_dlp_adapter.sys.platform = original_platform

    assert resolved == str(preferred)


def test_resolve_zen_profile_falls_back_to_cookies_sqlite_parent(
    tmp_path: Path, monkeypatch
) -> None:
    zen_root = tmp_path / "Library" / "Application Support" / "zen" / "Profiles"
    fallback = zen_root / "cookies-only.default"
    fallback.mkdir(parents=True)
    (fallback / "cookies.sqlite").write_text("sqlite", encoding="utf-8")
    monkeypatch.setattr(yt_dlp_adapter.sys, "platform", "darwin")

    resolved = yt_dlp_adapter._resolve_zen_profile(None, home=tmp_path)

    assert resolved == str(fallback)


def test_inspector_auto_cookie_fallback_tries_browsers_then_plain_request(monkeypatch) -> None:
    class FlakyYoutubeDL(FakeYoutubeDL):
        def extract_info(self, url, download=False):
            browser = self.options.get("cookiesfrombrowser", (None, None))[0]
            if browser is not None:
                raise RuntimeError(f"cookie lookup failed for {browser}")
            return super().extract_info(url, download=download)

    FakeYoutubeDL.instances = []
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FlakyYoutubeDL)
    monkeypatch.setattr(
        yt_dlp_adapter,
        "auto_cookie_browser_order",
        lambda platform=None: ["firefox", "chrome"],
    )

    items = YtDlpInspector().inspect("https://www.youtube.com/watch?v=abc123")

    attempted = [instance.options.get("cookiesfrombrowser") for instance in FakeYoutubeDL.instances]
    assert attempted == [
        ("firefox", None, None, None),
        ("chrome", None, None, None),
        None,
    ]
    assert items[0].video_id == "abc123"


def test_inspector_passes_default_remote_components(monkeypatch) -> None:
    FakeYoutubeDL.instances = []
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeYoutubeDL)

    YtDlpInspector().inspect("https://www.youtube.com/watch?v=abc123")

    assert FakeYoutubeDL.instances[0].options["remote_components"] == ["ejs:github"]


def test_inspector_passes_default_network_stability_options(monkeypatch) -> None:
    FakeYoutubeDL.instances = []
    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", FakeYoutubeDL)

    YtDlpInspector().inspect("https://www.youtube.com/watch?v=abc123")

    assert FakeYoutubeDL.instances[0].options["source_address"] == "0.0.0.0"
    assert FakeYoutubeDL.instances[0].options["retries"] == 5
    assert FakeYoutubeDL.instances[0].options["extractor_retries"] == 5


def test_inspector_auto_cookie_failure_message_mentions_explicit_flags(monkeypatch) -> None:
    class AlwaysFailYoutubeDL(FakeYoutubeDL):
        def extract_info(self, url, download=False):
            browser = self.options.get("cookiesfrombrowser", (None, None))[0]
            if browser is None:
                raise RuntimeError("plain extraction failed")
            raise RuntimeError(f"cookie lookup failed for {browser}")

    monkeypatch.setattr(yt_dlp_adapter, "YoutubeDL", AlwaysFailYoutubeDL)
    monkeypatch.setattr(
        yt_dlp_adapter,
        "auto_cookie_browser_order",
        lambda platform=None: ["firefox", "chrome"],
    )

    try:
        YtDlpInspector().inspect("https://www.youtube.com/watch?v=abc123")
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected runtime error")

    assert "--cookies-from-browser" in message
    assert "--cookies" in message
    assert "firefox, chrome" in message
