---
phase: 02-subtitle-artifact-delivery
status: complete
researched: 2026-05-10
---

# Phase 02 Research: Subtitle Artifact Delivery

## Scope

Plan Phase 2 so users can download subtitle artifacts for a single video, request one or more languages, receive VTT/SRT/TXT exports, see unavailable-language outcomes, and get per-video JSON metadata with provenance. Phase 2 builds on Phase 1 inspect/output identity contracts and intentionally does not implement playlist-level recovery, job manifests, reruns, progress summaries, video download, or API mode.

## Technical Findings

### yt-dlp subtitle download path

Use the existing `yt_subs.infrastructure.yt_dlp_adapter` boundary rather than letting CLI/services call `yt_dlp.YoutubeDL` directly.

Relevant yt-dlp Python options from current docs:

- `writesubtitles: True` downloads manual subtitles.
- `writeautomaticsub: True` downloads automatic captions.
- `subtitleslangs: ['en', 'es']` selects requested languages; `['all']` is supported but should not be Phase 2 default.
- `subtitlesformat: 'vtt'` should be the raw source download format for Phase 2. `yt-dlp` can also prefer `srt/vtt/best`, but keeping a VTT source file simplifies provenance and deterministic conversion.
- `skip_download: True` downloads subtitles without downloading media.
- `writeinfojson: True` can persist yt-dlp info JSON, but Phase 2 should write its own normalized `metadata/item.json` so CLI/API contracts are stable and do not leak raw yt-dlp schema.
- `paths` + `outtmpl` supports separate subtitle templates. Use the planned item `subtitles_dir` from Phase 1 and a stable template keyed by video ID/language/kind/format.

### Subtitle conversion library

`webvtt-py` 0.5.1 is a small focused library for reading WebVTT and writing SRT:

- Read VTT: `webvtt.read('captions.vtt')`
- Iterate captions with clean text: `caption.start`, `caption.end`, `caption.text`; `.text` strips WebVTT class tags.
- Write SRT: `vtt.write(file, format='srt')` or `vtt.save_as_srt()`

Recommendation: add `webvtt-py>=0.5.1,<0.6.0` as a runtime dependency. Implement TXT conversion in our own `services/subtitle_conversion.py` by iterating captions and writing de-duplicated non-empty text lines. This keeps plain-text semantics explicit and testable instead of burying them in shell filters.

### Existing code contracts to preserve

Phase 1 provides:

- Pure Pydantic domain models in `src/yt_subs/domain/models.py`.
- Deterministic item output identity in `src/yt_subs/domain/policies.py`:
  - bundle: `{output_dir}/items/{video_id[-safe-title]}`
  - metadata: `metadata/item.json`
  - subtitles: `subtitles/`
- Inspect service in `src/yt_subs/services/inspect.py` with injectable `Inspector` protocol and `InspectReport`.
- CLI pattern: Typer handlers in `interfaces/cli.py` call service functions and render normalized models via `interfaces/rendering.py`.

Preserve this layering:

```text
CLI -> services -> infrastructure adapter -> yt-dlp
domain models/policies stay free of Typer, Rich, and yt-dlp imports
```

## Recommended Architecture

### Add domain contracts first

Create explicit contracts before implementation:

- `SubtitleFormat = Literal['vtt', 'srt', 'txt']`
- `RequestedSubtitle` / `DownloadedSubtitleArtifact` / `MissingSubtitle` / `SubtitleDownloadResult`
- `SubtitleDownloadOptions` extending user-facing options: output dir, languages, formats, include automatic.
- `VideoMetadata` / `SubtitleProvenance` for normalized `metadata/item.json`.

These contracts should be API-ready Pydantic models and should not reference Typer/Rich/yt-dlp types.

### Adapter behavior

Add a `YtDlpSubtitleDownloader` adapter next to `YtDlpInspector`. It should:

1. Inspect/normalize the target item or reuse inspected item data.
2. Compute a planned output identity before any writes.
3. Invoke yt-dlp with `skip_download=True`, `writesubtitles=True`, `writeautomaticsub=include_automatic`, `subtitleslangs=languages`, `subtitlesformat='vtt'`, and an output template under the planned subtitle directory.
4. Return paths to VTT files discovered under the subtitle directory rather than assuming exact yt-dlp file naming internals in service code.

Use fake adapter tests for service logic. Avoid network-required tests.

### Conversion behavior

Conversion service should be deterministic:

- VTT is the source artifact. If `vtt` requested, retain/copy the downloaded VTT path as an artifact.
- SRT is generated from VTT via `webvtt-py`.
- TXT is generated from VTT by joining cleaned caption texts, dropping blank lines and consecutive duplicates.
- Every converted artifact records provenance: source VTT path, source format `vtt`, requested language, subtitle kind (`manual` or `automatic`), output format, output path.

### Metadata behavior

Write `metadata/item.json` alongside artifacts. Include at least:

- `video_id`
- `title`
- `webpage_url`
- `requested_languages`
- `requested_formats`
- `include_automatic`
- `artifacts` list with language, kind, format, path, source path/format
- `missing_languages` list with requested language and reason `unavailable`

Use `model_dump(mode='json')` for JSON-safe output.

## Pitfalls and Constraints

- Do not download video in Phase 2. `skip_download=True` is mandatory for subtitle adapter tests/acceptance.
- Do not expose raw yt-dlp dictionaries in service return values or metadata JSON.
- Do not build playlist retry/manifest logic here; that belongs to Phase 3.
- Do not rely on `youtube-transcript-api`; roadmap requires playlist, metadata, provenance, and future video expansion with yt-dlp as the core.
- Handle unavailable requested languages as a structured result, not a generic exception.
- Preserve manual vs automatic subtitle kind in outputs/metadata. If a language has both, prefer manual for that language unless automatic is specifically the only available match and `include_automatic=True`.

## Validation Architecture

Automated validation should avoid live YouTube network access:

- Unit tests for domain contracts and options validation.
- Fake downloader/inspector tests for language selection, unavailable-language reporting, artifact path/provenance, and metadata persistence.
- Conversion tests using tiny checked-in or inline VTT fixture content.
- CLI tests monkeypatch service calls and assert options are passed plus user-facing output includes artifact/missing-language summaries.
- Full suite: `uv run pytest -q --tb=short` and `uv run ruff check src tests`.

## Sources

- Context7 `/yt-dlp/yt-dlp` docs: subtitle options (`writesubtitles`, `writeautomaticsub`, `subtitleslangs`, `subtitlesformat`, `skip_download`), output templates, info JSON.
- `webvtt-py` docs: reading VTT captions, `caption.text`, writing SRT via `vtt.write(f, format='srt')`.
- PyPI `webvtt-py` 0.5.1 project metadata.
