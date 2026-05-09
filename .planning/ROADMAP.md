# Roadmap: YouTube 字幕与视频下载工具

## Overview

This roadmap delivers the project in the order the product needs to become trustworthy: first make YouTube targets inspectable and jobs deterministic, then make subtitle artifacts usable for real work, then make batch execution durable enough for reruns, automation, and the future API/video expansion path. The result is a CLI-first subtitle workflow that already behaves like a stable service core instead of a one-off script.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Inspectable Intake & Job Setup** - Users can validate inputs, inspect targets, and prepare deterministic jobs in a ready environment.
- [ ] **Phase 2: Subtitle Artifact Delivery** - Users can download usable subtitle artifacts with metadata and format conversion.
- [ ] **Phase 3: Batch Recovery & Automation Readiness** - Users can run resilient batch jobs, rerun failures, and consume structured results.

## Phase Details

### Phase 1: Inspectable Intake & Job Setup
**Goal**: Users can submit YouTube targets, verify the runtime, inspect what will be downloaded, and see stable job/output identities before execution.
**Depends on**: Nothing (first phase)
**Requirements**: INTK-01, INTK-02, INTK-03, INTK-04, EXPT-04, META-04, RELY-05, CLIX-01, CLIX-04
**Success Criteria** (what must be TRUE):
  1. User can run a documented CLI command to check whether required downloader dependencies are available before starting a job.
  2. User can submit either a single-video URL or a playlist URL, including common YouTube URL variants, without manual normalization.
  3. User can inspect a target and see the expanded items plus available subtitle languages before downloading.
  4. User can set the output directory and basic job options from the CLI and see deterministic item identities and output paths that include the YouTube video ID.
**Plans**: TBD

### Phase 2: Subtitle Artifact Delivery
**Goal**: Users can fetch subtitles as durable artifacts in the formats they need, with enough metadata and provenance to trust the outputs.
**Depends on**: Phase 1
**Requirements**: SUBT-01, SUBT-03, SUBT-04, SUBT-05, EXPT-01, EXPT-02, EXPT-03, EXPT-05, META-01
**Success Criteria** (what must be TRUE):
  1. User can download subtitles for a video and request one or more languages in the same run.
  2. User receives saved subtitle artifacts in VTT, SRT, and TXT formats according to the requested export options.
  3. User can tell from saved outputs or metadata whether a subtitle track was manual or auto-generated, and can trace each converted file back to its source track and format.
  4. User can see when a requested subtitle language is unavailable for a video instead of mistaking it for a generic tool failure.
  5. User gets per-video metadata persisted as JSON alongside the downloaded subtitle artifacts.
**Plans**: TBD

### Phase 3: Batch Recovery & Automation Readiness
**Goal**: Users can run playlist-scale subtitle jobs reliably, recover from failures efficiently, and consume durable run records for scripting and later API use.
**Depends on**: Phase 2
**Requirements**: SUBT-02, META-02, META-03, RELY-01, RELY-02, RELY-03, RELY-04, CLIX-02, CLIX-03
**Success Criteria** (what must be TRUE):
  1. User can run a playlist subtitle job that continues processing other items even when an individual item fails.
  2. User gets a persisted job manifest and structured run logs that record requested inputs, expanded items, artifact paths, statuses, and errors.
  3. User can rerun only failed items from a previous manifest, skip already completed artifacts, and avoid duplicating finished work.
  4. User can distinguish retryable failures from permanent no-subtitle or unavailable-content outcomes when reviewing job results.
  5. User can watch progress during execution and request a machine-readable end-of-job summary for automation or future API compatibility.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Inspectable Intake & Job Setup | 0/TBD | Not started | - |
| 2. Subtitle Artifact Delivery | 0/TBD | Not started | - |
| 3. Batch Recovery & Automation Readiness | 0/TBD | Not started | - |
