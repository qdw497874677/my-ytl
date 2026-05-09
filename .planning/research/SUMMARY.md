# Project Research Summary

**Project:** YouTube subtitle/video downloader tool
**Domain:** CLI-first YouTube subtitle downloader with future API and video expansion
**Researched:** 2026-05-09
**Confidence:** HIGH

## Executive Summary

This project is best treated as a **workflow-oriented downloader**, not a one-off paste-and-download utility. The research consistently points to a subtitle-first CLI that wraps **yt-dlp** as the download kernel, persists **manifests/logs/artifacts** as first-class outputs, and keeps a clean path to a later **FastAPI** service layer. Experts do not rebuild extractor logic here; they isolate yt-dlp behind an adapter, standardize output contracts, and model playlist work as many item-level tasks rather than one opaque batch command.

The recommended approach is opinionated: build a **shared Python 3.13 core** with **Typer + Rich** for the CLI, **Pydantic v2** for request/result/manifests, **structlog** for structured logs, **filesystem-first persistence**, and **FFmpeg/FFprobe** plus the yt-dlp JavaScript runtime support planned from day one. The product promise for MVP is not “download anything from anywhere.” It is: reliably inspect YouTube URLs, fetch subtitles in batch, choose languages and export formats, persist deterministic outputs, and rerun failures safely.

The key risks are operational rather than UI-related. YouTube compatibility churn, dependency/runtime drift, naive retry behavior, playlist-level monolith execution, and weak output/manifests are the failure modes most likely to cause rewrites or unreliable behavior. The mitigation is also consistent across the research: isolate the yt-dlp boundary, persist rich per-item state, classify failures, keep outputs deterministic, and build inspect → manifest → execute as the foundational workflow before adding API or full video support.

## Key Findings

### Recommended Stack

The stack research is unusually clear: **Python is the right runtime because the core dependency already lives there**, and the project should optimize for downloader reliability and operational clarity rather than framework novelty. The most durable shape is a layered Python app whose CLI and later API both call the same service layer over a yt-dlp adapter.

Critical versioning guidance also matters here. Pin **yt-dlp exactly and update it aggressively**, pin framework minors more calmly, require **FFmpeg >=7.1 and prefer 8.1.x**, and treat **yt-dlp-ejs + a JS runtime** as part of real-world YouTube support rather than an optional afterthought.

**Core technologies:**
- **Python 3.13**: primary runtime — best fit for yt-dlp integration, CLI/API reuse, and modern typed tooling.
- **uv**: package/project management — fast, reproducible environments with low overhead for a utility-style repo.
- **yt-dlp (2026.3.17 pinned)**: download/extraction engine — the de facto maintained YouTube downloader core.
- **FFmpeg / FFprobe (prefer 8.1.x)**: media/post-processing infrastructure — required for future video and useful early for probing/conversion.
- **yt-dlp-ejs + JS runtime**: YouTube compatibility support — increasingly necessary for full YouTube support.
- **Typer + Rich**: CLI and terminal UX — typed commands, subcommand growth, readable progress, and machine-friendly summaries.
- **Pydantic v2 + structlog**: validation and observability — shared models for CLI/API/manifests plus structured logs for reruns and debugging.
- **FastAPI + Uvicorn**: future API layer — clean reuse of the same services once HTTP mode begins.
- **Filesystem-first persistence, then SQLite later**: storage approach — artifacts are the product now; indexed job state arrives with API mode.

### Expected Features

The product baseline is defined by serious downloader workflows, not by UI polish. For MVP, users will expect reliable **single-video and playlist subtitle download**, **multi-language selection**, **VTT/SRT/TXT export**, **metadata sidecars**, **job manifests/logs**, **deterministic output layout**, **skip/already-downloaded behavior**, **continue-on-error batch handling**, and **rerun failed items**.

