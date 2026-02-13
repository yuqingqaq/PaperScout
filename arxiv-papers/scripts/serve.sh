#!/bin/bash

# HTTP 服务器启动脚本（带 API 支持）
# 用法: ./serve.sh [port]

PORT=${1:-8889}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 启动服务器..."
cd "$PROJECT_DIR" && uv run python scripts/server.py $PORT
