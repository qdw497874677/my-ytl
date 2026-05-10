# yt-subs

CLI-first YouTube subtitle inspection and download tooling.

Download subtitles for YouTube videos in VTT, SRT, and TXT formats with per-video metadata and provenance tracking.

> The current executable name, `yt-subdl`, is an internal temporary CLI name and may be replaced later without changing the core service boundaries.

## Setup

```bash
uv sync
```

## Discover Commands

```bash
uv run yt-subdl --help
```

## Preflight Runtime Dependencies

Check whether downloader-related dependencies are available before starting a job:

```bash
uv run yt-subdl preflight
```

The report distinguishes required checks such as `yt-dlp`, `ffmpeg`, and `ffprobe` from recommended JavaScript runtime support.

## Inspect a Target Before Download

Preview a single video, Shorts/share URL, or playlist-capable YouTube URL:

```bash
uv run yt-subdl inspect "https://www.youtube.com/watch?v=VIDEOID" --output-dir downloads
```

When you do **not** pass `--cookies-from-browser` or `--cookies`, `yt-subdl` automatically tries common browser cookies in fallback order. It prefers the Firefox family first, then tries Chrome-family browsers supported on the current platform. Zen browser is handled through yt-dlp's Firefox-compatible cookies backend; on macOS, `zen` resolves to the Zen profile directory under `~/Library/Application Support/zen/...`.

When you do **not** pass `--remote-components`, `yt-subdl` now enables `ejs:github` by default so `yt-dlp-ejs` can fetch the recommended remote YouTube component when needed. You can override this by repeating `--remote-components ...`, or disable all remote fetching with `--no-remote-components`.

For network stability, `yt-subdl` also defaults to the same knobs that were validated in the working native command: `--force-ipv4 --retries 5 --extractor-retries 5`. You can still override or disable them explicitly when needed.

If auto-detection is not enough, override it explicitly:

```bash
uv run yt-subdl inspect "https://www.youtube.com/watch?v=VIDEOID" --cookies-from-browser firefox
uv run yt-subdl inspect "https://www.youtube.com/watch?v=VIDEOID" --cookies-from-browser zen
uv run yt-subdl inspect "https://www.youtube.com/watch?v=VIDEOID" --cookies /path/to/cookies.txt
uv run yt-subdl inspect "https://www.youtube.com/watch?v=VIDEOID" --remote-components ejs:github
uv run yt-subdl inspect "https://www.youtube.com/watch?v=VIDEOID" --no-remote-components
uv run yt-subdl inspect "https://www.youtube.com/watch?v=VIDEOID" --force-ipv4 --retries 5 --extractor-retries 5
```

Inspect output includes:

- expanded per-video items for playlists
- YouTube video IDs and stable item identities
- available subtitle language codes with manual/automatic labels
- planned output bundle paths under the selected `--output-dir`

## Download Subtitles

Download subtitle artifacts for a single YouTube video in the languages and formats you need:

```bash
uv run yt-subdl download "https://www.youtube.com/watch?v=VIDEOID" --language en --language ja --format vtt --format srt --format txt --output-dir downloads
```

Download output includes:

- subtitle artifact files under `downloads/items/{video_id[-title]}/subtitles/`
- per-video metadata at `downloads/items/{video_id[-title]}/metadata/item.json`
- unavailable requested languages reported in CLI output and metadata

VTT is the source subtitle artifact. SRT and TXT are converted exports. Metadata links every converted file to its source track. Unavailable requested languages are reported as structured outcomes, not generic errors.

Options:

- `--language` / `-l` — one or more subtitle languages (repeatable, defaults to `en`)
- `--format` / `-f` — output formats: `vtt`, `srt`, `txt` (repeatable, defaults to `vtt`)
- `--output-dir` / `-o` — output directory (defaults to `downloads`)
- `--manual-only` — exclude auto-generated captions (default includes them)
- `--remote-components` — allow specific yt-dlp remote components; defaults to `ejs:github`
- `--no-remote-components` — disable all remote component fetching, including the default
- `--cookies-from-browser` — explicitly choose a browser cookie source; when omitted together with `--cookies`, auto-detection tries Firefox first, then Chrome / Chromium / Edge / Safari where supported
- `--cookies` — explicitly use a Netscape-format cookies.txt file
- `--force-ipv4` / `--no-force-ipv4` — force IPv4 requests by default, or turn that off explicitly
- `--retries` — yt-dlp request retry count (defaults to `5`)
- `--extractor-retries` — yt-dlp extractor retry count (defaults to `5`)

Known-good single-video inspect flow, matching the validated native yt-dlp setup:

```bash
uv run yt-subdl inspect "https://www.youtube.com/watch?v=VIDEOID" \
  --cookies-from-browser "firefox:/Users/quandawei/Library/Application Support/zen/Profiles/sif4btp1.Default (release)" \
  --remote-components ejs:github \
  --force-ipv4 \
  --retries 5 \
  --extractor-retries 5
```

Equivalent shorthand when Zen auto-detection works on your machine:

```bash
uv run yt-subdl inspect "https://www.youtube.com/watch?v=VIDEOID" --cookies-from-browser zen
```

Known-good download flow with the same validated settings:

```bash
uv run yt-subdl download "https://www.youtube.com/watch?v=VIDEOID" \
  --language en \
  --format vtt \
  --cookies-from-browser "firefox:/Users/quandawei/Library/Application Support/zen/Profiles/sif4btp1.Default (release)" \
  --remote-components ejs:github \
  --force-ipv4 \
  --retries 5 \
  --extractor-retries 5
```

