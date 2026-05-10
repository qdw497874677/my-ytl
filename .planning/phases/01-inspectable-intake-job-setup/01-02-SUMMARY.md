---
phase: 01-inspectable-intake-job-setup
plan: 02
subsystem: cli
tags: [typer, rich, preflight, yt-dlp, ffmpeg, pytest]
requires:
  - phase: 01-01
    provides: uv Python package skeleton and shared service/domain boundaries
provides:
  - runtime preflight checks for yt-dlp, ffmpeg, ffprobe, and JS runtime candidates
  - service-level PreflightReport and PreflightCheck contracts
  - Typer root app with first-class preflight subcommand
affects: [phase-01-cli, phase-02-download-readiness, phase-03-reliability]
tech-stack:
  added: []
  patterns: [thin-cli-adapter, service-owned-readiness-report, infrastructure-runtime-probes]
key-files:
  created:
    - src/yt_subs/infrastructure/__init__.py
    - src/yt_subs/infrastructure/preflight.py
    - src/yt_subs/services/__init__.py
    - src/yt_subs/services/preflight.py
    - src/yt_subs/interfaces/__init__.py
    - src/yt_subs/interfaces/cli.py
    - tests/test_preflight.py
    - tests/test_cli_preflight.py
  modified: []
key-decisions:
  - "Model preflight results as structured service contracts so the CLI and future API can share readiness semantics."
  - "Treat ffmpeg and ffprobe as required checks while JS runtime support is recommended but non-blocking."
patterns-established:
  - "CLI handlers call services and do not import infrastructure probe helpers directly."
  - "Infrastructure checks classify missing tools instead of crashing the command."
requirements-completed: [RELY-05, CLIX-01]
duration: 3 min
completed: 2026-05-10
---

# Phase 01 Plan 02: Runtime Preflight & CLI Shell Summary

**Typer `preflight` command backed by structured service reports for downloader dependency readiness**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-10T02:42:31Z
- **Completed:** 2026-05-10T02:45:11Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added infrastructure probes for `yt-dlp`, `ffmpeg`, `ffprobe`, and JS runtime candidates with deterministic tests that do not require real binaries.
- Added `PreflightCheck` and `PreflightReport` service contracts so readiness status is reusable beyond the CLI.
- Exposed a single Typer root app with a `preflight` subcommand that renders Rich output and returns non-zero only for required dependency failures.

## Task Commits

1. **Task 1 RED: Preflight service tests** - `ecca80d` (test)
2. **Task 1 GREEN: Preflight probe service** - `f9fc91d` (feat)
3. **Task 2 RED: CLI preflight tests** - `75d6265` (test)
4. **Task 2 GREEN: Typer preflight command** - `a20c0c5` (feat)

## Files Created/Modified

- `src/yt_subs/infrastructure/preflight.py` - Runtime probes for Python package and external downloader support tools.
- `src/yt_subs/services/preflight.py` - Service-level readiness report models and `run_preflight` use case.
- `src/yt_subs/interfaces/cli.py` - Typer app and Rich-rendered `preflight` command.
- `tests/test_preflight.py` - Deterministic service/probe tests with monkeypatched runtime checks.
- `tests/test_cli_preflight.py` - Typer runner tests for help text, successful checks, and required failures.
- Namespace `__init__.py` files for infrastructure, services, and interfaces.

## Decisions Made

- Classified `yt-dlp`, `ffmpeg`, and `ffprobe` as required because later download/post-processing workflows depend on them operationally.
- Classified JS runtime support as recommended because it improves full YouTube compatibility but should not block a Phase 1 preflight command from explaining the state.
- Kept CLI rendering in `interfaces/cli.py` and all runtime probe logic below the service boundary.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness

- Plan 01-04 can reuse the existing Typer app and rendering pattern when wiring inspect commands.
- Runtime readiness is now available before metadata inspection or subtitle download work.

## Self-Check: PASSED

- Verified created files exist: `src/yt_subs/infrastructure/preflight.py`, `src/yt_subs/services/preflight.py`, `src/yt_subs/interfaces/cli.py`, `tests/test_cli_preflight.py`.
- Verified plan commits exist: `ecca80d`, `f9fc91d`, `75d6265`, `a20c0c5`.
- Verification commands passed: `uv run pytest tests/test_preflight.py tests/test_cli_preflight.py -x`; `uv run ruff check src tests`.

---
*Phase: 01-inspectable-intake-job-setup*
*Completed: 2026-05-10*
