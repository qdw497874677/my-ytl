# yt-subs

CLI-first YouTube subtitle inspection and download tooling.

Download subtitles for YouTube videos in VTT, SRT, and TXT formats with per-video metadata and provenance tracking.

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

## Download Subtitles

Download subtitle artifacts for a single YouTube video in the languages and formats you need:

```bash
uv run yt-subdl download "https://www.youtube.com/watch?v=VIDEOID" --language en --language ja --format vtt --format srt --format txt --output-dir downloads
```

Download output includes:

- subtitle artifact files under `downloads/items/{video_id[-title]}/subtitles/`
- per-video metadata at `downloads/items/{video_id[-title]}/metadata/item.json`
- unavailable requested languages reported in CLI output and metadata

VTT is the source subtitle artifact. SRT and TXT are converted exports. Metadata links every converted file to its source track. Unavailable requested languages are reported as structured outcomes, not generic errors.

Options:

- `--language` / `-l` — one or more subtitle languages (repeatable, defaults to `en`)
- `--format` / `-f` — output formats: `vtt`, `srt`, `txt` (repeatable, defaults to `vtt`)
- `--output-dir` / `-o` — output directory (defaults to `downloads`)
- `--manual-only` — exclude auto-generated captions (default includes them)

Artifact layout:

```
downloads/
  items/
    {video_id[-title]}/
      subtitles/
        en.manual.vtt
        en.manual.srt
        en.manual.txt
        ja.automatic.vtt
      metadata/
        item.json
      logs/          (reserved for later)
```

Not implemented yet:

- playlist reruns/manifests and failed-task recovery
- video download workflows
- HTTP API mode

Those capabilities are intentionally reserved for later roadmap phases.