Artifact layout:

```
downloads/
  items/
    {video_id[-title]}/
      subtitles/
        en.manual.vtt
        en.manual.srt
        en.manual.txt
        ja.automatic.vtt
      metadata/
        item.json
      logs/          (reserved for later)
```

## Batch Playlist Subtitle Jobs

Run a resilient batch subtitle job for a playlist or playlist-capable target:

```bash
uv run yt-subdl batch "https://www.youtube.com/playlist?list=PLAYLISTID" --language en --language ja --format vtt --format srt --output-dir downloads
```

Batch jobs use the same repeatable options as single-video downloads:

- `--language` / `-l` — one or more subtitle languages (repeatable, defaults to `en`)
- `--format` / `-f` — output formats: `vtt`, `srt`, `txt` (repeatable, defaults to `vtt`)
- `--output-dir` / `-o` — output directory (defaults to `downloads`)
- `--manual-only` — exclude auto-generated captions (default includes them)
- `--json-summary` — print a machine-readable JSON summary for scripts
- `--remote-components` — allow specific yt-dlp remote components; defaults to `ejs:github`
- `--no-remote-components` — disable all remote component fetching, including the default
- `--cookies-from-browser` / `--cookies` — same cookie override behavior as `inspect` and `download`; otherwise common browsers are auto-detected in fallback order
- `--force-ipv4` / `--no-force-ipv4`, `--retries`, `--extractor-retries` — same network stability controls as `inspect` and `download`

Batch output is durable. A single failed item does not stop later items, and state is written before the first item and after every item transition.

Batch artifact layout:

```
downloads/
  batch-jobs/
    {job_id}/
      manifest.json   # requested inputs, expanded items, statuses, artifacts, errors
      run.jsonl       # one structured event per line for progress and automation
      summary.json    # final machine-readable counts and durable paths
  items/
    {video_id[-title]}/
      subtitles/
      metadata/item.json
```

Item statuses are machine-readable:

- `completed` — subtitle artifacts and metadata were written
- `skipped` — metadata and all requested artifacts already existed, so work was not duplicated
- `failed_retryable` — temporary failure, safe candidate for rerun
- `failed_permanent` — unsupported or unavailable content that should not be retried automatically
- `no_subtitles` — requested subtitles were unavailable and are treated as a permanent outcome

For scripting, request JSON instead of parsing Rich terminal tables:

```bash
uv run yt-subdl batch "https://www.youtube.com/playlist?list=PLAYLISTID" --language en --format vtt --json-summary
```

The printed JSON includes total, completed, skipped, no-subtitle, retryable failure, permanent failure, manifest, log, and summary paths.

## Rerun Failed Batch Items

Retry only retryable failures from a saved manifest:

```bash
uv run yt-subdl rerun downloads/batch-jobs/{job_id}/manifest.json
```

Reruns are manifest-driven. They do not re-expand the playlist to decide what to attempt. By default, only `failed_retryable` items are selected. `completed`, `skipped`, `failed_permanent`, and `no_subtitles` records are preserved so successful work and known permanent outcomes are not repeated.

Use JSON output for automation:

```bash
uv run yt-subdl rerun downloads/batch-jobs/{job_id}/manifest.json --json-summary
```

Not implemented yet:

- video download workflows
- HTTP API mode

Those capabilities are intentionally reserved for later roadmap phases.

## 已验证命令 / 故障排查

### 已验证命令

```bash
# inspect
uv run yt-subdl inspect "https://www.youtube.com/watch?v=VIDEOID" \
  --cookies-from-browser "firefox:/Users/you/Library/Application Support/zen/Profiles/<profile>.Default (release)" \
  --remote-components ejs:github \
  --force-ipv4 \
  --retries 5 \
  --extractor-retries 5

# download
uv run yt-subdl download "https://www.youtube.com/watch?v=VIDEOID" \
  --language en \
  --format vtt \
  --cookies-from-browser "firefox:/Users/you/Library/Application Support/zen/Profiles/<profile>.Default (release)" \
  --remote-components ejs:github \
  --force-ipv4 \
  --retries 5 \
  --extractor-retries 5
```

### 什么时候需要这些参数

- `--remote-components ejs:github`：遇到 YouTube 提取异常，或想和已验证的 `yt-dlp-ejs` 方案完全一致时使用；本 CLI 默认已开启。
- `--force-ipv4`：当前网络的 IPv6 不稳定、请求卡住、连接偶发失败时使用；本 CLI 默认已开启。
- `--retries 5`：请求偶发超时、连接被重置、429/5xx 波动时使用；本 CLI 默认值就是 `5`。
- `--extractor-retries 5`：提取阶段偶发失败、YouTube 临时返回异常时使用；本 CLI 默认值就是 `5`。

### Zen cookies 说明

- macOS 上 Zen 通过 **Firefox-compatible cookies backend** 工作，不是单独的一套 cookies 提取逻辑。
- 优先尝试 `--cookies-from-browser zen`。
- 如果自动识别不稳定，改用显式 profile 路径：`firefox:/Users/you/Library/Application Support/zen/Profiles/<profile>.Default (release)`。

### 常见现象

- 出现 impersonation warning：当前已知**不阻塞字幕 inspect/download**；只要仍能列出字幕或成功产出文件，就可以继续使用。
- 仍然提示登录 / 机器人校验：先确认 Zen 里该视频能正常打开，再重试 `--cookies-from-browser zen` 或显式 profile 路径。
- 默认命令已经成功：保持默认即可，不必额外堆参数。
