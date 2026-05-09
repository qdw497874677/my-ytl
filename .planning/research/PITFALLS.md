# Domain Pitfalls

**Domain:** YouTube subtitle-first downloader CLI with future video/API expansion
**Researched:** 2026-05-09
**Overall confidence:** HIGH for yt-dlp/YouTube compatibility and output/retry pitfalls; MEDIUM for service-scale API evolution pitfalls

## Critical Pitfalls

Mistakes here commonly force rewrites, create unreliable batch behavior, or make later API/video expansion painful.

### Pitfall 1: Treating subtitle download as “easy mode” and discovering YouTube churn still breaks it
**What goes wrong:** Teams assume subtitle-only scope is stable because they are not downloading full video, then ship a thin wrapper that breaks whenever YouTube changes player logic, caption fetching behavior, or anti-bot protections.

**Why it happens:** Current yt-dlp documentation/changelog shows YouTube compatibility is a moving target even for subtitles. Recent releases include repeated fixes for subtitle extraction, automatic caption languages, impersonation for downloading subtitles, PO token support, and a now-important external JavaScript runtime path for full YouTube support.

**Consequences:**
- Random subtitle failures after YouTube-side changes
- “Works yesterday, broken today” incidents
- Emergency upgrades and support burden
- Architecture drift if the tool hardcodes assumptions about extractor behavior

**Warning signs:**
- Success rate drops after no local code change
- Same URL works in browser but fails in tool
- Frequent extractor-specific errors or sudden 403/429 spikes
- Team treats yt-dlp as a frozen dependency instead of an actively changing upstream

**Prevention:**
- Build around a replaceable/upgradeable download kernel adapter from day 1
- Persist yt-dlp version, runtime environment, and invocation options with each run
- Add a compatibility health check command against a small canary URL set
- Support fast yt-dlp upgrades independently from app releases
- Prefer nightly/master fallback process for break/fix operations; official docs explicitly note stable can become stale and nightly is recommended for regular users

**Detection:**
- Daily canary jobs start failing on multiple known-public videos
- Failure clusters around extractor changes rather than one playlist/user input

**Which phase should address it:** Phase 1 — core download kernel abstraction and observability

---

### Pitfall 2: Not planning for required runtime/dependency drift around yt-dlp
**What goes wrong:** Project wraps yt-dlp but assumes “Python package installed” is enough. Later YouTube support fails because required supporting pieces are missing or outdated.

**Why it happens:** yt-dlp now strongly recommends `ffmpeg`, `ffprobe`, `yt-dlp-ejs`, and a supported JS runtime such as Deno/Node/QuickJS/Bun for full YouTube support. Teams often discover this only after field failures.

**Consequences:**
- Environment-specific breakage
- “Works on dev machine, fails on CI/server” problems
- Subtitle conversion and future video download blocked by missing ffmpeg

**Warning signs:**
- Setup docs say only `pip install yt-dlp`
- No startup validation for ffmpeg / JS runtime / optional networking deps
- Manual bug reports begin with “please install ffmpeg” or “update yt-dlp”

**Prevention:**
- Add a preflight command that verifies yt-dlp version, ffmpeg, JS runtime, and optional dependencies
- Separate “required for subtitle-only MVP” from “required for future video support,” but validate both paths early
- Log dependency matrix in run manifests for support/debugging
- Package a known-good environment profile for local use and future server deployment

**Detection:**
- Failures correlate with machine/environment, not URL
- Subtitle conversion to SRT/TXT fails while raw download succeeds

**Which phase should address it:** Phase 1 — installation, preflight, and environment validation

---

### Pitfall 3: Designing retries as “keep trying forever” instead of classifying failure types
**What goes wrong:** Tool retries everything indiscriminately, including extractor bugs, playlist continuation glitches, 429 throttling, or missing captions, causing slow jobs, hanging jobs, or infinite loops.

**Why it happens:** yt-dlp exposes many retry knobs (`retries`, `fragment_retries`, `extractor_retries`, `retry_sleep`), which tempts wrappers to just raise them globally. But real YouTube failures differ: some are transient, some are structural, and some get worse when retried.

**Consequences:**
- Stuck playlist jobs
- Massive time waste on non-retryable cases
- IP reputation damage from aggressive reattempts
- Operators cannot tell transient errors from permanent no-caption cases

**Warning signs:**
- Use of `infinite` retries in defaults
- No distinction between HTTP 429/5xx, private/deleted videos, no subtitle track, and extractor errors
- Same item retried many times with identical terminal error

