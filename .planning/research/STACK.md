# Technology Stack

**Project:** YouTube subtitle/video downloader tool  
**Researched:** 2026-05-09  
**Scope:** CLI-first downloader built for subtitles first, with a clean expansion path to server-side API and full video download later.

## Recommended Stack

This project should be built as a **Python 3.13 application that wraps `yt-dlp` as the download engine**, uses **Typer** for the CLI, **Pydantic v2** for job/config/output models, and **FastAPI** for the future API layer. Persist job manifests and logs on disk first; add SQLite-backed job indexing when API mode arrives.

That is the standard 2025-era shape for this kind of tool because:

- **`yt-dlp` is the de facto maintained downloader core** for YouTube and playlists. Rebuilding extractor logic yourself is a maintenance trap.
- **Python is the path of least resistance** because `yt-dlp` is native to it, FFmpeg orchestration is straightforward, and CLI/API sharing is easy.
- **Typer + FastAPI + Pydantic** gives one coherent developer model across CLI commands, internal services, and future HTTP endpoints.
- **FFmpeg is non-optional infrastructure** once video becomes a first-class capability and even helps with subtitle/post-processing workflows.

## Opinionated Recommendation

### Build around these principles

1. **Use `yt-dlp` as a library-backed engine, but isolate it behind your own adapter.**  
   Do not let `yt-dlp` types and flags leak through the entire codebase.

2. **Use Python, not Node, for the core app.**  
   Your most important dependency already lives in Python, so choosing Node only adds process boundaries, packaging complexity, and duplicated modeling.

3. **Treat subtitle download and video download as the same job system with different output modes.**  
   The stack should model “resolve URL → enumerate items → fetch assets → transform → persist manifest/logs”, not “subtitle app now, separate video app later”.

4. **Persist artifacts to the filesystem first.**  
   For a CLI-first tool, files are the product: subtitle files, metadata JSON, logs, and rerun manifests. Database concerns should support indexing and API workflows later, not replace the artifact-first design.

## Core Stack

### Runtime / Language

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | **3.13.x** | Primary runtime | Best fit because `yt-dlp` is Python-native, Typer/FastAPI/Pydantic are mature here, and Python 3.13 is stable with broad ecosystem support. Choose 3.13 for new development; keep code compatible with `yt-dlp`'s 3.10+ floor. | HIGH |
| uv | **latest** | Package/project manager | `uv` has become the default modern Python project manager for fast installs, lockfiles, reproducible envs, and simple CLI workflows. Better fit than Poetry for a utility-focused repo. | HIGH |

### Download / Media Core

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| yt-dlp | **2026.3.17** | Download/extraction engine | This is the standard core for YouTube downloading in 2025-era tooling. It supports playlists, subtitles, metadata extraction, format selection, post-processing hooks, and regular upstream fixes for site breakage. | HIGH |
| FFmpeg / FFprobe | **8.1.x preferred** | Media post-processing, muxing, probing | Required once video is core, and still valuable early for format normalization, probing, and future-proof architecture. Treat it as a system dependency, not a Python package. | HIGH |
| yt-dlp-ejs + JS runtime | match `yt-dlp` requirements | Full YouTube support | Current `yt-dlp` docs explicitly recommend `yt-dlp-ejs` plus a JS runtime such as Deno/Node/Bun/QuickJS for full YouTube support. Plan for this from day one even if local setups vary. | HIGH |

### CLI / Application Layer

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Typer | **0.25.1** | CLI framework | Best choice for a serious Python CLI in 2025: typed commands, good help UX, shell completion, and an ergonomic path to multiple subcommands like `subtitle`, `video`, `playlist`, `rerun`, and `inspect`. | HIGH |
| Rich | **15.0.0** | Terminal UX | Use for progress, tables, error panels, and structured human-readable output. Important because downloader tools are operational tools; clear output matters more than minimal dependencies. | HIGH |
| Pydantic | **2.13.4** | Internal models / validation | Use for validating CLI options, persisted manifests, metadata snapshots, config files, and future API schemas. This keeps CLI and API models aligned. | HIGH |
| structlog | **25.5.0** | Structured logging | Prefer structured logs over ad-hoc print statements so the same events work for local debugging now and API/server observability later. | HIGH |

