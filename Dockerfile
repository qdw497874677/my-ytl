FROM python:3.12-slim

LABEL maintainer="yt-subdl"

# 系统依赖：ffmpeg 用于视频/字幕后处理，deno 用于 yt-dlp JavaScript 运行时
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        unzip \
        ca-certificates && \
    curl -fsSL https://deno.land/install.sh | sh && \
    apt-get purge -y curl unzip && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.deno/bin:${PATH}"

WORKDIR /app

# 先拷贝依赖声明，利用 Docker 缓存层
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir -e .

# 默认下载输出目录
VOLUME /downloads

ENTRYPOINT ["yt-subdl"]
CMD ["--help"]