**Prevention:**
- Implement your own retry policy above yt-dlp with bounded attempts and jittered backoff
- Classify outcomes into: retryable transient, retryable throttling, permanent unavailable, permanent unsupported, and unknown
- Never default to infinite extractor retries for YouTube playlists
- Persist per-item attempt history so reruns resume intelligently instead of blindly repeating
- Make “retry failed items only” a first-class workflow

**Detection:**
- Long tail of jobs consuming most runtime
- Logs show repeated identical extractor or subtitle errors for same video/language

**Which phase should address it:** Phase 2 — batch resilience, retries, reruns, and failure taxonomy

---

### Pitfall 4: Modeling playlist jobs as one monolithic operation instead of many item jobs
**What goes wrong:** A playlist URL is treated as one big download transaction. One bad video, continuation bug, or throttling wave makes the whole playlist feel failed.

**Why it happens:** CLI-first prototypes often call yt-dlp once per playlist and treat the entire stdout/stderr stream as the job model. That is too coarse for restartability, task manifests, and later APIization.

**Consequences:**
- Poor partial-success handling
- Hard to resume failed subsets
- Difficult API status reporting
- One failure obscures 90% successful work

**Warning signs:**
- Job status is only SUCCESS/FAILED at playlist level
- No persistent per-video manifest entries
- No item-level result store for language/status/output paths

**Prevention:**
- Normalize playlist input into per-video task records even if yt-dlp does bulk extraction underneath
- Store playlist-level manifest plus item-level state machine
- Separate extraction/enumeration from artifact download state
- Keep per-item error/result summaries and aggregate playlist rollups

**Detection:**
- Users must rerun an entire playlist to recover 3 failed entries
- API cannot answer “which items failed and why?”

**Which phase should address it:** Phase 1 for data model, Phase 2 for resumable execution

---

### Pitfall 5: Assuming `download-archive` is enough to solve replay, dedupe, and idempotency
**What goes wrong:** Team leans entirely on yt-dlp’s `--download-archive`, then later discovers it only records successful downloads, is not a full task ledger, and does not model multi-language subtitle state or custom output semantics.

**Why it happens:** `download-archive` is useful, but it is a skip list, not a complete workflow database. It also is not an output template, so people frequently try to scope archive files per playlist directory using templated paths and hit limitations.

**Consequences:**
- Duplicate work on reruns
- No precise knowledge of which language/format succeeded
- Hard migration from CLI tool to API/stateful service
- Confusing behavior when archive location/output organization is dynamic

**Warning signs:**
- Design says “archive.txt will be our source of truth”
- No separate manifest for requested languages, output formats, attempts, and statuses
- Plan assumes archive file path can be templated by playlist metadata

**Prevention:**
- Use `download-archive` only as a low-level optimization, not as primary state
- Create your own manifest/store keyed by normalized task identity: `{video_id, language, output_format, mode}`
- Treat reruns as idempotent writes into deterministic artifact paths
- Keep separate states for discovered / requested / downloaded / converted / failed

**Detection:**
- Repeated runs create confusing duplicates or skip too much
- Team cannot answer whether `en` failed while `en-US` succeeded for same video

**Which phase should address it:** Phase 1 — manifest schema and idempotent task identity

---

### Pitfall 6: Weak output organization that is human-friendly once but machine-hostile forever
**What goes wrong:** Output paths are chosen for ad hoc browsing only, often title-based, with no deterministic identifiers, no separation by artifact type, and no stable mapping between source item and generated files.

**Why it happens:** Download tools default to filename templates optimized for interactive use, not for reprocessing, APIs, or partial reruns.

**Consequences:**
- File collisions across same/similar titles
- Impossible-to-predict API responses
- Painful later video support because subtitle-centric naming does not generalize
- Fragile scripts that guess filenames instead of reading manifests

**Warning signs:**
- Paths depend only on title or playlist title
- No inclusion of video ID in canonical identity
- Subtitle files, metadata, logs, and manifests scattered together without contract

**Prevention:**
- Define canonical directory contract early, e.g. job/playlist/item/artifact separation
- Always include video ID in canonical storage keys even if friendly names are preserved for display
- Separate raw subtitle, converted subtitle, metadata JSON, logs, and future video outputs
- Make manifest the source of truth for file paths; filenames are outputs, not API contracts

**Detection:**
- Two different videos can produce same path
- Code has to glob directories to “find the subtitle file”

**Which phase should address it:** Phase 1 — output contract and artifact manifest

---

### Pitfall 7: Underestimating filename/path edge cases for multilingual subtitle exports
**What goes wrong:** Long playlist titles, uploader names, non-ASCII languages, temporary suffixes, and language codes produce paths that fail on some filesystems or vary unpredictably.