The real differentiator is not “more downloader flags.” It is a **cleaner subtitle-first workflow model**: manifest-driven runs, better language fallback semantics, per-item artifact bundles, batch summaries, and API-ready task IDs/statuses. That is how this tool can feel more intentional than a generic yt-dlp wrapper while still reusing the mature core.

**Must have (table stakes):**
- Single video subtitle download by URL — minimum job-to-be-done.
- Playlist subtitle batch download — core requirement and power-user expectation.
- Multi-language subtitle selection — explicit requested languages plus fallback behavior.
- Subtitle export formats (VTT/SRT/TXT) — both machine- and human-friendly outputs.
- Metadata persistence per item — JSON sidecars for auditing, reruns, and future API use.
- Download logs and job manifest — source of truth for status, errors, and reruns.
- Deterministic output folder/file naming — automation-safe and human-usable.
- Skip/already-downloaded behavior — avoids waste on large playlists.
- Partial failure tolerance — continue through blocked/unavailable items.
- Retry/rerun failed items — first-class recovery workflow.
- Basic subtitle availability reporting — distinguish no captions from tool failure.
- Machine-friendly CLI output — JSON/NDJSON summaries for scripting.

**Should have (competitive):**
- Subtitle-first job manifest model — makes subtitles first-class artifacts rather than side effects.
- Rich language fallback policy — better than raw yt-dlp flag exposure.
- Clean transcript normalization pipeline — adds value for real subtitle consumers.
- Batch summary report — essential for large runs and later API use.
- Re-run by status filter — rerun only failed, missing-language, or subtitle-less items.
- URL intake normalization — reduces weird failures across watch/share/shorts/playlist URLs.
- API-ready task model from day one — stable IDs, enums, artifact records.
- Per-item artifact bundle — each item gets subtitles, metadata, and logs together.
- Safety/trust posture — explicit outputs, no shady downloader behavior.

**Defer (v2+):**
- Channel downloads and watch/subscription mode.
- Authenticated/private-content UX beyond simple passthrough.
- Full video quality/format selection and audio-only flows.
- Embedded subtitle/remux workflows.
- Multi-site support.
- Desktop GUI or browser extension.

### Architecture Approach

The architecture research strongly recommends a **shared-core layered system**: CLI and API adapters on top, application services/use cases beneath them, a job orchestrator managing per-item state, manifest/output components owning persistence contracts, and one yt-dlp adapter as the only downloader boundary. The essential execution pattern is **inspect first, then download**, with playlist jobs expanded into item-level state machines and progress emitted as structured events rather than raw prints.

**Major components:**
1. **CLI/API adapters** — validate input, map transport concerns, and call application services only.
2. **Application service layer** — inspect URLs, plan jobs, run subtitle batches, rerun failures, and summarize results.
3. **Job orchestrator** — manage per-item execution, retries, progress, and state transitions.
4. **Manifest store** — persist job specs, item states, errors, outputs, timestamps, and rerun eligibility.
5. **Output manager** — own deterministic directory layout, naming, sidecars, converted outputs, and log placement.
6. **Download engine adapter** — isolate yt-dlp embedding, option mapping, metadata extraction, and later video downloads.
7. **Subtitle conversion layer** — normalize/export raw subtitle artifacts into requested formats with provenance.
8. **Progress/event publisher** — emit structured lifecycle events for CLI rendering now and API polling/SSE later.

### Critical Pitfalls

The pitfalls research reinforces the roadmap order. Most failures come from treating the project like a thin wrapper script instead of a stateful downloader workflow system.

1. **Assuming subtitle-only means low maintenance** — YouTube churn still breaks subtitle extraction; avoid this with a replaceable yt-dlp adapter, canary checks, and fast upgrade paths.
2. **Ignoring dependency/runtime drift** — missing ffmpeg, ffprobe, yt-dlp-ejs, or JS runtime will create environment-specific failures; avoid with preflight validation and dependency logging.
3. **Using undifferentiated or infinite retries** — this wastes time and worsens throttling; avoid with bounded retry classes, backoff, and per-item attempt history.
4. **Treating playlists as one monolithic job** — this destroys partial success, reruns, and API status; avoid with playlist-level manifests plus item-level state machines.
5. **Relying on `download-archive` as the system of record** — it is a skip list, not a workflow ledger; avoid with an app-owned manifest keyed by item/language/format/mode.
6. **Weak output naming and artifact provenance** — title-only or flattened outputs break automation and future video support; avoid with canonical IDs, artifact namespaces, and manifest-owned paths.

