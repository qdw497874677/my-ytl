# Feature Landscape

**Domain:** YouTube subtitle/video downloader CLI with future API expansion
**Researched:** 2026-05-09
**Overall confidence:** MEDIUM

## Executive Summary

The downloader market splits into three product shapes:

1. **Quick web tools**: paste a URL, get one file, minimal control.
2. **Desktop/CLI power tools**: playlists, channels, subtitles, metadata, quality selection, retries, archives.
3. **Developer-friendly wrappers/services**: scriptable workflows, structured outputs, task history, and API readiness.

For this project, the competitive baseline is **not** flashy UI. The baseline is: given a video or playlist URL, reliably fetch subtitles and/or media in batch, choose languages and formats, persist metadata, and support reruns without manual cleanup. Tools like yt-dlp and 4K Video Downloader have already trained users to expect playlist support, subtitle extraction, output customization, and resumable/bulk workflows.

Because this project starts subtitle-first, the feature line should be drawn carefully: **table stakes in v1 are reliability, batching, language selection, format export, metadata/log persistence, and rerun safety**. Differentiation should come from being **cleaner and more workflow-oriented** than generic downloaders: better subtitle-first UX, manifest/history, deterministic file layout, failed-item reruns, and API-ready task modeling.

## Market Pattern Summary

Observed common capabilities across established tools and products:

- **Single URL + playlist/channel support** — common in yt-dlp and 4K Video Downloader.
- **Subtitle extraction/export** — common for serious desktop/CLI tools; weaker or inconsistent in lightweight web tools.
- **Quality/format selection for video/audio** — standard once video download is in scope.
- **Batch download and rerun controls** — common in power-user tools.
- **Output templates / organized file saving** — expected by advanced users, especially CLI users.
- **Private/authenticated content handling** — present in advanced tools, but higher complexity and legal/UX risk.
- **Auto-download/subscription workflows** — differentiating rather than baseline.
- **“Safe/no-ads/no-malware” positioning** — important for user trust, especially vs shady web downloaders.

## Table Stakes

Features users expect. Missing these makes the product feel incomplete for the intended CLI/power-user audience.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Single video subtitle download by URL | Absolute minimum job-to-be-done | Low | Must work with standard watch URLs and common URL variants. |
| Playlist subtitle batch download | Your project brief explicitly requires it, and power-user tools already support playlist-level workflows | Medium | Must handle multiple entries, partial failures, and summary reporting. |
| Multi-language subtitle selection | Subtitle users commonly need one or more target languages | Medium | Support explicit language list plus fallback behavior when requested language is unavailable. |
| Subtitle export formats (at least VTT/SRT/TXT) | Users expect machine-readable and human-readable outputs | Medium | TXT is often derived/transformed, so formatting rules must be consistent. |
| Metadata persistence per item | Advanced users expect title/id/channel/upload date/etc. alongside files | Low | Persist as JSON to support reruns, auditing, and future API use. |
| Download logs and job manifest | Required for trust, debugging, and batch reruns | Low | Manifest should record requested URL, resolved items, status, outputs, errors. |
| Deterministic output folder/file naming | Common expectation in CLI tools; essential for automation | Medium | Avoid ad hoc naming. Support stable templates or a strong default hierarchy. |
| Skip/already-downloaded behavior | Users hate duplicate work in large playlists | Medium | Can be implemented via archive file, manifest lookup, or both. |
| Partial failure tolerance in batch jobs | Real playlists often contain blocked/unavailable items | Medium | Batch should continue and report failed entries rather than crash whole run. |
| Retry/rerun failed items | Required by your project context and expected for batch tooling | Medium | Start with rerun-from-manifest; do not require full re-download. |
| Basic subtitle availability reporting | Users need to know whether failure is “no subtitles exist” vs “tool failed” | Low | Distinguish unavailable subtitles, extraction failure, auth-required, region-blocked. |
| Machine-friendly CLI output modes | CLI users expect scriptability | Low | Human-readable default + JSON/NDJSON summary output is ideal. |

