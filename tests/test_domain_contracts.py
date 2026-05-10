from pathlib import Path

import pytest
from pydantic import ValidationError

from yt_subs.domain.models import InspectItem, JobOptions, SubtitleTrack, TargetRequest


def test_inspect_item_preserves_video_id_and_tracks() -> None:
    item = InspectItem(
        video_id="abc123",
        title="Example video",
        webpage_url="https://www.youtube.com/watch?v=abc123",
        subtitles=[
            SubtitleTrack(language_code="en", language_name="English", kind="manual", source_format="vtt"),
            SubtitleTrack(language_code="ja", language_name="Japanese", kind="automatic", source_format="vtt"),
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
        (InspectItem, {"video_id": "", "title": "No id", "webpage_url": "https://www.youtube.com/watch?v=x"}),
        (TargetRequest, {"url": ""}),
    ],
)
def test_empty_critical_identifiers_are_rejected(model: type, kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        model(**kwargs)
