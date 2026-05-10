"""Isolated yt-dlp metadata inspection and subtitle download adapters."""

import configparser
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL

from yt_subs.domain.models import InspectItem, SubtitleTrack

AUTO_COOKIE_FAILURE_GUIDANCE = (
    "Automatic browser cookie detection was attempted but did not succeed. "
    "Pass --cookies-from-browser BROWSER or --cookies /path/to/cookies.txt explicitly."
)

COOKIE_BROWSER_ALIASES = {
    "zen": "firefox",
}

DEFAULT_REMOTE_COMPONENTS = ["ejs:github"]


def auto_cookie_browser_order(platform: str | None = None) -> list[str]:
    """Return the platform-aware browser fallback order for auto cookie detection."""

    platform = platform or sys.platform
    if platform.startswith("darwin"):
        return ["firefox", "chrome", "chromium", "edge", "safari"]
    if platform.startswith("win"):
        return ["firefox", "chrome", "edge", "chromium"]
    return ["firefox", "chrome", "chromium", "edge"]


def _build_ydl_cookie_options(
    cookies_from_browser: str | None = None,
    cookies_file: str | Path | None = None,
) -> dict[str, Any]:
    """Build yt-dlp cookie-related options from user-facing CLI flags."""
    opts: dict[str, Any] = {}
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = _parse_cookies_from_browser(cookies_from_browser)
    elif cookies_file:
        opts["cookiefile"] = str(cookies_file)
    return opts


def _parse_cookies_from_browser(value: str) -> tuple[str, str | None, str | None, str | None]:
    """Translate CLI cookies-from-browser input into yt-dlp API tuple format."""

    browser_spec, container = _split_browser_container(value)
    browser_name, profile, keyring = _split_browser_profile(browser_spec)

    normalized_browser = browser_name.lower()
    backend = COOKIE_BROWSER_ALIASES.get(normalized_browser, normalized_browser)
    resolved_profile = profile
    resolved_keyring = keyring

    if normalized_browser == "zen":
        resolved_profile = _resolve_zen_profile(profile)
        resolved_keyring = None

    return (backend, resolved_profile, resolved_keyring, container)


def _split_browser_container(value: str) -> tuple[str, str | None]:
    browser_spec, separator, container = value.partition("::")
    return browser_spec, container if separator else None


def _split_browser_profile(value: str) -> tuple[str, str | None, str | None]:
    parts = value.split(":")
    browser = parts[0]
    profile = parts[1] if len(parts) >= 2 and parts[1] else None
    keyring = parts[2] if len(parts) >= 3 and parts[2] else None
    return browser, profile, keyring


def _resolve_zen_profile(profile: str | None, home: Path | None = None) -> str | None:
    """Resolve macOS Zen profile paths for yt-dlp's Firefox cookie backend."""

    if profile:
        return profile

    if not sys.platform.startswith("darwin"):
        return None

    home = home or Path.home()
    zen_root = home / "Library" / "Application Support" / "zen"
    profiles_ini = zen_root / "profiles.ini"

    for candidate in _zen_profiles_from_ini(profiles_ini, zen_root):
        if candidate.exists():
            return str(candidate)

    profiles_dir = zen_root / "Profiles"
    preferred_candidates = sorted(profiles_dir.glob("*Default (release)"))
    for candidate in preferred_candidates:
        if candidate.exists():
            return str(candidate)

    fallback_candidates = sorted(profiles_dir.glob("*/cookies.sqlite"))
    if fallback_candidates:
        return str(fallback_candidates[0].parent)

    return None


def _zen_profiles_from_ini(profiles_ini: Path, zen_root: Path) -> list[Path]:
    if not profiles_ini.exists():
        return []

    parser = configparser.ConfigParser()
    parser.read(profiles_ini, encoding="utf-8")

    install_defaults: set[str] = set()
    for section in parser.sections():
        if not section.startswith("Install"):
            continue
        default = parser.get(section, "Default", fallback="").strip()
        if default:
            install_defaults.add(default)

    preferred: list[Path] = []
    others: list[Path] = []
    for section in parser.sections():
        if not section.startswith("Profile"):
            continue
        path_value = parser.get(section, "Path", fallback="").strip()
        if not path_value:
            continue
        is_relative = parser.getboolean(section, "IsRelative", fallback=True)
        candidate = (zen_root / path_value) if is_relative else Path(path_value)
        if path_value in install_defaults or "Default (release)" in candidate.name:
            preferred.append(candidate)
        else:
            others.append(candidate)

    return [*preferred, *others]


def _build_remote_component_options(
    remote_components: list[str] | None = None,
    disable_remote_components: bool = False,
) -> dict[str, Any]:
    if disable_remote_components:
        return {"remote_components": []}
    selected = (
        list(remote_components)
        if remote_components is not None
        else list(DEFAULT_REMOTE_COMPONENTS)
    )
    return {"remote_components": selected}