## Differentiators

Features that create product advantage, especially for a subtitle-first tool that later grows into full video download.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Subtitle-first job manifest model | Makes this feel like a real workflow tool, not a thin downloader wrapper | Medium | Manifest should treat subtitles as first-class artifacts, not side effects. |
| Rich language fallback policy | Better UX than raw downloader flags | Medium | Example: prefer `zh-Hans`, fallback to `zh`, then auto-generated if allowed. |
| Clean transcript normalization pipeline | Strong differentiator for users who actually read/process subtitles | Medium | Normalize timestamps, line wrapping, speaker labels if present, and TXT extraction rules. |
| Batch summary report | Saves time on large runs and enables API transition | Low | Include success count, failures, missing languages, paths, elapsed time. |
| Re-run by status filter | Better than generic “run again” | Medium | Example: rerun only failed items, only missing-language items, or only subtitle-less items. |
| URL intake normalization | Reduces friction and weird edge-case failures | Low | Normalize watch/share/shorts/playlist URLs before dispatching work. |
| API-ready task model from day one | Big long-term payoff for minimal extra design cost | Medium | Stable task IDs, manifest schema, status enums, artifact records. |
| Video mode reusing same task/output model | Smooth expansion path from subtitles to video | High | Prevents a future rewrite when video becomes core. |
| Per-item artifact bundle | Improves downstream automation | Medium | One folder per item containing subtitles, metadata, logs, thumbnail/description if enabled. |
| Safety/trust posture | Differentiates from ad-heavy web tools | Low | No ads, no browser-extension tricks, explicit logs, explicit file outputs. |
| Optional playlist/channel watch mode later | High-value differentiator for recurring use | High | Auto-fetch new uploads/captions on schedule; defer from MVP. |
| Sidecar metadata for downstream LLM/search workflows | Strong niche differentiator | Medium | Useful if users later feed subtitles into summarization, indexing, or translation pipelines. |

## Future Core Features for Video Expansion

These are not subtitle-v1 requirements, but they become table stakes once video download is promoted to a first-class capability.

| Feature | Why It Becomes Important | Complexity | Notes |
|---------|---------------------------|------------|-------|
| Video quality/format selection | Core expectation for any real downloader | Medium | Resolution, container, codec preferences. |
| Audio-only extraction | Very common user intent | Medium | MP3/M4A or source-preserving audio where possible. |
| Playlist/channel video batch download | Standard in mature tools | Medium | Reuse batch/task model from subtitle phase. |
| Embed subtitles into media or save sidecar | Common advanced workflow | Medium | Sidecar first; embed later if FFmpeg-based pipeline is adopted. |
| Resumable downloads | Important for larger media files | Medium | More important for video than subtitles. |
| Thumbnail/description capture | Common companion metadata feature | Low | Nice complement to video archival workflows. |
| Format merging/remuxing | Required for high-quality YouTube formats in many cases | High | This is where video complexity rises sharply. |

## Anti-Features

Features to deliberately NOT build, at least in the foreseeable early roadmap.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Browser extension / injected “download button” UX | High maintenance, policy risk, brittle against frontend changes, outside stated scope | Keep the product CLI-first and later expose a clean API or minimal web frontend. |
| Full desktop GUI in early phases | Slows delivery without improving downloader core reliability | Build stable CLI/task core first; UI can wrap it later. |
| Reimplementing YouTube extraction logic from scratch | Huge maintenance burden; contradicts project constraint to wrap mature download core | Use mature engine such as yt-dlp and focus on orchestration/product layer. |
| Ad-heavy public web downloader | Operational/legal/trust burden and wrong product direction | Prefer self-use/local CLI first, then controlled API exposure. |
| Editing/transcription suite in MVP | Expands into a different product category | Export clean subtitles/metadata so editing or AI processing can happen downstream. |
| “Download everything from every site” in v1 | Dilutes focus from YouTube subtitle reliability | Design abstraction for future sites, but optimize first for YouTube. |
| Complex account/session management UI | Auth flows are valuable but increase support burden early | Start with local cookie/auth passthrough only if truly needed later. |
| Auto-scheduling/watch mode in subtitle MVP | Useful, but not required to prove core value | Defer until single-run and rerun workflows are rock solid. |

