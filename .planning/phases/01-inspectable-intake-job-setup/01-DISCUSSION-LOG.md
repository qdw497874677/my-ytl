# Phase 1: Inspectable Intake & Job Setup - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-10
**Phase:** 01-inspectable-intake-job-setup
**Areas discussed:** CLI 结构

---

## CLI 结构

### 第一版 CLI 命令结构

| Option | Description | Selected |
|--------|-------------|----------|
| 单入口+子命令 | 例如 `yt-sub preflight`、`yt-sub inspect URL`、后续再加 `download` / `rerun`。最利于扩展。 | ✓ |
| 单一主命令+参数模式 | 例如统一 `yt-sub URL --inspect`、`yt-sub --preflight`。 | |
| 分离命令 | 例如 `yt-sub-inspect`、`yt-sub-preflight`。 | |

**User's choice:** 单入口+子命令
**Notes:** 用户接受推荐方案，优先保证 Phase 2/3 扩展能力与 CLI 结构清晰度。

---

### CLI 主入口名风格

| Option | Description | Selected |
|--------|-------------|----------|
| 功能直白 | 像 `yt-sub` / `youtube-sub`，突出字幕能力。 | |
| 更通用 | 像 `ytdlx` / `yt-fetch`，为后续视频能力保留中性品牌。 | |
| 先临时，后续可改 | 先用简单内部名推进实现，后续再定最终对外名字。 | ✓ |

**User's choice:** 先临时，后续可改
**Notes:** 先把结构和核心体验做对，不在 Phase 1 锁死品牌命名。

---

### inspect 的命令层定位

| Option | Description | Selected |
|--------|-------------|----------|
| 独立 inspect 子命令 | 例如 `yt-sub inspect URL`，把 inspect 作为一等能力。 | ✓ |
| download 的前置模式 | 例如 `download --inspect` / `--dry-run`。 | |
| 两者都支持 | 既有 `inspect` 又有 `download --inspect`。 | |

**User's choice:** 独立 inspect 子命令
**Notes:** 用户希望“先看清楚再下载”在 CLI 上是显式、独立可见的。

---

### 基础 job 选项的组织层次

| Option | Description | Selected |
|--------|-------------|----------|
| 先集中在 inspect/download 级别 | 常用选项先挂在业务子命令上，避免过早抽象。 | ✓ |
| 一开始就做全局共享选项 | 很多选项挂在根命令统一复用。 | |
| inspect 尽量轻，执行类命令再加 | inspect 只保留最少参数。 | |

**User's choice:** 先集中在 inspect/download 级别
**Notes:** 用户偏向 greenfield 阶段的务实组织方式，先不要把根命令做复杂。

---

### CLI help / 文档风格

| Option | Description | Selected |
|--------|-------------|----------|
| 操作型 | 给出常见命令示例、参数解释、下一步建议。 | ✓ |
| 极简型 | 尽量少写 help，主要靠 README。 | |
| 偏参考手册型 | 在命令内详尽列出参数与行为。 | |

**User's choice:** 操作型
**Notes:** 第一版更重视“拿起来就能跑”的体验，而不是最短 help 或最完整手册。

---

## the agent's Discretion

- 临时主入口的具体命名可在规划/实现阶段决定。
- 子命令细节层级、别名、help 展现排版未被锁定。

## Deferred Ideas

- Inspect 输出形式
- URL 支持范围
- 任务/输出身份
- 配置与预检深度