### API-Ready Server Layer

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| FastAPI | **0.136.1** | Future HTTP API | The cleanest expansion path from typed Python service objects to an API. Reuse Pydantic models and service layer without rewriting the downloader core. | HIGH |
| Uvicorn | **0.46.0** | ASGI server | Standard deployment/runtime choice for FastAPI. Lightweight, well-understood, and sufficient until you need more advanced process management. | HIGH |
| AnyIO | **4.13.0** | Concurrency foundation | Useful for structured concurrency around queued download jobs, cancellation, and background task orchestration; aligns with the modern FastAPI/Starlette ecosystem. | MEDIUM |
| HTTPX | **0.28.1** | HTTP client for non-yt-dlp calls | Use only for your own control-plane HTTP work: health checks, remote manifests, webhook callbacks, or API integrations. Do not use it to replace `yt-dlp` for YouTube extraction. | HIGH |

### Persistence

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Filesystem-first artifact store | n/a | Subtitle/video outputs, metadata, logs, rerun manifests | This is the right v1 persistence model because outputs are files, users need deterministic directories, and reruns should work from manifest files even without a DB. | HIGH |
| SQLite | stdlib `sqlite3` | Future job index / API state | Add when API mode begins: track jobs, item status, retries, and queryable history. Do not start with Postgres for a CLI-first single-user tool. | HIGH |
| SQLAlchemy | **2.0.49** | Future DB access layer | Use when SQLite-backed API/job storage is introduced. SQLAlchemy 2.x is the safest long-term choice if the project later outgrows SQLite. | HIGH |
| SQLModel | **0.0.38** | Optional simplified models for API+DB | Acceptable if you want FastAPI-friendly ORM models quickly, but only after the DB exists. It is convenience, not core infrastructure. | MEDIUM |

### Quality / Tooling

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Ruff | **0.15.12** | Linting + formatting | Standard modern Python choice: fast, batteries-included, and simpler than maintaining Flake8 + isort + Black as separate tools. | HIGH |
| pytest | **9.0.3** | Test runner | Still the standard for Python CLI/service testing. Use for manifest logic, config parsing, filesystem workflows, and integration boundaries. | HIGH |
| respx | **0.23.1** | HTTPX mocking | Useful once you add HTTPX-based control-plane behavior or API callbacks. Not needed for the `yt-dlp` engine path itself. | HIGH |

## Prescriptive Architecture Fit

Use the repo as four layers:

1. **`core/`** – pure domain models and policies  
   Examples: job spec, language selection rules, output naming, retry rules.

2. **`engine/`** – adapter around `yt-dlp`, FFmpeg, filesystem, subprocess/runtime checks  
   This is where extractor flags and FFmpeg probing belong.

3. **`app/`** – orchestration services  
   Examples: `download_subtitles(urls, langs, format)`, `download_video(urls, profile)`, `rerun_failed_job(job_id)`.

4. **`interfaces/`** – Typer CLI now, FastAPI later  
   Both should call the same `app/` services.

This keeps the stack future-proof: the CLI and API become thin wrappers over the same downloader application services.

## What to Use for Each Requirement

| Requirement | Recommended Technology | Notes |
|-------------|------------------------|-------|
| Single video subtitle download | `yt-dlp` + Typer + Pydantic | Core v1 path |
| Playlist subtitle batch download | `yt-dlp` playlist extraction + filesystem manifests | Keep playlist item enumeration explicit in your own manifest |
| Multi-language subtitle selection | Your own domain model over `yt-dlp` subtitle options | Do not expose raw flags directly to users forever |
| Subtitle format conversion (`vtt`/`srt`/`txt`) | `yt-dlp` extraction + your own post-processing/conversion layer | Keep “plain text export” in your app, not buried in one-off scripts |
| Metadata persistence | JSON sidecar files | Store raw-ish source metadata plus normalized manifest |
| Logs and reruns | structlog + manifest files + exit summaries | Rerun should operate from saved state |
| Future video download | same `yt-dlp` engine + FFmpeg | Equal core capability later, no stack rewrite |
| Future HTTP API | FastAPI + Uvicorn + same service layer | Do not fork business logic into API-only code |

## What NOT to Use

