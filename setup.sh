#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────────────────────
# yt-subdl — One-click setup & run
# ────────────────────────────────────────────────────────────
# Usage:
#   ./setup.sh              # 首次安装 + 进入虚拟环境
#   ./setup.sh run <args>   # 安装后直接运行命令
#   ./setup.sh docker       # 用 Docker 构建并运行
#   ./setup.sh clean        # 清理虚拟环境和缓存
# ────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_MIN="3.12"

check_python() {
    local python_cmd=""
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            local ver
            ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
            if [ "$(printf '%s\n' "$PYTHON_MIN" "$ver" | sort -V | head -n1)" = "$PYTHON_MIN" ]; then
                python_cmd="$cmd"
                break
            fi
        fi
    done
    if [ -z "$python_cmd" ]; then
        err "需要 Python >= $PYTHON_MIN，请先安装 Python 3.12+"
    fi
    echo "$python_cmd"
}

check_deno() {
    if command -v deno &>/dev/null; then
        ok "Deno 已安装 ($(deno --version 2>/dev/null | head -1))"
        return
    fi
    info "安装 Deno 运行时 (yt-dlp 需要)..."
    if command -v curl &>/dev/null && (command -v unzip &>/dev/null || command -v 7z &>/dev/null); then
        curl -fsSL https://deno.land/install.sh | sh 2>&1
        export DENO_INSTALL="${DENO_INSTALL:-$HOME/.deno}"
        export PATH="$DENO_INSTALL/bin:$PATH"
        # 写入 .venv/bin/activate 以便后续自动加载
        if [ -f "$VENV_DIR/bin/activate" ]; then
            cat >> "$VENV_DIR/bin/activate" <<'DENO_RC'
# Auto-added by yt-subdl setup: Deno runtime for yt-dlp
if [ -d "$HOME/.deno/bin" ]; then
    export PATH="$HOME/.deno/bin:$PATH"
fi
DENO_RC
        fi
        ok "Deno 安装完成"
    else
        warn "无法自动安装 Deno (需要 curl + unzip)。"
        warn "请手动安装: curl -fsSL https://deno.land/install.sh | sh"
        warn "没有 Deno，yt-dlp 可能无法正常访问 YouTube 视频。"
    fi
}

setup_venv() {
    local python_cmd
    python_cmd=$(check_python)

    if [ -d "$VENV_DIR" ]; then
        info "虚拟环境已存在，跳过创建"
    else
        info "创建虚拟环境 ($python_cmd)..."
        "$python_cmd" -m venv "$VENV_DIR"
        ok "虚拟环境创建完成"
    fi

    info "激活虚拟环境并安装依赖..."
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"

    pip install --upgrade pip --quiet
    pip install -e "$SCRIPT_DIR" --quiet
    ok "依赖安装完成"

    check_deno
}

run_cmd() {
    if [ ! -d "$VENV_DIR" ]; then
        setup_venv
    fi
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    exec yt-subdl "$@"
}

run_docker() {
    if ! command -v docker &>/dev/null; then
        err "需要 Docker，请先安装 Docker"
    fi
    if ! command -v docker compose &>/dev/null; then
        err "需要 Docker Compose v2，请先安装"
    fi
    info "构建 Docker 镜像..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" build
    ok "镜像构建完成"
    shift
    info "运行 yt-subdl $*..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" run --rm yt-subdl "$@"
}

run_preflight() {
    if [ ! -d "$VENV_DIR" ]; then
        setup_venv
    fi
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    yt-subdl preflight
    echo ""
    echo "快速开始:"
    echo "  source .venv/bin/activate"
    echo "  yt-subdl download \"https://www.youtube.com/watch?v=VIDEO_ID\" -l en -f srt"
}

clean() {
    info "清理虚拟环境和缓存..."
    rm -rf "$VENV_DIR"
    rm -rf "$SCRIPT_DIR/__pycache__"
    find "$SCRIPT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$SCRIPT_DIR" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    ok "清理完成"
}

main() {
    local action="${1:-setup}"
    case "$action" in
        setup|install|"")
            setup_venv
            echo ""
            run_preflight
            ;;
        run)
            shift
            run_cmd "$@"
            ;;
        docker)
            run_docker "$@"
            ;;
        clean)
            clean
            ;;
        preflight)
            run_preflight
            ;;
        help|--help|-h)
            echo "用法:"
            echo "  ./setup.sh              首次安装依赖"
            echo "  ./setup.sh run <args>   运行 yt-subdl 命令"
            echo "  ./setup.sh docker <args> 用 Docker 运行"
            echo "  ./setup.sh preflight    检查运行时依赖"
            echo "  ./setup.sh clean        清理虚拟环境"
            ;;
        *)
            run_cmd "$@"
            ;;
    esac
}

main "$@"