## Implications for Roadmap

Based on the combined research, the roadmap should follow **shared core first, interface second, expansion third**. The right dependency order is not “build CLI commands, then later clean them up.” It is: define the job/output contract, prove the yt-dlp boundary via inspect flows, complete subtitle execution with manifests/reruns, then wrap it with polished CLI ergonomics, and only then add API and later video support.

### Phase 1: Core contracts and environment validation
**Rationale:** Every later feature depends on deterministic models, output rules, and a reliable runtime baseline.
**Delivers:** Domain models, artifact model, manifest schema, status/error taxonomy, output directory contract, language selection contract, config assembly rules, preflight checks for yt-dlp/ffmpeg/JS runtime.
**Addresses:** Deterministic output naming, metadata persistence, machine-friendly state, API-ready task model.
**Avoids:** CLI-only corner, config leakage, title-only paths, subtitle-centric schema, missing dependency drift controls.

### Phase 2: Inspection and planning engine
**Rationale:** Inspection is the lowest-risk way to validate the yt-dlp boundary before full downloads.
**Delivers:** URL normalization, metadata-only inspection, playlist expansion, subtitle availability/language listing, JSON-safe metadata normalization, manifest draft/planning mode.
**Uses:** yt-dlp adapter, Pydantic models, filesystem manifest contract.
**Implements:** Two-phase inspect → execute architecture pattern.
**Avoids:** Monolithic playlist execution, simplistic `--lang` semantics, poor subtitle availability reporting.

### Phase 3: Subtitle execution pipeline
**Rationale:** This is the first full product slice and the MVP value promise.
**Delivers:** Single-video and playlist subtitle download, per-item execution state machine, VTT/SRT/TXT conversion, per-item metadata/log/artifact bundle, continue-on-error handling, skip/already-downloaded rules.
**Addresses:** Core table stakes from FEATURES.md.
**Avoids:** Weak provenance, archive-as-truth, artifact-blind success/failure models.

### Phase 4: Resilience, reruns, and batch ergonomics
**Rationale:** Once downloads work, reliability and operator control become the differentiator.
**Delivers:** Failure taxonomy, bounded retries with backoff, rerun-failed-items, rerun-by-status filters, batch summary reports, canary/health check command, structured JSON/NDJSON summaries.
**Uses:** structlog, manifest history, event model.
**Implements:** Per-item retries and operational observability.
**Avoids:** Infinite retries, hidden throttling, whole-playlist reruns for a few failures.

### Phase 5: CLI productization
**Rationale:** CLI syntax and UX should wrap a proven core rather than define it.
**Delivers:** Typer command groups, Rich progress rendering, inspect/download/rerun/preflight commands, human-readable summaries plus machine-friendly modes, stable exit-code mapping.
**Addresses:** Scriptability and operational usability expectations.
**Avoids:** Giant command handlers and print-driven status coupling.

### Phase 6: Local API wrapper
**Rationale:** The API should expose the same use cases, not fork business logic.
**Delivers:** FastAPI endpoints for job submission/status/results, local in-process runner for early self-hosted mode, optional polling/SSE progress, SQLite-backed job indexing if needed.
**Uses:** Same service layer, manifest/output contracts, event model.
**Implements:** Thin HTTP adapter over shared core.
**Avoids:** Treating FastAPI BackgroundTasks as a durable large-scale queue or exposing a shell script as the backend.