def _cookie_attempts(
    cookies_from_browser: str | None = None,
    cookies_file: str | Path | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    if cookies_from_browser or cookies_file:
        label = (
            f"browser:{cookies_from_browser}" if cookies_from_browser else f"file:{cookies_file}"
        )
        return [(label, _build_ydl_cookie_options(cookies_from_browser, cookies_file))]

    return [
        (f"auto:{browser}", _build_ydl_cookie_options(cookies_from_browser=browser))
        for browser in auto_cookie_browser_order()
    ] + [("auto:none", {})]


def _run_with_cookie_fallback(
    action: Callable[[dict[str, Any]], Any],
    *,
    base_options: dict[str, Any],
    cookies_from_browser: str | None = None,
    cookies_file: str | Path | None = None,
) -> Any:
    attempts = _cookie_attempts(cookies_from_browser, cookies_file)
    explicit_cookie_input = bool(cookies_from_browser or cookies_file)
    auto_failures: list[str] = []
    last_error: Exception | None = None

    for label, cookie_options in attempts:
        options = dict(base_options)
        options.update(cookie_options)
        try:
            return action(options)
        except Exception as exc:
            last_error = exc
            if explicit_cookie_input:
                raise
            if label.startswith("auto:") and label != "auto:none":
                auto_failures.append(label.removeprefix("auto:"))

    if last_error is None:
        msg = "yt-dlp execution failed before any cookie attempt was made"
        raise RuntimeError(msg)

    attempted = ", ".join(auto_failures) or ", ".join(auto_cookie_browser_order())
    message = f"{last_error} {AUTO_COOKIE_FAILURE_GUIDANCE} Tried: {attempted}."
    raise RuntimeError(message) from last_error


class YtDlpInspector:
    """Adapter boundary for metadata-only yt-dlp inspection."""

    def __init__(
        self,
        ydl_options: dict[str, Any] | None = None,
        *,
        cookies_from_browser: str | None = None,
        cookies_file: str | Path | None = None,
        remote_components: list[str] | None = None,
        disable_remote_components: bool = False,
    ) -> None:
        self.ydl_options: dict[str, Any] = {
            "ignoreconfig": True,
            "quiet": True,
            "skip_download": True,
            "ignoreerrors": True,
        }
        self.ydl_options.update(
            _build_remote_component_options(remote_components, disable_remote_components)
        )
        if ydl_options:
            self.ydl_options.update(ydl_options)
        self._cookies_from_browser = cookies_from_browser
        self._cookies_file = cookies_file

    def inspect(self, url: str) -> list[InspectItem]:
        def _inspect(options: dict[str, Any]) -> list[InspectItem]:
            with YoutubeDL(options) as ydl:
                raw_info = ydl.extract_info(url, download=False)
                if raw_info is None:
                    return []
                if hasattr(ydl, "sanitize_info"):
                    raw_info = ydl.sanitize_info(raw_info)
            return list(_normalize_info(raw_info))

        return _run_with_cookie_fallback(
            _inspect,
            base_options=self.ydl_options,
            cookies_from_browser=self._cookies_from_browser,
            cookies_file=self._cookies_file,
        )


class YtDlpSubtitleDownloader:
    """Adapter for subtitle-only downloads via yt-dlp."""

    def __init__(
        self,
        ydl_options: dict[str, Any] | None = None,
        *,
        cookies_from_browser: str | None = None,
        cookies_file: str | Path | None = None,
        remote_components: list[str] | None = None,
        disable_remote_components: bool = False,
    ) -> None:
        self._extra_options: dict[str, Any] = _build_remote_component_options(
            remote_components, disable_remote_components
        )
        if ydl_options:
            self._extra_options.update(ydl_options)
        self._cookies_from_browser = cookies_from_browser
        self._cookies_file = cookies_file

    def download_subtitles(
        self,
        url: str,
        subtitles_dir: Path,
        languages: list[str],
        include_automatic: bool = True,
    ) -> list[Path]:
        """Download subtitle VTT files to subtitles_dir and return discovered paths."""
        subtitles_dir.mkdir(parents=True, exist_ok=True)
        options: dict[str, Any] = {
            "ignoreconfig": True,
            "quiet": True,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": include_automatic,
            "subtitleslangs": languages,
            "subtitlesformat": "vtt",
            "outtmpl": {
                "subtitle": str(subtitles_dir / "%(id)s.%(language)s.%(ext)s"),
                "default": str(subtitles_dir / "%(id)s.%(ext)s"),
            },
        }
        options.update(self._extra_options)

        def _download(ydl_options: dict[str, Any]) -> list[Path]:
            with YoutubeDL(ydl_options) as ydl:
                ydl.download([url])
            return sorted(subtitles_dir.glob("*.vtt"))

        return _run_with_cookie_fallback(
            _download,
            base_options=options,
            cookies_from_browser=self._cookies_from_browser,
            cookies_file=self._cookies_file,
        )


def _normalize_info(raw_info: dict[str, Any]) -> Iterable[InspectItem]:
    entries = raw_info.get("entries")
    if entries:
        for index, entry in enumerate(entries, start=1):
            if entry:
                yield _normalize_item(entry, playlist_index=index)
        return
    yield _normalize_item(raw_info, playlist_index=raw_info.get("playlist_index"))


def _normalize_item(info: dict[str, Any], playlist_index: int | None = None) -> InspectItem:
    return InspectItem(
        video_id=str(info.get("id") or info.get("display_id")),
        title=info.get("title"),
        webpage_url=info.get("webpage_url") or info.get("original_url"),
        playlist_index=playlist_index,
        subtitles=[
            *_tracks(info.get("subtitles") or {}, "manual"),
            *_tracks(info.get("automatic_captions") or {}, "automatic"),
        ],
    )


def _tracks(raw_tracks: dict[str, list[dict[str, Any]]], kind: str) -> list[SubtitleTrack]:
    tracks: list[SubtitleTrack] = []
    for language_code, variants in raw_tracks.items():
        first = variants[0] if variants else {}
        tracks.append(
            SubtitleTrack(
                language_code=language_code,
                language_name=first.get("name"),
                kind=kind,
                source_format=first.get("ext"),
            )
        )
    return tracks
