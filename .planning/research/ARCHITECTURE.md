# Architecture Patterns

**Domain:** CLI-first YouTube subtitle/video downloader, designed to expand into an API
**Researched:** 2026-05-09
**Overall confidence:** MEDIUM-HIGH

## Recommended Architecture

Build this as a **layered application with a shared download core**, not as “a CLI script now, then rewrite as a web service later.”

The right shape is:

```text
CLI / API Adapters
        ↓
Application Services / Use Cases
        ↓
Job + Manifest + Output Management
        ↓
Download Engine Adapter (yt-dlp wrapper)
        ↓
Filesystem / External binaries / YouTube
```

This structure fits the project constraints well:

- v1 is local and CLI-first
- the long-term product needs API readiness
- the system must persist subtitle files, metadata, logs, and rerunnable task manifests
- the project should wrap a mature download core instead of reimplementing extraction logic

**Opinionated recommendation:** use **one shared core library** that both the CLI and future API call. The CLI should be a thin adapter. The API should also be a thin adapter. The download workflow, manifest logic, output layout, retries, and yt-dlp option mapping should live below both.

## High-Level Component Map

```text
[CLI Commands] ───────────────┐
                              │
[Future FastAPI Endpoints] ───┤
                              ↓
                    [Application Service Layer]
                    - plan job
                    - validate request
                    - expand playlist/video targets
                    - execute or enqueue work
                    - collect outcomes
                              ↓
                    [Job Orchestrator]
                    - task graph / per-item execution
                    - retry / resume semantics
                    - progress events
                    - state transitions
                              ↓
      ┌───────────────────────┼────────────────────────┐
      ↓                       ↓                        ↓
[Manifest Store]      [Output Manager]         [Download Engine Adapter]
- job spec            - directory layout        - yt-dlp options builder
- item state          - filenames               - metadata extraction
- rerun inputs        - metadata JSON           - subtitle download
- history/log refs    - logs                    - future video download
      │               - normalized exports      - progress hooks
      │                        │                        │
      └──────────────→ [Filesystem] ←──────────────────┘
                                      │
                                      ↓
                             [yt-dlp / ffmpeg / network]
```

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| CLI adapter | Parse command flags, print progress, map exit codes, call application services | Application services only |
| API adapter (future) | Validate HTTP payloads, create jobs, expose job status/results, return 202 + polling handles for long jobs | Application services only |
| Application service layer | Main use cases: inspect URL, plan download, run subtitle batch, rerun failures, export formats | CLI/API adapters, job orchestrator, manifest store, output manager |
| Job orchestrator | Convert a request into executable item tasks; manage per-video state, retries, cancellation hooks, progress emission | Application services, manifest store, download engine adapter, output manager |
| Manifest store | Persist job request, expanded target list, per-item status, errors, timestamps, rerun eligibility | Application services, job orchestrator |
| Output manager | Own output root, naming conventions, file placement, metadata JSON, subtitle conversion outputs, log files | Application services, job orchestrator, download engine adapter |
| Download engine adapter | Single wrapper around yt-dlp embedding/API options; normalize calls for metadata extraction, subtitles, future video downloads | Job orchestrator, output manager |
| Subtitle conversion layer | Convert raw subtitle artifacts into target formats like vtt/srt/txt and normalize language/output naming | Download engine adapter, output manager |
| Progress/event publisher | Emit structured lifecycle events for terminal progress now and API/SSE/WebSocket later | Job orchestrator, CLI/API adapters |
| Config layer | Resolve defaults from env/config/project settings and translate them into internal request models | CLI/API adapters, application services |

## Boundary Rules

These rules matter because they prevent the later API from forcing a rewrite.

### 1) CLI must not call yt-dlp directly
The CLI should never assemble raw yt-dlp options or write output files itself. It should call a service like `download_subtitles(request)` and render the returned result.

### 2) The yt-dlp wrapper must be the only download engine boundary
All direct usage of `yt_dlp.YoutubeDL(...)`, `extract_info(...)`, `download(...)`, progress hooks, and subtitle-related options should be isolated in one adapter module. Context7 and the yt-dlp docs confirm these embedding points exist and are the intended programmatic interface.

### 3) Manifest state must be first-class, not derived ad hoc from files
Do not infer job status only from “which subtitle files exist.” Persist a manifest with requested languages, expanded targets, item states, errors, and paths. This is the bridge from local CLI runs to API job polling.

### 4) Output layout must be owned by one component
File naming and directory rules should not be spread across CLI commands and download code. Centralize them so rerun, import, API download links, and debugging all point at the same conventions.

### 5) Progress should be event-based, not print-based
yt-dlp supports progress hooks; use them to emit internal events. The CLI can render those to stdout. The future API can expose the same events via polling or streaming.

## Data Flow

### Primary flow: subtitle batch download