### Phase 7: Video expansion on the same execution model
**Rationale:** Video adds real complexity and should only arrive once subtitle workflows are stable.
**Delivers:** Video/audio artifact types, format/quality profiles, FFmpeg-aware post-processing, larger-file storage rules, richer artifact-level aggregate statuses.
**Addresses:** Future video table stakes without rewriting the core.
**Avoids:** Bolting on a second pipeline or breaking subtitle-era storage contracts.

### Phase Ordering Rationale

- **Contracts before commands:** output, manifest, and artifact identity are harder to change than CLI syntax.
- **Inspect before execute:** playlist expansion and subtitle availability are safer ways to validate the engine boundary than full download orchestration.
- **Execution before polish:** reliable per-item workflows, provenance, and reruns matter more than command UX early.
- **Shared core before API:** the architecture only scales if CLI and API are delivery layers over the same services.
- **Subtitle maturity before video:** video introduces storage, remuxing, and larger retry/performance complexity; it should reuse the proven task model.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4:** retry/throttling strategy at batch scale needs tuning against real YouTube behavior and canary data.
- **Phase 6:** API job execution model needs deeper research once requirements move beyond single-user/self-hosted usage.
- **Phase 7:** video format selection, remuxing policy, and storage/throughput implications deserve focused phase research.

Phases with standard patterns (skip research-phase):
- **Phase 1:** Python/Typer/Pydantic/manifest contract setup is well supported by current research.
- **Phase 2:** yt-dlp metadata inspection and playlist expansion patterns are established and documented.
- **Phase 5:** CLI adapter/productization over a shared service layer is standard and low risk.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Based primarily on official docs, package metadata, and the dominant downloader ecosystem pattern around yt-dlp. |
| Features | MEDIUM-HIGH | Table stakes are well supported by established tools; differentiators are more opinionated product synthesis. |
| Architecture | MEDIUM-HIGH | Core patterns are strongly grounded in verified library capabilities, with some design synthesis for future API evolution. |
| Pitfalls | HIGH | Strong support from yt-dlp docs/changelog/issues plus clear alignment with the product’s likely failure modes. |

**Overall confidence:** HIGH

### Gaps to Address

- **Durable API execution model:** early in-process jobs are acceptable, but queue/worker architecture for larger service usage remains intentionally unresolved.
- **Real-world throttling thresholds:** concurrency, pacing, and backoff defaults need empirical validation during implementation.
- **Authenticated/private-content support:** research says to defer it, but if product scope changes this will need dedicated design.
- **Transcript normalization policy:** TXT cleaning and provenance rules need explicit product decisions before they become user-facing contracts.
- **Video expansion specifics:** quality profiles, merge/remux rules, and artifact retention policy should be researched when Phase 7 is planned.

## Sources

### Primary (HIGH confidence)
- yt-dlp official repository/README/FAQ/changelog — downloader embedding, subtitle handling, playlist behavior, archives, retries, config, and compatibility churn.
- Python 3.13 release notes — runtime baseline.
- uv docs — project/dependency management.
- FFmpeg official docs/releases — system dependency guidance.
- Typer official docs — CLI framework patterns.
- FastAPI official docs — API patterns and BackgroundTasks limitations.
- PyPI metadata for yt-dlp, Typer, FastAPI, Pydantic, Rich, HTTPX, AnyIO, SQLAlchemy, SQLModel, structlog, Uvicorn, Ruff, pytest, and respx — version verification.

### Secondary (MEDIUM confidence)
- 4K Video Downloader Plus official product page — table-stakes/differentiator comparison for downloader workflows.
- cobalt official site and GitHub README — trust/simplicity positioning reference.
- JDownloader official overview — batch/retry/download-manager expectations.
- Context7 docs for yt-dlp and Typer — embedding and CLI structuring support.

### Tertiary (LOW confidence)
- Comparison/review ecosystem sources used only to confirm recurring market patterns, not as primary authority.
- yt-dlp GitHub issues cited in PITFALLS.md for edge-case evidence and operational nuance.

---
*Research completed: 2026-05-09*
*Ready for roadmap: yes*
