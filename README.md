# yt-subs

CLI-first YouTube subtitle inspection and download tooling.

Phase 1 focuses on inspectable intake and job setup. It lets you check the local runtime, inspect a YouTube video or playlist, see available subtitle tracks, and preview deterministic output paths before any subtitle files are downloaded.

> The current executable name, `yt-subdl`, is an internal temporary CLI name and may be replaced later without changing the core service boundaries.

## Setup

```bash
uv sync
```

## Discover Commands

```bash
uv run yt-subdl --help
```

## Preflight Runtime Dependencies

Check whether downloader-related dependencies are available before starting a job:

```bash
uv run yt-subdl preflight
```

The report distinguishes required checks such as `yt-dlp`, `ffmpeg`, and `ffprobe` from recommended JavaScript runtime support.

## Inspect a Target Before Download

Preview a single video, Shorts/share URL, or playlist-capable YouTube URL:

```bash
uv run yt-subdl inspect "https://www.youtube.com/watch?v=VIDEOID" --output-dir downloads
```

Inspect output includes:

- expanded per-video items for playlists
- YouTube video IDs and stable item identities
- available subtitle language codes with manual/automatic labels
- planned output bundle paths under the selected `--output-dir`

## Phase 1 Boundaries

Implemented now:

- `preflight` runtime readiness checks
- `inspect` metadata preview and output path planning
- configurable output directory for inspect/job setup

Not implemented in Phase 1:

- actual subtitle downloads
- VTT/SRT/TXT conversion
- failed-task reruns or manifests
- video download workflows
- HTTP API mode

Those capabilities are intentionally reserved for later roadmap phases so the CLI/service contracts stay inspectable and stable first.