## Feature Dependencies

```text
URL intake normalization → single video subtitle download
single video subtitle download → multi-language subtitle selection
single video subtitle download → subtitle export formats
single video subtitle download → metadata persistence
metadata persistence → logs and job manifest
logs and job manifest → retry/rerun failed items
single video subtitle download + logs/manifest → playlist subtitle batch download
playlist subtitle batch download → partial failure tolerance
deterministic output naming + metadata persistence → skip/already-downloaded behavior
job manifest model → API-ready task model
API-ready task model + existing manifests → future video download mode
video quality selection + audio extraction + resumable downloads → mature video capability
FFmpeg/remux pipeline → embed subtitles / merged high-quality video outputs
```

## MVP Recommendation

Prioritize:

1. **Single video + playlist subtitle download**
   - This is the core user promise and the baseline expectation.
2. **Multi-language selection + VTT/SRT/TXT export**
   - Without this, the tool is not meaningfully subtitle-first.
3. **Metadata/log/manifest persistence + rerun failed items**
   - This is the strongest practical differentiator for a CLI-first workflow tool.

Recommended MVP cut:

- Include:
  - Video URL + playlist URL intake
  - Multi-language selection
  - VTT/SRT/TXT export
  - Per-item metadata JSON
  - Job manifest and logs
  - Continue-on-error batch behavior
  - Rerun failed items from manifest

- Defer:
  - Channel downloads
  - Auto-download/watch mode
  - Authenticated/private content support
  - Video quality/format downloading
  - Embedded subtitles / remuxing
  - Multi-site expansion

## Product Positioning Recommendation

Do **not** try to beat web downloaders on “fastest paste-and-download UI.” That market is crowded, ad-heavy, and not aligned with the project constraints.

Instead, position this tool as:

> **A reliable, subtitle-first YouTube downloader for batch workflows, with clean outputs and a future-proof path to full video download and API automation.**

That positioning is narrower, more defensible, and matches the roadmap: first stabilize subtitle workflows, then promote video download into the same task/artifact system.

## Confidence Notes

| Area | Confidence | Notes |
|------|------------|-------|
| Subtitle table stakes | HIGH | Strongly supported by project brief plus yt-dlp/4K feature sets. |
| Video downloader table stakes | HIGH | Strongly supported by established downloader product pages and ecosystem comparisons. |
| Differentiators | MEDIUM | Based on synthesis of market gaps and your project direction, not a single official spec. |
| Anti-features | MEDIUM | Product-strategy recommendation informed by scope and ecosystem patterns. |

## Sources

### High confidence

- yt-dlp documentation/repo overview and option references (playlist support, metadata output, archive/rerun-adjacent patterns, subtitle handling): https://github.com/yt-dlp/yt-dlp and https://zread.ai/yt-dlp/yt-dlp
- 4K Video Downloader Plus official product page (playlists, channels, subtitles, quality options, auto-download, private content, output management): https://www.4kdownload.com/products/videodownloader-42
- cobalt official site/about and GitHub README (simple paste-and-download UX, privacy/safety posture, self-hostable/service orientation): https://cobalt.tools/about/general and https://github.com/imputnet/cobalt
- JDownloader official overview (download management, pause/resume, bandwidth controls, extensibility): https://jdownloader.org/home/index

### Medium/low confidence supporting ecosystem discovery

- Exa and web search comparison/review content used to identify recurring market patterns, not as sole authority:
  - https://www.notelm.ai/blog/youtube-downloader-guide-2026
  - https://snapvie.com/compare
  - https://en.wikipedia.org/wiki/Comparison_of_YouTube_downloaders

These supporting sources were used mainly to confirm which features repeatedly appear in market comparisons; product recommendations above are based primarily on official product/docs sources plus project constraints.