| Category | Avoid | Why Not |
|----------|-------|---------|
| Download core | **`pytube` as the primary engine** | Historically more fragile against YouTube changes and not the standard serious choice when reliability matters. Use the actively maintained downloader ecosystem leader instead. |
| Download core | **`youtube-transcript-api` as the core substrate** | Fine for transcript-only niche cases, but too narrow for your roadmap because it does not solve playlists, metadata, or the later video-download core. |
| Runtime | **Node.js as the main application runtime** | Adds needless complexity when the critical dependency (`yt-dlp`) is Python-native. Use Node only if you explicitly choose a JS-based downloader ecosystem, which you are not. |
| Persistence | **PostgreSQL in v1** | Premature for a CLI-first tool. It increases setup friction without improving the core file-delivery workflow. |
| CLI framework | **argparse-only hand-built CLI** | Too low-level for a tool that will grow many commands, typed options, good help output, and completion needs. |
| Logging | **print-driven logging** | Breaks down immediately once you need reruns, machine-readable logs, or API observability. |
| FFmpeg integration | **Python package named `ffmpeg` as a substitute for FFmpeg binary** | `yt-dlp` docs explicitly warn that what you need is the system `ffmpeg` binary, not the unrelated Python package. |

## Installation

### Recommended dependency groups

```bash
# project bootstrap
uv init

# runtime
uv add yt-dlp typer rich pydantic structlog httpx

# future API layer
uv add fastapi uvicorn anyio

# optional future DB layer
uv add sqlalchemy

# dev tooling
uv add --dev ruff pytest respx
```

### System dependencies

Install separately:

```bash
# required system binaries
ffmpeg
ffprobe

# strongly recommended for full YouTube support with modern yt-dlp
yt-dlp-ejs
deno   # preferred JS runtime by yt-dlp docs; node is acceptable fallback
```

## Suggested Minimum Versions Policy

Pin with a bias toward reproducibility:

- Python: `>=3.13,<3.14` for project runtime
- `yt-dlp`: pin exact release and update aggressively
- Typer / FastAPI / Pydantic / Uvicorn: pin compatible minor versions
- FFmpeg: require `>=7.1`, prefer current stable `8.1.x`

Why this policy:

- **`yt-dlp` breaks for external reasons, not just code reasons.** You want controlled updates and frequent refreshes.
- **FFmpeg compatibility matters operationally.** “Whatever is on the machine” leads to support headaches.
- **CLI/API framework churn is lower than extractor churn.** Pin them, but update them on a calmer cadence than `yt-dlp`.

## Final Recommendation

If you want the most standard, lowest-regret stack for this project, build it as:

- **Python 3.13**
- **uv** for project management
- **yt-dlp** as the downloader core
- **FFmpeg/FFprobe** as required system dependencies
- **Typer + Rich** for the CLI
- **Pydantic v2 + structlog** for models and logs
- **Filesystem-first manifests/logs/artifacts**
- **FastAPI + Uvicorn** when API mode starts
- **SQLite + SQLAlchemy later**, not at the beginning

That stack is the right one because it optimizes for the actual hard part of the product: **reliable downloading and clean operational workflows**, not framework novelty.

## Sources

- Python 3.13 release notes: https://docs.python.org/3/whatsnew/3.13.html
- uv docs: https://docs.astral.sh/uv/
- yt-dlp repository and docs: https://github.com/yt-dlp/yt-dlp
- yt-dlp PyPI metadata (`2026.3.17`): https://pypi.org/pypi/yt-dlp/json
- FFmpeg official downloads/releases: https://ffmpeg.org/download.html
- Typer docs: https://typer.tiangolo.com/
- Typer PyPI metadata (`0.25.1`): https://pypi.org/pypi/typer/json
- FastAPI docs: https://fastapi.tiangolo.com/
- FastAPI PyPI metadata (`0.136.1`): https://pypi.org/pypi/fastapi/json
- Pydantic PyPI metadata (`2.13.4`): https://pypi.org/pypi/pydantic/json
- Rich PyPI metadata (`15.0.0`): https://pypi.org/pypi/rich/json
- HTTPX PyPI metadata (`0.28.1`): https://pypi.org/pypi/httpx/json
- AnyIO PyPI metadata (`4.13.0`): https://pypi.org/pypi/anyio/json
- SQLAlchemy PyPI metadata (`2.0.49`): https://pypi.org/pypi/sqlalchemy/json
- SQLModel PyPI metadata (`0.0.38`): https://pypi.org/pypi/sqlmodel/json
- structlog PyPI metadata (`25.5.0`): https://pypi.org/pypi/structlog/json
- Uvicorn PyPI metadata (`0.46.0`): https://pypi.org/pypi/uvicorn/json
- Ruff PyPI metadata (`0.15.12`): https://pypi.org/pypi/ruff/json
- pytest PyPI metadata (`9.0.3`): https://pypi.org/pypi/pytest/json
- RESPX PyPI metadata (`0.23.1`): https://pypi.org/pypi/respx/json
