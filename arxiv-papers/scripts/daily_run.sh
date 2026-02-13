#!/bin/bash

# 每日自动推荐脚本
# 由 cron 定时执行

# 切换到项目目录
cd "$(dirname "$0")/.."

# 运行主程序（会自动导出 kb_data.json 到 output 目录）
uv run python src/main.py --config config.json --mode daily >> logs/daily_$(date +%Y%m%d).log 2>&1

echo "Daily recommendation completed at $(date)" >> logs/cron.log
