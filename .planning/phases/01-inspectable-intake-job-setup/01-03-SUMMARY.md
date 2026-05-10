---
phase: 01-inspectable-intake-job-setup
plan: 03
subsystem: inspect
tags: [yt-dlp, url-intake, metadata-inspection, pydantic, output-planning]
requires:
  - phase: 01-01
    provides: Pydantic domain contracts and deterministic output policy
provides:
  - common YouTube URL intake classification
  - isolated yt-dlp metadata-only inspection adapter
  - inspect service returning per-item subtitle availability and output identities
affects: [phase-01-cli-inspect, phase-02-subtitle-download, phase-03-playlist-manifest]
tech-stack:
  added: []
  patterns: [inspect-first-service, isolated-yt-dlp-adapter, per-item-playlist-expansion]
key-files:
  created:
    - src/yt_subs/domain/url.py
    - src/yt_subs/infrastructure/yt_dlp_adapter.py
    - src/yt_subs/services/inspect.py
    - tests/test_url_intake.py
    - tests/test_inspect_service.py
  modified: []
key-decisions:
  - "Preserve original YouTube URLs for yt-dlp while using lightweight domain parsing only for early classification and validation."
  - "Keep direct yt-dlp extraction inside one infrastructure adapter and expose normalized InspectItem records to services."
patterns-established:
  - "Playlist inspect results expand into per-video records with playlist_index instead of one opaque batch."
  - "Inspect service attaches Plan 01 output identities without performing filesystem writes."
requirements-completed: [INTK-01, INTK-02, INTK-03, INTK-04, EXPT-04, META-04]
duration: 2 min
completed: 2026-05-10
---

# Phase 01 Plan 03: URL Intake & Metadata Inspection Summary

**Inspect-first service that classifies common YouTube URLs, isolates yt-dlp metadata extraction, and attaches video-ID-based output plans**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-10T02:45:11Z
- **Completed:** 2026-05-10T02:47:23Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Added URL intake parsing for watch, share, Shorts, and playlist-capable YouTube URLs while rejecting unsupported hosts before adapter execution.
- Implemented `YtDlpInspector` as the sole direct `yt_dlp.YoutubeDL` adapter, using metadata-only `extract_info(..., download=False)` and normalizing subtitles into domain models.
- Added `inspect_target` service that parses targets, delegates inspection, preserves playlist order, and attaches deterministic output identity/path plans for each video item.

## Task Commits

1. **Task 1 RED: URL intake tests** - `d3c4a7c` (test)
2. **Task 1 GREEN: URL intake parser** - `7239f7e` (feat)
3. **Task 2 RED: Metadata inspection tests** - `32e8ebc` (test)
4. **Task 2 GREEN: yt-dlp adapter** - `ff6b484` (feat)
5. **Task 3 GREEN: Inspect service composition** - `42e864f` (feat)

## Files Created/Modified

- `src/yt_subs/domain/url.py` - YouTube URL classification and early unsupported-host rejection.
- `src/yt_subs/infrastructure/yt_dlp_adapter.py` - Isolated yt-dlp metadata adapter and subtitle/playlist normalization.
- `src/yt_subs/services/inspect.py` - Application inspect use case with output identity planning.
- `tests/test_url_intake.py` - URL variant and unsupported-host tests.
- `tests/test_inspect_service.py` - Adapter and service tests using fakes/monkeypatching without network access.

## Decisions Made

- Preserved the original URL string for yt-dlp because yt-dlp remains the extraction source of truth; domain URL parsing only provides early classification and validation.
- Expanded playlist entries into individual `InspectItem` records with `playlist_index` so later batch manifests can track per-video status.
- Attached output identity plans during inspect service execution but kept filesystem writes out of Phase 1 inspection logic.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness

- Plan 01-04 can wire the inspect service into the CLI and render per-item subtitle/path information.
- Phase 2 can reuse the adapter/service boundaries when adding actual subtitle artifact downloads.

## Self-Check: PASSED

- Verified created files exist: `src/yt_subs/domain/url.py`, `src/yt_subs/infrastructure/yt_dlp_adapter.py`, `src/yt_subs/services/inspect.py`, `tests/test_inspect_service.py`.
- Verified plan commits exist: `d3c4a7c`, `7239f7e`, `32e8ebc`, `ff6b484`, `42e864f`.
- Verification commands passed: `uv run pytest tests/test_url_intake.py tests/test_inspect_service.py -x`; `uv run ruff check src tests`.

---
*Phase: 01-inspectable-intake-job-setup*
*Completed: 2026-05-10*
