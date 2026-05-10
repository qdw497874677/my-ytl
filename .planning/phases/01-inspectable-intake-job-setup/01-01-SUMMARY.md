---
phase: 01-inspectable-intake-job-setup
plan: 01
subsystem: domain
tags: [python, uv, pydantic, pytest, ruff, output-identity]
requires: []
provides:
  - uv-managed Python 3.13 package skeleton with temporary CLI entry point
  - Pydantic contracts for inspectable YouTube targets, items, subtitle tracks, job options, and output identities
  - Deterministic output path policy keyed by YouTube video ID
affects: [phase-01-preflight, phase-01-inspect, phase-02-subtitle-download, phase-03-manifest-rerun]
tech-stack:
  added: [uv, yt-dlp, typer, rich, pydantic, structlog, pytest, ruff, hatchling]
  patterns: [pure-domain-contracts, deterministic-filesystem-output-policy, tdd-domain-development]
key-files:
  created:
    - pyproject.toml
    - README.md
    - .gitignore
    - src/yt_subs/__init__.py
    - src/yt_subs/domain/__init__.py
    - src/yt_subs/domain/models.py
    - src/yt_subs/domain/policies.py
    - tests/test_domain_contracts.py
    - uv.lock
  modified: []
key-decisions:
  - "Use video_id as the required canonical uniqueness anchor for every output identity."
  - "Reserve metadata, subtitles, logs, and media namespaces now so later phases can add persistence without changing item identity."
patterns-established:
  - "Domain layer is pure Pydantic/Python and does not import Typer or yt-dlp."
  - "Output paths are computed as deterministic plans before any filesystem writes occur."
requirements-completed: [EXPT-04, META-04, CLIX-04]
duration: 23 min
completed: 2026-05-10
---

# Phase 01 Plan 01: Project Skeleton & Domain Contracts Summary

**uv-managed Python package with pure Pydantic inspect/job contracts and video-ID-based deterministic artifact paths**

## Performance

- **Duration:** 23 min
- **Started:** 2026-05-10T02:19:00Z
- **Completed:** 2026-05-10T02:42:31Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments

- Bootstrapped a Python 3.13 `yt-subs` project with uv-compatible metadata, runtime/dev dependencies, Ruff/Pytest configuration, and temporary `yt-subdl` script entry point.
- Added reusable Pydantic domain contracts for target requests, subtitle tracks, inspected items, job options, and output identities without coupling the domain to Typer or yt-dlp.
- Implemented deterministic output identity/path planning where YouTube `video_id` is the stable machine key and artifact namespaces are planned for metadata, subtitles, logs, and future media.

## Task Commits

Each task was committed atomically:

1. **Task 1: Bootstrap uv Python package and test tooling** - `96ddcdb` (chore)
2. **Task 2 RED: Domain contract tests** - `8e37dc8` (test)
3. **Task 2 GREEN: Domain contract models** - `061e44a` (feat)
4. **Task 3 RED: Output identity policy tests** - `caa25f2` (test)
5. **Task 3 GREEN: Deterministic output policies** - `9ad3694` (feat)
6. **Task 3 cleanup: Generated artifact ignore rules** - `17544b1` (chore)

## Files Created/Modified

- `pyproject.toml` - Project metadata, dependencies, build backend, temporary script entry point, and pytest/ruff configuration.
- `README.md` - Minimal package readme required for editable builds and current project scope.
- `.gitignore` - Python virtualenv, bytecode, and tool cache ignore rules.
- `src/yt_subs/__init__.py` - Package marker and version.
- `src/yt_subs/domain/__init__.py` - Domain namespace marker.
- `src/yt_subs/domain/models.py` - Pydantic contracts for inspectable targets, subtitle tracks, inspected items, job options, and output identities.
- `src/yt_subs/domain/policies.py` - Pure deterministic identity and artifact path policy functions.
- `tests/test_domain_contracts.py` - Unit tests proving validation, stable IDs, output path determinism, and duplicate-title non-collision.
- `uv.lock` - Reproducible uv dependency lockfile.

## Decisions Made

- Used `video_id` as the required canonical uniqueness anchor because titles are mutable and duplicate-prone while META-04 requires a stable identity including the YouTube video ID.
- Reserved `metadata`, `subtitles`, `logs`, and `media` path namespaces during planning so later subtitle and video phases can add writes without changing the Phase 1 identity contract.
- Kept `README.md` minimal in this plan because full CLI documentation is scheduled for Plan 01-04; this file currently exists to satisfy build metadata and orient contributors.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing uv command**
- **Found during:** Task 1 (Bootstrap uv Python package and test tooling)
- **Issue:** The execution environment did not have `uv` on PATH, blocking the required `uv run` verification.
- **Fix:** Installed `uv` for the user environment using `python3 -m pip install --user --break-system-packages uv` and used `$HOME/.local/bin` on PATH for verifications.
- **Files modified:** None in repository
- **Verification:** `uv run python -c "import yt_subs; print(yt_subs.__name__)"` executed successfully after package fixes.
- **Committed in:** N/A (environment-only fix)

**2. [Rule 3 - Blocking] Added package build metadata and minimal README**
- **Found during:** Task 1 (Bootstrap uv Python package and test tooling)
- **Issue:** `uv run` could not import the package until editable build metadata existed, then Hatchling failed because the configured `README.md` did not exist.
- **Fix:** Added Hatchling build-system/package configuration and a minimal `README.md`.
- **Files modified:** `pyproject.toml`, `README.md`
- **Verification:** `uv run python -c "import yt_subs; print(yt_subs.__name__)"` prints `yt_subs`.
- **Committed in:** `96ddcdb`

**3. [Rule 3 - Blocking] Ignored generated Python artifacts**
- **Found during:** Task 3 (Implement deterministic identity and output path policy)
- **Issue:** Running uv/pytest generated `.venv`, `__pycache__`, and tool caches that would otherwise remain as untracked working-tree noise.
- **Fix:** Added `.gitignore` rules for Python virtualenv, bytecode, and cache outputs.
- **Files modified:** `.gitignore`
- **Verification:** `git status --short` no longer reports generated cache directories as untracked.
- **Committed in:** `17544b1`

---

**Total deviations:** 3 auto-fixed (3 blocking)
**Impact on plan:** All fixes were required to complete the planned uv verification and keep the working tree clean; no feature scope was added.

## Issues Encountered

- Local environment only had Python 3.12 system-wide, but `uv` downloaded and used CPython 3.13.13 for the project as required by the plan.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness

- Plan 01-02 can build runtime preflight services and CLI shell on top of the package and domain boundary.
- Plan 01-03 can normalize yt-dlp metadata into `InspectItem` and call the output policy without returning raw dictionaries.
- No blockers remain for downstream Phase 1 plans.

## Self-Check: PASSED

- Verified created files exist: `pyproject.toml`, `src/yt_subs/domain/models.py`, `src/yt_subs/domain/policies.py`, `tests/test_domain_contracts.py`.
- Verified plan commits exist: `96ddcdb`, `8e37dc8`, `061e44a`, `caa25f2`, `9ad3694`, `17544b1`.
- Verification commands passed: `uv run pytest tests/test_domain_contracts.py -x`; `uv run ruff check src tests`.

---
*Phase: 01-inspectable-intake-job-setup*
*Completed: 2026-05-10*
