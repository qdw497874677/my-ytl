import pytest
from pydantic import ValidationError

from yt_subs.domain.url import parse_target_url


def test_standard_watch_url_parses_as_video_target() -> None:
    target = parse_target_url("https://www.youtube.com/watch?v=VIDEOID")

    assert target.kind == "video"
    assert str(target.url) == "https://www.youtube.com/watch?v=VIDEOID"


@pytest.mark.parametrize(
    "url",
    [
        "https://youtu.be/VIDEOID",
        "https://www.youtube.com/shorts/VIDEOID",
    ],
)
def test_share_and_shorts_urls_parse_without_manual_normalization(url: str) -> None:
    target = parse_target_url(url)

    assert target.kind == "video"


def test_url_with_list_parameter_parses_as_playlist_capable_target() -> None:
    url = "https://www.youtube.com/watch?v=VIDEOID&list=PLAYLISTID"

    target = parse_target_url(url)

    assert target.kind == "playlist"
    assert str(target.url) == url


def test_non_youtube_url_raises_clear_validation_error() -> None:
    with pytest.raises(ValidationError):
        parse_target_url("https://example.com/watch?v=VIDEOID")
