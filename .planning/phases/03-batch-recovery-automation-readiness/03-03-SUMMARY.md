---
phase: 03-batch-recovery-automation-readiness
plan: 03
subsystem: services
tags: [rerun, manifests, retry, recovery]
requires:
  - phase: 03-batch-recovery-automation-readiness
    provides: Batch manifest persistence and resilient batch item execution from 03-01/03-02
provides:
  - Manifest-driven retryable failed-item reruns
  - Shared batch item execution semantics for rerun recovery
affects: [cli-rerun, automation-output, future-api]
tech-stack:
  added: []
  patterns: [Manifest-driven recovery, shared retry/skip semantics]
key-files:
  created: [src/yt_subs/services/rerun.py, tests/test_rerun_service.py]
  modified: [src/yt_subs/services/batch.py]
key-decisions:
  - "Rerun reads the saved manifest as the source of truth and does not re-expand playlists."
  - "Only failed_retryable records are selected; completed, skipped, permanent, and no-subtitle records are preserved."
patterns-established:
  - "Expose a small batch item executor for rerun reuse instead of duplicating status and skip logic."
  - "Append rerun JSONL events and rewrite manifest/summary after each retry candidate."
requirements-completed: [META-02, RELY-02, RELY-03, RELY-04]
duration: 9min
completed: 2026-05-10
---

# Phase 03 Plan 03: Failed-Item Rerun Summary

**Manifest-driven reruns for retryable failures with completed/permanent/no-subtitle records preserved**

## Performance

- **Duration:** 9 min
- **Started:** 2026-05-10T08:41:00Z
- **Completed:** 2026-05-10T08:50:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `rerun_failed_items` to retry only `failed_retryable` records from an existing manifest.
- Reused batch execution/skip/failure semantics by exposing `execute_batch_item` from `batch.py`.
- Added tests proving retry selection, skip-completed behavior, attempts updates, event logging, and preservation of permanent outcomes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Select retryable failures from manifest** - `1ddb48e` (feat)
2. **Task 2: Execute rerun attempts and update durable records** - `1ddb48e` (feat, same cohesive service/test commit)

## Files Created/Modified

- `src/yt_subs/services/rerun.py` - Manifest-driven retry selection, rerun execution, JSONL events, and summary updates.
- `tests/test_rerun_service.py` - Coverage for retry-only selection, skip-completed reruns, and preservation of permanent outcomes.
- `src/yt_subs/services/batch.py` - Exposed shared `execute_batch_item` helper for consistent rerun semantics.

## Decisions Made

- Treat saved manifests as the rerun source of truth so reruns do not depend on live playlist expansion.
- Preserve non-retryable records exactly and mutate only selected retryable item records.

## Deviations from Plan

None - plan executed as written aside from grouping the TDD green work for both rerun tasks into one cohesive commit.

## Issues Encountered

- `uv` remains unavailable; verification used `python3 -m pytest`.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness

- Plan 03-04 can expose `run_batch_subtitle_job` and `rerun_failed_items` through Typer commands and render `BatchRunSummary` for both humans and scripts.

## Self-Check: PASSED

- Found `src/yt_subs/services/rerun.py`.
- Found `tests/test_rerun_service.py`.
- Found commit `1ddb48e`.

---
*Phase: 03-batch-recovery-automation-readiness*
*Completed: 2026-05-10*
