---
phase: 02-subtitle-artifact-delivery
plan: 02
subsystem: services
tags: [yt-dlp, subtitle-download, metadata, provenance, protocol]

requires:
  - phase: 02-01
    provides: SubtitleArtifact, SubtitleFormat, SubtitleProvenance, SubtitleDownloadOptions, convert_vtt_artifacts, MissingSubtitle
  - phase: 01
    provides: InspectItem, OutputIdentity, build_output_identity, parse_target_url
provides:
  - YtDlpSubtitleDownloader adapter for subtitle-only VTT downloads
  - download_subtitles orchestration service with missing-language handling
  - VideoMetadata and SubtitleDownloadResult domain contracts
  - Per-video metadata JSON persistence
affects: [02-03]

tech-stack:
  added: []
  patterns: [injectable Inspector/Downloader protocols, manual-track preference, language-code VTT parsing]

key-files:
  created:
    - src/yt_subs/infrastructure/yt_dlp_adapter.py (YtDlpSubtitleDownloader)
    - src/yt_subs/services/subtitles.py
    - tests/test_subtitle_downloader.py
    - tests/test_subtitle_service.py
  modified:
    - src/yt_subs/domain/models.py (VideoMetadata, SubtitleDownloadResult)

key-decisions:
  - "Manual subtitle tracks preferred over automatic when both exist for a language"
  - "VTT language code parsed from yt-dlp filename patterns, not assumed"
  - "Service uses Protocol-based dependency injection for testability"

patterns-established:
  - "Inspector/Downloader protocols allow fake implementations in tests"
  - "Metadata persisted as normalized JSON with model_dump(mode='json')"

requirements-completed: [SUBT-01, SUBT-03, SUBT-04, SUBT-05, EXPT-01, EXPT-02, EXPT-03, EXPT-05, META-01]

duration: 7min
completed: 2026-05-10
---

# Phase 02 Plan 02: Single-Video Subtitle Download Summary

**yt-dlp subtitle-only adapter plus orchestration service producing VTT/SRT/TXT artifacts with per-video metadata JSON and structured missing-language reporting**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-10T03:12:46Z
- **Completed:** 2026-05-10T03:19:32Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- YtDlpSubtitleDownloader adapter configured for subtitle-only VTT downloads
- download_subtitles service handles language selection, manual preference, conversion, and metadata
- Missing requested languages reported as structured unavailable outcomes
- Per-video metadata JSON persisted with artifacts, provenance, and missing languages

## Task Commits

1. **Task 1: Add yt-dlp subtitle-only downloader adapter** - `2baff4a` (feat)
2. **Task 2: Orchestrate single-video subtitle artifacts and metadata** - `287cbde` (feat)

## Files Created/Modified
- `src/yt_subs/infrastructure/yt_dlp_adapter.py` - Added YtDlpSubtitleDownloader class
- `src/yt_subs/services/subtitles.py` - download_subtitles service with Protocol-based DI
- `src/yt_subs/domain/models.py` - Added VideoMetadata and SubtitleDownloadResult
- `tests/test_subtitle_downloader.py` - Fake YoutubeDL adapter tests
- `tests/test_subtitle_service.py` - Service orchestration tests with fakes

## Decisions Made
- Manual tracks preferred over automatic when both exist for a language
- VTT language code parsed from yt-dlp filename patterns
- Service uses Protocol-based dependency injection for testability

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SameFileError when source VTT is already in destination dir**
- **Found during:** Task 2 (subtitle service integration)
- **Issue:** convert_vtt_artifacts tried to copy VTT to same path when source was already in subtitles_dir
- **Fix:** Added resolve() comparison before shutil.copy2
- **Files modified:** src/yt_subs/services/subtitle_conversion.py
- **Verification:** All 51 tests pass
- **Committed in:** 287cbde (part of task commit)

---

**Total deviations:** 1 auto-fixed (bug)
**Impact on plan:** Bug fix necessary for correctness. No scope creep.

## Issues Encountered

None

## Next Phase Readiness
- Subtitle download service ready for CLI command wiring in Wave 3
- VideoMetadata and SubtitleDownloadResult contracts ready for rendering layer

---
*Phase: 02-subtitle-artifact-delivery*
*Completed: 2026-05-10*
