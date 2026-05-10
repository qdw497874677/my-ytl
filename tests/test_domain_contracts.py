from pathlib import Path

import pytest
from pydantic import ValidationError

from yt_subs.domain.models import InspectItem, JobOptions, SubtitleTrack, TargetRequest
from yt_subs.domain.policies import build_output_identity, plan_item_paths


def test_inspect_item_preserves_video_id_and_tracks() -> None:
    item = InspectItem(
        video_id="abc123",
        title="Example video",
        webpage_url="https://www.youtube.com/watch?v=abc123",
        subtitles=[
            SubtitleTrack(
                language_code="en", language_name="English", kind="manual", source_format="vtt"
            ),
            SubtitleTrack(
                language_code="ja", language_name="Japanese", kind="automatic", source_format="vtt"
            ),
        ],
    )

    assert item.video_id == "abc123"
    assert [track.kind for track in item.subtitles] == ["manual", "automatic"]


def test_job_options_normalizes_output_dir(tmp_path: Path) -> None:
    options = JobOptions(output_dir=str(tmp_path), languages=["en", "zh-Hans"])

    assert options.output_dir == tmp_path
    assert options.languages == ["en", "zh-Hans"]


@pytest.mark.parametrize(
    ("model", "kwargs"),
    [
        (
            InspectItem,
            {"video_id": "", "title": "No id", "webpage_url": "https://www.youtube.com/watch?v=x"},
        ),
        (TargetRequest, {"url": ""}),
    ],
)
def test_empty_critical_identifiers_are_rejected(model: type, kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        model(**kwargs)


def test_output_identity_contains_video_id(tmp_path: Path) -> None:
    item = InspectItem(
        video_id="abc123",
        title="Example video",
        webpage_url="https://www.youtube.com/watch?v=abc123",
    )

    identity = build_output_identity(item, JobOptions(output_dir=tmp_path))

    assert identity.video_id == "abc123"
    assert "abc123" in identity.item_key


def test_plan_item_paths_are_deterministic_under_output_dir(tmp_path: Path) -> None:
    identity = build_output_identity(
        InspectItem(
            video_id="abc123",
            title="Example video",
            webpage_url="https://www.youtube.com/watch?v=abc123",
        ),
        JobOptions(output_dir=tmp_path),
    )

    planned = plan_item_paths(identity, JobOptions(output_dir=tmp_path))

    assert planned.bundle_dir == tmp_path / "items" / identity.item_key
    assert planned.metadata_path == planned.bundle_dir / "metadata" / "item.json"
    assert planned.subtitles_dir == planned.bundle_dir / "subtitles"
    assert planned.logs_dir == planned.bundle_dir / "logs"
    assert planned.media_dir == planned.bundle_dir / "media"


def test_duplicate_titles_do_not_collide_when_video_ids_differ(tmp_path: Path) -> None:
    options = JobOptions(output_dir=tmp_path)
    first = build_output_identity(
        InspectItem(
            video_id="first123",
            title="Same title",
            webpage_url="https://www.youtube.com/watch?v=first123",
        ),
        options,
    )
    second = build_output_identity(
        InspectItem(
            video_id="second456",
            title="Same title",
            webpage_url="https://www.youtube.com/watch?v=second456",
        ),
        options,
    )

    assert first.item_key != second.item_key
    assert first.bundle_dir != second.bundle_dir