**Why it happens:** yt-dlp output templates can exceed filesystem byte limits, and subtitle outputs intentionally append language-related suffixes. Projects often assume `-o transcript.srt` means exactly one resulting filename.

**Consequences:**
- “Filename too long” failures mid-run
- Broken automation because output names differ from expectation
- Cross-platform bugs, especially Windows/path-length/shell quoting issues

**Warning signs:**
- Hardcoded fixed filenames for subtitle output
- No byte-length trimming in output templates
- Assumption that converted subtitle filename will exactly match requested base name

**Prevention:**
- Use yt-dlp template controls deliberately; trim by bytes, not just characters
- Design around manifest-returned actual file paths, not predicted names
- Reserve separate subtitle output templates when needed instead of reusing video templates
- Test with long titles, non-Latin text, multiple subtitle languages, and Windows-style shells

**Detection:**
- Failures only on certain titles/playlists/languages
- Users report unexpected `.en.vtt` / `.en-US.srt` suffix behavior

**Which phase should address it:** Phase 1 — output template design and cross-platform test fixtures

---

### Pitfall 8: Mixing raw subtitles, cleaned text, and converted formats without provenance
**What goes wrong:** Tool exports VTT/SRT/TXT but does not preserve which TXT came from which raw track, language, or cleaning rules.

**Why it happens:** Subtitle-first tools often optimize for “get me text fast” and flatten all exports into one file without lineage.

**Consequences:**
- Hard to debug bad transcript quality
- Impossible to reproduce cleaning results later
- API consumers cannot know whether text came from manual captions, auto captions, or post-processed output

**Warning signs:**
- TXT file has no sidecar metadata
- No distinction between manual and auto-generated captions in manifest
- Cleaning/conversion logic is implicit in code, not recorded in output

**Prevention:**
- Store raw timed subtitle artifact and derived clean text together
- Persist provenance fields: source track type, language code, original format, conversion steps, and timestamps
- Expose artifact types distinctly in CLI output and future API

**Detection:**
- Team cannot reproduce a user’s TXT output from saved artifacts
- Later analytics use cases question transcript trustworthiness

**Which phase should address it:** Phase 1 — artifact model; Phase 2 — conversion/cleaning pipeline

---

### Pitfall 9: Treating subtitle language selection as a simple string option
**What goes wrong:** Product UI/CLI implies “language=en” is enough, but real behavior involves manual vs auto captions, regional variants (`en`, `en-US`), regex selection, missing tracks, and multiple matched outputs.

**Why it happens:** yt-dlp supports rich subtitle language selection, but naive wrappers collapse that into a single simplistic flag.

**Consequences:**
- User confusion when requested language is absent but a variant exists
- Surprising extra files when multiple variants match
- Hard-to-debug 429s or excess requests if config merges requested languages unintentionally

**Warning signs:**
- CLI/API has only one `language` string and no mode semantics
- No manifest field for requested vs resolved subtitle language
- Global config and per-run language flags can silently combine

**Prevention:**
- Define explicit language selection semantics: exact, preferred list, regex, all, manual-only, auto-allowed
- Record requested language spec and resolved track(s) separately
- Always expose whether output came from auto subtitles or human subtitles
- Isolate your app config from ambient global yt-dlp config where possible

**Detection:**
- “Why did I get en-US instead of en?”
- Same command behaves differently on machines with different yt-dlp configs

**Which phase should address it:** Phase 1 — CLI/API contract for language selection

---

### Pitfall 10: Letting ambient yt-dlp config leak into application behavior
**What goes wrong:** A developer or user has system/user yt-dlp config files that inject output templates, subtitle languages, or other flags, producing behavior the application did not request.

**Why it happens:** yt-dlp supports system and user configuration loading. Embedded wrappers that do not control config loading can inherit surprising defaults.

**Consequences:**
- Non-reproducible bugs
- Hidden extra subtitle requests, wrong paths, or unexpected download modes
- Support burden because “same command” behaves differently across machines

**Warning signs:**
- Verbose output shows config files being loaded unexpectedly
- Bug only reproduces on one machine
- Output path or language behavior differs from app configuration

**Prevention:**
- Decide explicitly whether to ignore external yt-dlp config in app mode
- Log effective option set for every job
- Prefer application-owned config assembly over inheriting user/system config by default
- Add diagnostics that print loaded config locations and effective options

**Detection:**
- Removing a user config file suddenly “fixes” the app
- Debug logs show unplanned flags such as extra `--sub-lang en`

**Which phase should address it:** Phase 1 — deterministic invocation and diagnostics

---

