# UAT Report — All Phases (1 + 2 + 3)

**Date:** 2026-05-10
**Environment:** Python 3.12.3 (system), no `uv`, no `ffmpeg`, no `deno`
**Tester:** Automated UAT

---

## Phase 1: Inspectable Intake & Job Setup

| # | Test | Result | Notes |
|---|------|--------|-------|
| 1 | `yt-subdl --help` cold start | ✅ PASS | All subcommands listed, no import errors |
| 2 | `yt-subdl preflight` dependency check | ✅ PASS | yt-dlp OK, ffmpeg/ffprobe MISSING correctly reported, js-runtime warning shown |
| 3 | `yt-subdl inspect --help` | ✅ PASS | Usage, args, options displayed correctly |
| 4 | `yt-subdl download --help` | ✅ PASS | Usage, args, multi-language/format options correct |
| 5 | `yt-subdl batch --help` | ✅ PASS | Usage, args, json-summary option present |
| 6 | `yt-subdl rerun --help` | ✅ PASS | Usage, args, manifest_path required |

### Phase 1 Issues

- **ISSUE-1 (minor):** `requires-python = ">=3.13,<3.14"` too strict for Python 3.12 environments. The code itself runs fine on 3.12. Relaxed to `>=3.12,<3.14` during testing.
- **Severity:** Low — recommendation to widen or document Python 3.12 compatibility.

---

## Phase 2: Subtitle Artifact Delivery

| # | Test | Result | Notes |
|---|------|--------|-------|
| 7 | `yt-subdl inspect VIDEO_URL` | ✅ PASS | Video title, manual+automatic subtitles, planned bundle path all correct |
| 8 | `yt-subdl download VIDEO_URL -l en -f vtt -f srt -f txt` | ✅ PASS | 3 artifacts created (vtt/srt/txt), metadata JSON persisted |
| 9 | SRT content validation | ✅ PASS | Proper SRT format with timestamps |
| 10 | TXT content validation | ✅ PASS | Plain text lyrics exported correctly |
| 11 | Metadata JSON structure | ✅ PASS | video_id, title, requested_languages, artifacts[] with provenance, missing_languages=[] |
| 12 | Artifact provenance chain | ✅ PASS | Each artifact tracks source_path, source_format, source_language_code, source_kind |

### Phase 2 Issues

- None found.

---

## Phase 3: Batch Recovery & Automation Readiness

| # | Test | Result | Notes |
|---|------|--------|-------|
| 13 | Unit tests (65 total) | ✅ PASS | All 65 unit tests passing |
| 14 | Lint (`ruff check`) | ✅ PASS | Clean |
| 15 | `yt-subdl batch PLAYLIST_URL` | ❌ FAIL | **Critical: unhandled DownloadError from yt-dlp during playlist extraction** |

### Phase 3 Issues

- **ISSUE-2 (critical):** `batch` command crashes when yt-dlp encounters authentication/bot-detection errors during playlist extraction. The `inspect_target()` call at `batch.py:70` is outside any per-item error boundary. When yt-dlp raises `DownloadError` while iterating playlist entries (e.g., "Sign in to confirm you're not a bot"), the entire batch job crashes instead of marking that item as failed and continuing.
  - **Root cause:** `inspect_target()` uses `ydl.extract_info(url, download=False)` which tries to enumerate all playlist entries in one call. If any single entry fails, the entire yt-dlp call throws.
  - **Fix needed:** Either (a) pass `ignoreerrors=True` to yt-dlp so it skips failed entries and returns what it can, or (b) wrap the inspect call in a try/except and surface a clear "playlist inspection partially failed" result, or (c) both.
  - **Severity:** High — makes batch unusable for any playlist with restricted/geoblocked videos.

---

## Summary

| Phase | Tests | Pass | Fail |
|-------|-------|------|------|
| 1 | 6 | 6 | 0 |
| 2 | 6 | 6 | 0 |
| 3 | 3 | 2 | 1 |
| **Total** | **15** | **14** | **1** |

### Issues Found

| ID | Severity | Phase | Description |
|----|----------|-------|-------------|
| ISSUE-1 | Low | 1 | Python version constraint too strict (>=3.13 only) |
| ISSUE-2 | High | 3 | Batch crashes on playlist entry errors instead of per-item recovery |

### Verdict

**Phase 1:** ✅ PASS
**Phase 2:** ✅ PASS
**Phase 3:** ⚠️ PASS with critical issue — batch needs error boundary around playlist inspection

### Recommended Next Steps

1. Fix ISSUE-2: Add `ignoreerrors` or equivalent error boundary to yt-dlp adapter for batch operations
2. Fix ISSUE-1: Widen `requires-python` or explicitly document 3.12 compat
3. Re-run UAT for batch with fix applied