```text
User input URL(s) + languages + output options
        ↓
CLI/API adapter validates and builds internal request model
        ↓
Application service creates Job record + initial manifest
        ↓
URL inspection step extracts metadata / playlist entries
        ↓
Job orchestrator expands into per-video work items
        ↓
For each item:
  Download engine adapter calls yt-dlp
        ↓
  Raw metadata + subtitle artifacts returned/written
        ↓
  Subtitle conversion layer generates requested formats
        ↓
  Output manager writes files to stable directory layout
        ↓
  Manifest store updates item status + file paths + errors
        ↓
Application service summarizes results
        ↓
CLI prints summary / API returns status handle or result
```

### Inspection flow: dry-run / planning mode

```text
Input URL
  ↓
Application service calls download engine adapter in metadata-only mode
  ↓
Expanded item list + available subtitles/languages + normalized metadata
  ↓
Manifest draft or preview response
```

This is important because yt-dlp supports metadata extraction without downloading via `extract_info(..., download=False)`, and `sanitize_info()` is recommended before serializing data for API or manifest usage.

### Rerun flow

```text
Existing manifest/job id
  ↓
Application service loads manifest
  ↓
Select failed / missing / filtered items
  ↓
Job orchestrator re-executes only those items
  ↓
Manifest store updates prior state with new attempt records
```

## Recommended Internal Modules

Use module boundaries like these even if the codebase starts small:

```text
src/
  app/
    cli/
    api/                 # future
  services/
    inspect.py
    download_subtitles.py
    rerun_job.py
  domain/
    models.py            # job, item, output, language, status
    policies.py          # naming, retry, filtering rules
  orchestration/
    jobs.py
    progress.py
  infrastructure/
    yt_dlp_adapter.py
    manifest_store.py
    output_manager.py
    subtitle_converter.py
    config.py
```

The exact folders can vary. The important part is the dependency direction:

```text
cli/api → services → orchestration/domain → infrastructure adapters
```

Not the reverse.

## Patterns to Follow

### Pattern 1: Adapter + Use Case separation
**What:** Treat CLI and future API as delivery adapters over the same use cases.

**When:** From day one.

**Why:** This is the single highest-value architectural choice for a CLI-first tool that is expected to become a service.

**Example:**

```python
def download_subtitles(request: DownloadSubtitlesRequest) -> JobResult:
    job = manifest_store.create(request)
    items = planner.expand_targets(request)
    for item in items:
        orchestrator.run_item(job.id, item)
    return manifest_store.build_result(job.id)
```

CLI command:

```python
@app.command()
def subtitles(url: str, lang: list[str]):
    result = download_subtitles(
        DownloadSubtitlesRequest(urls=[url], languages=lang)
    )
    render_cli_result(result)
```

Future API route:

```python
@router.post("/jobs")
def create_job(payload: DownloadRequest):
    job = submit_download_job(payload)
    return {"job_id": job.id, "status": job.status}
```

### Pattern 2: Two-phase execution — inspect, then download
**What:** Separate “expand and inspect targets” from “download artifacts.”

**When:** For playlists, multi-language selection, reruns, and preview commands.

**Why:** Prevents brittle one-shot scripts. Also makes manifests and API job creation much cleaner.

### Pattern 3: Per-item state machine
**What:** Each playlist entry or video should move through states like `pending -> inspecting -> ready -> downloading -> converting -> completed/failed`.

**When:** Always, even for CLI.

**Why:** This is how you make retries, reruns, logs, and API status endpoints coherent.

### Pattern 4: Stable output contract
**What:** Every completed item should produce a predictable bundle:

- source metadata JSON
- manifest/job reference
- raw subtitle artifacts if retained
- converted subtitle outputs (srt/txt/vtt)
- per-item error or log record if failed

**When:** From v1.

**Why:** The persisted artifact contract is part of the product, not just an implementation detail.

### Pattern 5: Event sink abstraction
**What:** Internal events such as `job_created`, `item_started`, `progress`, `item_failed`, `item_completed` should be emitted to an interface.

**When:** Early.

**Why:** The CLI sink prints them; a later API sink stores them or streams them.

## Anti-Patterns to Avoid

### Anti-Pattern 1: “Thin wrapper around subprocess command strings”
**What:** Building shell commands in CLI handlers and executing `yt-dlp ...` directly.

**Why bad:** Hard to test, hard to reuse in API, hard to normalize errors, and harder to persist structured metadata.

**Instead:** Use a dedicated adapter around embedded yt-dlp calls.

### Anti-Pattern 2: One giant command function
**What:** URL parsing, file naming, download calls, conversion, logging, and retries all inside one CLI command.

**Why bad:** Guarantees rewrite pressure when API arrives.

**Instead:** Keep command handlers shallow.

### Anti-Pattern 3: Treating FastAPI BackgroundTasks as a durable job system
**What:** Using in-process background tasks as if they were a resilient queue for long-running downloads.

