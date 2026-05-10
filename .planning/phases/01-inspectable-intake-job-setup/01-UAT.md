---
status: testing
phase: 01-inspectable-intake-job-setup
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md]
started: 2026-05-10T09:30:00Z
updated: 2026-05-10T09:30:00Z
---

## Current Test

number: 1
name: Cold Start Smoke Test
expected: |
  Run `uv run yt-subdl --help` from the project root. The command should print a help screen listing the available subcommands (preflight, inspect, download, batch, rerun) with no import errors or tracebacks.
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: Run `uv run yt-subdl --help` from the project root. The command should print a help screen listing the available subcommands (preflight, inspect, download, batch, rerun) with no import errors or tracebacks.
result: [pending]

### 2. Preflight Dependency Check
expected: Run `uv run yt-subdl preflight`. The command prints a Rich report showing the status of yt-dlp, ffmpeg, ffprobe, and JS runtime. Each check shows "available" or "missing". Required deps (yt-dlp, ffmpeg, ffprobe) missing cause a non-zero exit. Recommended deps (JS runtime) missing produce a warning but do not fail.
result: [pending]

### 3. Inspect Single Video
expected: Run `uv run yt-subdl inspect "https://www.youtube.com/watch?v=dQw4w9WgXcQ"`. The command contacts YouTube via yt-dlp, then displays a Rich table with the video ID, title, available subtitle languages (with manual/automatic labels), and planned output bundle path. No files are written to disk.
result: [pending]

### 4. Inspect with Custom Output Directory
expected: Run `uv run yt-subdl inspect "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o /tmp/yt-test`. The planned output paths shown in the inspect output are rooted under `/tmp/yt-test/` instead of the default `downloads/`.
result: [pending]

### 5. Inspect Invalid URL
expected: Run `uv run yt-subdl inspect "https://example.com/not-youtube"`. The command prints a clear error about the unsupported URL and exits with a non-zero code.
result: [pending]

### 6. Domain Contract Validation
expected: Run `uv run pytest tests/test_domain_contracts.py -x`. All domain model tests pass, validating that video_id is the canonical key, output paths are deterministic, and duplicate titles don't collide.
result: [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps

[none yet]
