#!/bin/bash

# 设置 cron 定时任务
# 每工作日 10:00 执行每日推荐

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DAILY_SCRIPT="$SCRIPT_DIR/daily_run.sh"

# 确保脚本可执行
chmod +x "$DAILY_SCRIPT"
chmod +x "$SCRIPT_DIR/serve.sh"

# 生成 cron 任务
CRON_JOB="0 10 * * 1-5 $DAILY_SCRIPT"

# 添加到 crontab
(crontab -l 2>/dev/null | grep -v "$DAILY_SCRIPT"; echo "$CRON_JOB") | crontab -

echo "Cron job added successfully!"
echo "Schedule: Every weekday at 10:00 AM"
echo "Command: $DAILY_SCRIPT"
echo ""
echo "To view current crontab:"
echo "  crontab -l"
echo ""
echo "To remove this cron job:"
echo "  crontab -e"