### Pitfall 11: Assuming subtitle failure should behave exactly like video failure
**What goes wrong:** Later, when video download is added, the system has no nuanced policy for “video succeeded but subtitle failed” or “subtitle succeeded but conversion failed.”

**Why it happens:** Subtitle-first MVPs often encode a binary success/failure model. That becomes wrong once artifacts multiply.

**Consequences:**
- Wrong overall job status
- Users rerun everything because one artifact type failed
- API design becomes awkward and inconsistent

**Warning signs:**
- One boolean `success` per item
- No artifact-level result tracking
- Error handling only at command exit-code level

**Prevention:**
- Model status per artifact class: metadata, subtitle raw, subtitle converted, video, thumbnail, log
- Define aggregate status rules: success, partial_success, failed, skipped
- Make reruns target missing/failed artifacts only

**Detection:**
- Operators cannot distinguish “usable result with missing TXT” from “complete failure”

**Which phase should address it:** Phase 2 — artifact-level state machine before video expansion

---

### Pitfall 12: Painting the architecture into a CLI-only corner
**What goes wrong:** Early implementation directly couples parsing stdout, console progress, local filesystem assumptions, and synchronous process flow. Later API work requires a rewrite.

**Why it happens:** MVP pressure encourages a single script that “just shells out.” That is fine for a spike, not for a roadmap that explicitly targets future API/service use.

**Consequences:**
- Rewrite before API launch
- No clean cancellation/progress/status endpoints
- Hard to move from single-user local runs to queued jobs

**Warning signs:**
- Business logic lives in CLI command handlers
- No domain model for job, item, artifact, attempt
- Parsing human-readable logs is the only source of status

**Prevention:**
- Keep yt-dlp adapter, orchestration, persistence, and presentation layers separate
- Emit structured events/status records independent of terminal formatting
- Treat CLI as one client of a reusable application service layer
- Define cancellation, timeout, and progress concepts even if CLI is the only frontend initially

**Detection:**
- API planning begins with “how do we expose this shell script?”
- Progress is readable by humans but not by code

**Which phase should address it:** Phase 1 — service-oriented core beneath CLI

---

### Pitfall 13: Designing subtitle-only storage that blocks clean video expansion later
**What goes wrong:** The folder layout, manifest schema, and task identity encode subtitle assumptions so deeply that adding video creates incompatible naming, state, and retention models.

**Why it happens:** Subtitle-first is mistaken for subtitle-only. Long-term requirements in this project explicitly say video becomes a co-equal core capability later.

**Consequences:**
- Migration scripts and breaking changes
- Duplicate metadata models for subtitle vs video mode
- Confusing API contracts

**Warning signs:**
- Manifest key is just `{video_id -> subtitle_path}`
- No place for multiple artifact variants per video
- Output directories named only around transcript concepts

**Prevention:**
- Use an artifact-centric model from the start: one source item, many artifact types
- Reserve namespaces for video/audio/thumbnail/metadata alongside subtitle artifacts
- Keep “download mode” in task identity instead of baking it into schema implicitly

**Detection:**
- Video support design requires renaming core entities or moving all outputs

**Which phase should address it:** Phase 1 — schema and storage design with future video in mind

---

### Pitfall 14: Ignoring anti-bot/rate-limit behavior until batch scale exposes it
**What goes wrong:** Small manual tests pass, but playlist and bulk runs hit 429s, empty or partial responses, or soft blocks.

**Why it happens:** YouTube tolerance differs sharply between one-off and bursty batch access. Subtitle fetching is not immune.

**Consequences:**
- Unreliable playlist execution
- Spiky failure rates under load
- Misleading “no subtitles available” conclusions that are actually throttling symptoms

**Warning signs:**
- Success rate collapses only for larger batches
- 429s cluster by run intensity/time, not by content type
- No pacing between requests/subtitle fetches

**Prevention:**
- Add bounded concurrency and pacing controls early
- Use backoff with jitter on 429/5xx classes
- Track empty/partial-response anomalies separately from true “missing subtitle” cases
- Support cookies/browser-based auth workflows for cases requiring CAPTCHA recovery or user context

**Detection:**
- Same videos succeed when rerun slowly or individually
- Captions appear missing during batch runs but available in later manual reruns

**Which phase should address it:** Phase 2 — concurrency, pacing, and throttling controls

## Moderate Pitfalls

### Pitfall 1: Using `flat-playlist`/lazy playlist semantics without understanding metadata tradeoffs
**What goes wrong:** Faster playlist enumeration is chosen, but required metadata for output naming, filtering, or manifests is absent or delayed.

**Prevention:**
- Decide which metadata is required before choosing flat/lazy modes
- Separate “enumeration fast path” from “full extraction for selected items”

