# Requirements: YouTube 字幕与视频下载工具

**Defined:** 2026-05-09
**Core Value:** 用户输入 YouTube 地址后，能稳定、可批量地拿到可用的字幕结果，并为后续视频下载和 API 化留下清晰扩展路径。

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Intake

- [x] **INTK-01**: User can submit a single YouTube video URL for subtitle download
- [x] **INTK-02**: User can submit a YouTube playlist URL and have the tool expand it into per-video subtitle tasks
- [x] **INTK-03**: User can use common YouTube URL variants without manual normalization
- [x] **INTK-04**: User can inspect a target before download and see what items/languages are available

### Subtitles

- [x] **SUBT-01**: User can download subtitles for a single video
- [x] **SUBT-02**: User can download subtitles for every supported item in a playlist without the entire batch stopping on one failure
- [x] **SUBT-03**: User can request one or more subtitle languages in a single run
- [x] **SUBT-04**: User can distinguish between manual subtitles and auto-generated subtitles in saved outputs or metadata
- [x] **SUBT-05**: User can see when requested subtitle languages are unavailable for a video

### Export

- [x] **EXPT-01**: User can save subtitle outputs in VTT format
- [x] **EXPT-02**: User can save subtitle outputs in SRT format
- [x] **EXPT-03**: User can save subtitle outputs in TXT format
- [x] **EXPT-04**: User can get deterministic output paths for saved subtitle artifacts
- [x] **EXPT-05**: User can retain provenance linking converted subtitle files back to their source track and format

### Metadata and State

- [x] **META-01**: User gets per-video metadata persisted as JSON alongside downloaded artifacts
- [x] **META-02**: User gets a job manifest that records requested inputs, expanded items, artifact paths, statuses, and errors
- [x] **META-03**: User gets structured download logs for each run
- [x] **META-04**: User can identify each saved artifact bundle by a stable item identity that includes the YouTube video ID

### Reliability

- [x] **RELY-01**: User can continue batch execution after an individual item fails
- [ ] **RELY-02**: User can rerun only failed items from a previous job manifest
- [x] **RELY-03**: User can distinguish retryable failures from permanent no-subtitle or unavailable-content outcomes
- [x] **RELY-04**: User can skip already completed artifacts without duplicating work
- [x] **RELY-05**: User can run an environment preflight check that verifies required downloader dependencies

### CLI Experience

- [x] **CLIX-01**: User can run subtitle workflows through a documented CLI command set
- [x] **CLIX-02**: User can see progress and a final success/failure summary for each job
- [x] **CLIX-03**: User can request machine-readable summary output for scripting or later API compatibility
- [x] **CLIX-04**: User can configure output directory and basic job options without editing source code

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### API

- **API-01**: User can submit a subtitle download job through an HTTP API
- **API-02**: User can query HTTP job status and retrieve artifact locations or downloadable results
- **API-03**: User can reuse the same core job model across CLI and API execution paths

### Video

- **VIDE-01**: User can download video for a single YouTube video URL
- **VIDE-02**: User can choose video quality or format preferences
- **VIDE-03**: User can download audio-only outputs
- **VIDE-04**: User can download video for playlists using the same task and manifest model as subtitle jobs
- **VIDE-05**: User can use FFmpeg-based post-processing for remuxing or merged outputs when needed

### Advanced Workflows

- **ADVW-01**: User can rerun jobs filtered by status category beyond just failed items
- **ADVW-02**: User can use channel-level batch downloads
- **ADVW-03**: User can use a local or self-hosted watch mode for recurring downloads
- **ADVW-04**: User can query historical jobs from a database-backed index when API mode matures

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Browser extension / injected download button | Outside CLI-first/API-ready direction and higher maintenance risk |
| Desktop GUI in early milestones | Slows delivery before core download workflows are stable |
| Reimplementing YouTube extraction from scratch | Conflicts with chosen strategy of wrapping a mature download core |
| Multi-site downloader support in v1 | Dilutes focus away from YouTube subtitle reliability |
| Public ad-heavy web downloader product | Wrong trust and operational model for this project stage |
| Full transcription/editing suite | Not core to download-and-export workflow |
| Private/authenticated content support in v1 | Adds complexity and support burden before core public-content workflow is stable |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INTK-01 | Phase 1 | Complete |
| INTK-02 | Phase 1 | Complete |
| INTK-03 | Phase 1 | Complete |
| INTK-04 | Phase 1 | Complete |
| SUBT-01 | Phase 2 | Complete |
| SUBT-02 | Phase 3 | Complete |
| SUBT-03 | Phase 2 | Complete |
| SUBT-04 | Phase 2 | Complete |
| SUBT-05 | Phase 2 | Complete |
| EXPT-01 | Phase 2 | Complete |
| EXPT-02 | Phase 2 | Complete |
| EXPT-03 | Phase 2 | Complete |
| EXPT-04 | Phase 1 | Complete |
| EXPT-05 | Phase 2 | Complete |
| META-01 | Phase 2 | Complete |
| META-02 | Phase 3 | Complete |
| META-03 | Phase 3 | Complete |
| META-04 | Phase 1 | Complete |
| RELY-01 | Phase 3 | Complete |
| RELY-02 | Phase 3 | Pending |
| RELY-03 | Phase 3 | Complete |
| RELY-04 | Phase 3 | Complete |
| RELY-05 | Phase 1 | Complete |
| CLIX-01 | Phase 1 | Complete |
| CLIX-02 | Phase 3 | Complete |
| CLIX-03 | Phase 3 | Complete |
| CLIX-04 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-09*
*Last updated: 2026-05-09 after initial definition*
