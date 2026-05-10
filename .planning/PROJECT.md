# YouTube 字幕与视频下载工具

## What This Is

一个先以命令行工具落地、后续可扩展为服务端 API 的 YouTube 下载工具。第一阶段聚焦根据单个视频或播放列表地址批量下载字幕与相关元数据，支持多语言字幕、格式转换、日志与任务清单；后续阶段将补齐并强化视频下载能力，使字幕和视频都成为核心能力。

## Core Value

用户输入 YouTube 地址后，能稳定、可批量地拿到可用的字幕结果，并为后续视频下载和 API 化留下清晰扩展路径。

## Requirements

### Validated

- Phase 1 validated inspectable intake and job setup: users can run CLI preflight, inspect common YouTube video/playlist targets, see available subtitle tracks, and preview deterministic output identities/paths before download.
- Phase 2 validated subtitle artifact delivery: users can download subtitles for single videos in VTT/SRT/TXT formats, request multiple languages, see unavailable-language outcomes, and get per-video JSON metadata with provenance.

### Active

- [ ] 用户可以通过单个视频或播放列表 URL 批量下载字幕（Phase 2 已实现单视频下载；播放列表批量进入 Phase 3）
- [ ] 工具会保存元数据、下载日志与任务清单，便于重跑和后续 API 化（Phase 2 已实现元数据；日志与任务清单进入 Phase 3）

### Out of Scope

- 浏览器插件或桌面 GUI — 当前优先把核心下载链路和可扩展架构做稳
- v1 视频下载实现 — 这是后续核心能力，但不挤进字幕优先的第一阶段
- 面向大规模公开服务的完整运营能力 — 先服务自己使用，再逐步面向更多用户

## Context

- 项目起点是“根据地址下载 YouTube 内容”，但范围明确采用“先字幕、后视频”的推进方式。
- 第一版优先做本地 CLI，未来需要自然演进到服务端 API，因此一开始就要把下载内核、任务模型、输出目录、日志与元数据抽象清楚。
- 使用者当前主要是项目作者本人，但设计上希望未来给更多人使用，因此不能只写成一次性脚本。
- 字幕能力是第一阶段的交付核心：需要支持单视频多语言、播放列表批量、vtt/srt/txt 等格式转换。
- 第一版完成标准：输入单个视频或播放列表地址后，能够稳定批量下载字幕；能选择语言并导出成 srt/txt 等格式；失败任务可重跑；后续接 Web API 顺畅。
- 长期方向上，视频下载不是附带功能，而是后续同等重要的核心能力。
- 技术路线偏向基于成熟下载内核封装，项目方自己负责 CLI/API、任务调度、结果组织、日志、失败恢复与后续扩展。

## Constraints

- **Product Scope**: 先字幕后视频 — 先把字幕链路做到稳定可批量使用，再进入视频下载能力
- **Interface**: CLI first, API-ready — 第一版先做命令行，但架构需要为服务端 API 预留边界
- **Output**: 必须持久化字幕文件、视频元数据、下载日志、任务清单 — 这些是可用性与批量重跑的基础
- **Adoption**: 先给自己用，未来给更多人用 — 既允许先优化个人效率，也要求结构不能写死成临时脚本
- **Implementation**: 基于成熟下载内核封装 — 以稳定性和交付速度优先，不从零实现所有底层解析逻辑

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| v1 先做 CLI 而不是 Web 服务 | 先把核心下载能力做稳，再封装服务形态 | — Pending |
| 第一阶段聚焦字幕下载 | 字幕复杂度更低，能更快形成稳定的批量能力 | — Pending |
| 字幕支持多语言、播放列表批量与格式转换 | 这些是作者定义的第一版“够用”标准 | — Pending |
| 视频下载延后，但作为后续核心能力规划 | 长期目标不是字幕小工具，而是完整下载器 | — Pending |
| 技术路线采用成熟下载内核封装 | 降低底层维护成本，把精力放在产品层能力 | — Pending |
| Phase 2 采用 subtitle-first 服务边界 | 先实现字幕下载、格式转换和元数据，再进入批量恢复和自动化 | Validated in Phase 2 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-10 after Phase 2 completion*
