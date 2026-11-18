#!/usr/bin/env bash
# FontWorks 环境准备：安装依赖，并在 macOS 上配置 cairo 动态库路径。
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"

echo "==> 安装依赖"
"$PY" -m pip install -r "$ROOT/scripts/requirements.txt"

if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
  BREW_LIB="$(brew --prefix cairo 2>/dev/null)/lib"
  if [ -d "$BREW_LIB" ]; then
    echo "export DYLD_FALLBACK_LIBRARY_PATH=\"$BREW_LIB:\$DYLD_FALLBACK_LIBRARY_PATH\"" > "$ROOT/cairo-env.sh"
    echo "==> cairo 路径已写入 $ROOT/cairo-env.sh"
    echo "    使用前执行: source \"$ROOT/cairo-env.sh\""
  fi
fi

echo "==> 验证"
"$PY" "$ROOT/scripts/fontworks.py" --version
echo "完成。"