**Why bad:** FastAPI’s own docs explicitly position `BackgroundTasks` for smaller same-process work and recommend bigger tools like Celery when you need heavier multi-process or multi-server jobs.

**Instead:**
- **Early API stage:** in-process job runner is acceptable for single-user/self-hosted usage if job state is persisted and limitations are explicit.
- **Later scale-up stage:** move execution behind a proper worker queue.

### Anti-Pattern 4: Filesystem-as-only-database
**What:** Assuming file existence alone is enough to know whether a job ran successfully.

**Why bad:** Breaks rerun semantics, partial failure visibility, and API status reporting.

**Instead:** Persist manifests and execution records explicitly.

### Anti-Pattern 5: Video path bolted on separately later
**What:** Building subtitle-only internals that cannot generalize to video/media artifacts.

**Why bad:** Creates a second pipeline later.

**Instead:** Model “artifact types” now. Subtitle is the first artifact, video is the next one.

## Suggested Build Order

This project’s roadmap should follow dependency order, not user-visible surface area alone.

### Phase 1: Core domain + output contract
Build first:

1. request/result/domain models
2. manifest schema
3. output directory conventions
4. status/error model

**Why first:** Every interface and workflow depends on these contracts.

### Phase 2: yt-dlp adapter + inspection mode
Build next:

1. metadata extraction wrapper
2. subtitle capability detection / language listing
3. playlist expansion
4. JSON-safe metadata normalization

**Why second:** Inspection is lower risk than full download and validates the engine boundary early.

### Phase 3: subtitle download pipeline
Build next:

1. per-item execution
2. subtitle download
3. conversion to requested formats
4. manifest updates and failure handling

**Why third:** This is the first full product slice and the validated v1 goal.

### Phase 4: CLI UX layer
Build once the core path exists:

1. Typer command groups
2. progress rendering
3. summary/report output
4. rerun commands

**Why fourth, not first:** CLI syntax is cheap to change; core workflow boundaries are not.

### Phase 5: local API wrapper
Build after the CLI core is stable:

1. FastAPI endpoints for job creation/status/result listing
2. adapter from HTTP request -> same services
3. local in-process runner or simple worker loop
4. optional polling/SSE progress exposure

**Why fifth:** The API should wrap proven workflows, not define them.

### Phase 6: video download capability
Add after subtitle pipeline is reliable:

1. artifact model extension for media outputs
2. ffmpeg-aware post-processing paths
3. larger file storage rules
4. richer retry/error taxonomy

**Why sixth:** Video introduces new storage, performance, and post-processing complexity. It should reuse the same job/orchestration/output architecture, not fork it.

## Build-Order Implications for Roadmap

```text
Domain models/output contract
  → yt-dlp adapter / inspect flow
    → manifest persistence
      → subtitle execution pipeline
        → CLI commands
          → rerun / batch ergonomics
            → API layer
              → queue/worker hardening
                → video pipeline
```

Key implication: **do not define the roadmap as “CLI first, API later” in interface terms only.** Define it as:

1. shared core first
2. CLI over the core
3. API over the same core

That is what avoids a rewrite.

## Scalability Considerations

| Concern | At 100 users / personal use | At 10K jobs / team use | At 1M jobs / service scale |
|---------|-----------------------------|------------------------|----------------------------|
| Job execution | In-process orchestration is acceptable | Separate worker process recommended | Durable distributed queue required |
| State storage | Local JSON/SQLite manifest is acceptable | SQLite/Postgres strongly preferred | Postgres + object storage + queue |
| Progress delivery | CLI stdout | polling or SSE | SSE/WebSocket + event backend |
| File storage | Local filesystem | shared volume/object storage planning needed | object storage mandatory |
| Failure recovery | manual rerun via manifest | automated retries + worker restart recovery | idempotent job execution + lease/lock semantics |

## Architecture Recommendation in One Sentence

**Structure the system as a shared download-core application with thin CLI/API adapters, explicit manifest persistence, and a single yt-dlp integration boundary; build inspect → manifest → subtitle pipeline first, then add API and later video on the same execution model.**

## Sources

- yt-dlp embedding/API usage via `YoutubeDL`, `extract_info`, `download`, `progress_hooks`, and `sanitize_info`: Context7 `/yt-dlp/yt-dlp` and official README/GitHub docs — **HIGH confidence**
- FastAPI `BackgroundTasks` usage and caveat that heavy/durable jobs should use bigger queue tools like Celery: official FastAPI docs — **HIGH confidence**
- Typer command-group modular structure via `Typer()` and `add_typer()`: Context7 `/fastapi/typer` and official Typer docs — **HIGH confidence**
- Shared-core / adapter-first architecture and build-order recommendations: architecture synthesis based on project constraints plus verified library capabilities — **MEDIUM confidence**
