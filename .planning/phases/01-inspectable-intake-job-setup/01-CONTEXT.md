# Phase 1: Inspectable Intake & Job Setup - Context

**Gathered:** 2026-05-10
**Status:** Ready for planning

<domain>
## Phase Boundary

本阶段交付一个可检查、可预检、可稳定建模的 CLI 入口层：用户可以提交单个视频或播放列表 URL，先验证运行环境，再 inspect 目标并看到展开后的条目、可用字幕语言、稳定的 item identity，以及包含 YouTube video ID 的确定性输出路径。真正的字幕下载、格式转换、失败重跑与批量恢复不属于本阶段。

</domain>

<decisions>
## Implementation Decisions

### CLI 结构
- **D-01:** Phase 1 采用**单一主入口 + 子命令**的 CLI 结构，而不是单命令参数模式或多个分离可执行文件。
- **D-02:** `inspect` 作为**独立子命令**存在，而不是作为 `download --inspect` / `--dry-run` 的附属模式。
- **D-03:** CLI 主入口名在 Phase 1 **先使用临时内部名推进实现，并保持后续可替换**；当前不锁定最终对外品牌名。
- **D-04:** 基础 job 选项在当前阶段**先挂在业务子命令层**（如 `inspect` / 后续 `download`），不提前抽成复杂的全局共享选项体系。
- **D-05:** CLI help 和文档风格采用**操作型**：优先给出常见命令示例、参数含义和下一步动作，而不是极简 help 或偏手册式堆叠。

### the agent's Discretion
- Phase 1 主入口的临时具体名字可由规划/实现阶段决定，只要后续可平滑替换。
- 子命令的精确层级、别名策略、help 排版细节可由 planner / executor 自主决定。
- 未讨论的灰区（Inspect 输出形式、URL 支持范围、任务/输出身份、配置与预检深度）暂不锁定，研究与规划阶段可基于现有文档提出默认方案；若这些方案会显著改变用户体验，再回到 discuss-phase 补充决策。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` — Phase 1 的目标、依赖关系与 4 条 success criteria，是本阶段边界的最高优先级来源。
- `.planning/REQUIREMENTS.md` — INTK-01, INTK-02, INTK-03, INTK-04, EXPT-04, META-04, RELY-05, CLIX-01, CLIX-04 的正式要求与 traceability。
- `.planning/PROJECT.md` — 产品范围、长期方向、CLI-first / API-ready 约束，以及“先字幕后视频”的非协商前提。
- `.planning/STATE.md` — 当前项目状态、当前聚焦 Phase 1、以及已有 blocker/concern 说明。

### Architecture and workflow shape
- `.planning/research/ARCHITECTURE.md` — 推荐分层架构、CLI/API 边界、inspect→execute 两阶段模式、manifest/output manager/yt-dlp adapter 的职责分离。
- `.planning/research/SUMMARY.md` — 研究结论总览，尤其是 shared-core、deterministic outputs、inspect-first workflow 的整体方向。

### Risks and operational constraints
- `.planning/research/PITFALLS.md` — Phase 1 相关关键坑点，尤其是依赖漂移、playlist 任务建模、manifest 不是 archive、输出路径契约、路径命名边界等。

### Stack and tool choices
- `.planning/research/STACK.md` — Python 3.13、uv、yt-dlp、Typer、Rich、Pydantic、structlog、filesystem-first persistence 的锁定技术路线。

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 当前仓库**没有现成源码**；现阶段可复用资产主要是 `.planning/research/` 下的研究文档与架构约束，而不是代码组件。
- `.planning/research/ARCHITECTURE.md` 已给出可直接落地的模块边界参考，如 CLI adapter、services、manifest store、output manager、yt-dlp adapter。

### Established Patterns
- 采用**共享核心 + 薄 CLI 适配层**模式，CLI 不应直接调用 yt-dlp。
- 采用 **inspect → execute** 两阶段模式；Phase 1 聚焦 inspect / setup 这一层。
- manifest、输出路径和 item identity 被视为**产品契约**，不是执行时的副产物。
- 文件系统优先，结构化日志和 Pydantic 模型优先，为后续 API 复用保留边界。

### Integration Points
- 未来实现需要连接到 `yt-dlp` 的 metadata-only inspection 能力，以及显式的 runtime preflight 检查。
- CLI 入口需要与后续 service layer 对齐，避免把命令解析、路径计算、状态建模耦合在 command handler 内。
- 输出路径契约、manifest schema、环境检查结果都应成为后续 Phase 2/3 复用的稳定输入。

</code_context>

<specifics>
## Specific Ideas

- 第一版 CLI 不追求品牌名一次定死；先把结构做对，再决定最终对外命名。
- `inspect` 必须是用户显式可见的一等能力，而不是隐藏在下载命令背后的开关。
- 帮助信息应更像“可操作指南”，而不是只罗列参数。

</specifics>

<deferred>
## Deferred Ideas

- Inspect 输出形式（默认表格/列表/JSON、是否支持 `--json`）—— 本次未锁定。
- URL 支持范围（是否支持 Invidious / Piped 等镜像链接）—— 本次未锁定。
- 稳定 item identity 与输出目录命名细节（仅 video ID vs video ID + 标题）—— 本次未锁定。
- 配置文件是否在 Phase 1 引入，以及 preflight 的检查深度 —— 本次未锁定。

</deferred>

---

*Phase: 01-inspectable-intake-job-setup*
*Context gathered: 2026-05-10*