**Warning signs:** Missing playlist item fields during naming or filtering.

**Which phase should address it:** Phase 2

### Pitfall 2: Overusing shell-based `--exec` glue for core behavior
**What goes wrong:** Important file moves, manifest writes, or post-processing live in shell snippets with quoting/security portability problems.

**Prevention:**
- Keep critical orchestration in application code, not shell hooks
- If `--exec` is ever used, quote safely and treat it as optional integration glue only

**Warning signs:** Core correctness depends on shell expansion or platform-specific commands.

**Which phase should address it:** Phase 1

### Pitfall 3: Confusing “captions unavailable” with “captions inaccessible in current run context” 
**What goes wrong:** Tool reports no subtitles when the real issue is auth, rate limiting, regional restrictions, or extractor breakage.

**Prevention:**
- Return explicit unavailability reasons where possible
- Distinguish no-track, private/restricted, throttled, and unknown failures in manifests/logs

**Warning signs:** High “no subtitles” rate combined with intermittent success on rerun.

**Which phase should address it:** Phase 2

## Minor Pitfalls

### Pitfall 1: Hardcoding TXT cleaning assumptions
**What goes wrong:** Cleaning logic strips too much structure or cannot be revised later.

**Prevention:**
- Keep raw and cleaned outputs both
- Version the cleaning pipeline in metadata

**Which phase should address it:** Phase 2

### Pitfall 2: Assuming one URL type = one extractor behavior
**What goes wrong:** Shorts, playlists, channels, scheduled/live items, or age-restricted videos behave differently than standard watch URLs.

**Prevention:**
- Build URL normalization and capability detection into manifests and diagnostics

**Which phase should address it:** Phase 1

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Core kernel wrapper | Tight-coupling to one yt-dlp invocation shape | Create adapter boundary; persist version/options per run |
| CLI contract | Simplistic `--lang` semantics | Support exact/preferred/regex/manual-vs-auto modes |
| Output organization | Title-only filenames and mixed artifacts | Use deterministic IDs and separate artifact namespaces |
| Retry/rerun | Infinite or undifferentiated retries | Bounded retry classes + item-level manifests |
| Playlist support | Monolithic playlist job model | Normalize to playlist + item states |
| Logging/diagnostics | Human-only logs | Structured manifests and machine-readable status events |
| Subtitle conversion | Dropping provenance | Keep raw + converted outputs and record transformations |
| API-readiness | CLI script becomes de facto backend | Separate orchestration core from presentation layer |
| Video expansion | Subtitle-centric schema cannot generalize | Use artifact-centric model from day 1 |
| YouTube compatibility | Slow upstream upgrade response | Add canary checks and fast dependency upgrade path |

## Sources

### HIGH confidence
- yt-dlp README (current master): https://github.com/yt-dlp/yt-dlp/blob/master/README.md
- yt-dlp FAQ (output templates, archive behavior, 429/cookies, path handling): https://github.com/yt-dlp/yt-dlp-wiki/blob/master/FAQ.md
- Context7 docs for `/yt-dlp/yt-dlp` (embedding, subtitles, playlists, output templates, retries)
- yt-dlp changelog/search excerpts showing recent YouTube subtitle and compatibility churn (2025–2026): https://github.com/yt-dlp/yt-dlp/blob/master/Changelog.md

### MEDIUM confidence
- yt-dlp issue #8206 on playlist incomplete-data retry behavior: https://github.com/yt-dlp/yt-dlp/issues/8206
- yt-dlp issue #2082 on subtitle/template duplication behavior: https://github.com/yt-dlp/yt-dlp/issues/2082
- yt-dlp issue #2503 and #9962 on archive-file templating limitations: https://github.com/yt-dlp/yt-dlp/issues/2503 , https://github.com/yt-dlp/yt-dlp/issues/9962
- yt-dlp issue #9680 on subtitle filepath retrieval and artifact-specific paths: https://github.com/yt-dlp/yt-dlp/issues/9680
- yt-dlp issue #14588 on config leakage / subtitle language interaction: https://github.com/yt-dlp/yt-dlp/issues/14588
- YTVidHub engineering article for queue/idempotency/provenance ideas (useful pattern source, not authoritative for yt-dlp behavior): https://ytvidhub.com/blog/engineering-decisions-ytvidhub/

## Research Notes / Gaps

- I did not verify a single “best” server-side queue architecture because this milestone asked for pitfalls, not a full architecture recommendation.
- Some rate-limit/throttling prevention tactics beyond official yt-dlp guidance are inherently unstable over time; treat them as operational tuning, not product guarantees.
