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
