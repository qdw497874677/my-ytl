---
phase: 02-subtitle-artifact-delivery
plan: 01
subsystem: domain
tags: [pydantic, webvtt-py, subtitle, conversion, provenance]

requires:
  - phase: 01-inspectable-intake-job-setup
    provides: InspectItem, OutputIdentity, JobOptions, build_output_identity
provides:
  - SubtitleFormat, SubtitleProvenance, SubtitleArtifact, MissingSubtitle, SubtitleDownloadOptions domain contracts
  - convert_vtt_artifacts deterministic VTT/SRT/TXT conversion service
affects: [02-02, 02-03]

tech-stack:
  added: [webvtt-py>=0.5.1,<0.6.0]
  patterns: [deterministic subtitle conversion with source-track provenance]

key-files:
  created:
    - src/yt_subs/services/subtitle_conversion.py
    - tests/test_subtitle_contracts.py
    - tests/test_subtitle_conversion.py
  modified:
    - src/yt_subs/domain/models.py
    - pyproject.toml
    - uv.lock

key-decisions:
  - "VTT is always the source artifact; SRT/TXT are derived conversions"
  - "TXT conversion drops consecutive duplicate caption lines for clean output"
  - "Domain models stay free of Typer, Rich, yt-dlp, and webvtt imports"

patterns-established:
  - "Conversion functions return SubtitleArtifact list with provenance for traceability"
  - "File naming convention: {language_code}.{kind}.{format} under subtitles dir"

requirements-completed: [EXPT-01, EXPT-02, EXPT-03, EXPT-05]

duration: 4min
completed: 2026-05-10
---

# Phase 02 Plan 01: Subtitle Artifact Contracts Summary

**Pydantic contracts for subtitle formats, provenance, artifacts, and missing-language outcomes plus deterministic VTT-to-SRT/TXT conversion via webvtt-py**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-10T03:07:26Z
- **Completed:** 2026-05-10T03:11:49Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- SubtitleFormat/Provenance/Artifact/MissingSubtitle/DownloadOptions contracts in domain models
- Deterministic VTT→SRT conversion via webvtt-py and VTT→TXT with dedup/cleanup
- webvtt-py dependency added and lockfile refreshed
- All existing Phase 1 domain tests remain passing

## Task Commits

1. **Task 1: Add subtitle artifact domain contracts and conversion dependency** - `8dc5bef` (feat)
2. **Task 2: Implement VTT to SRT/TXT conversion with provenance** - `968911a` (feat)

## Files Created/Modified
- `src/yt_subs/domain/models.py` - SubtitleFormat, SubtitleProvenance, SubtitleArtifact, MissingSubtitle, SubtitleDownloadOptions
- `src/yt_subs/services/subtitle_conversion.py` - convert_vtt_artifacts with VTT/SRT/TXT conversion
- `pyproject.toml` - Added webvtt-py>=0.5.1,<0.6.0
- `uv.lock` - Refreshed with webvtt-py
- `tests/test_subtitle_contracts.py` - Domain contract tests
- `tests/test_subtitle_conversion.py` - Conversion service tests

## Decisions Made
- VTT is always the source artifact; SRT/TXT are derived conversions
- TXT conversion drops consecutive duplicate caption lines for clean output
- Domain models stay free of Typer, Rich, yt-dlp, and webvtt imports

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness
- Conversion core ready for Wave 2 subtitle download service
- SubtitleDownloadOptions contract ready for adapter and service layer

---
*Phase: 02-subtitle-artifact-delivery*
*Completed: 2026-05-10*
