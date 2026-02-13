#!/bin/bash

# ArXiv Papers 安装脚本
# 自动设置和配置项目

set -e  # 遇到错误立即退出

echo "=================================="
echo "ArXiv Papers Agent 安装向导"
echo "=================================="
echo ""

# 检查 Python 版本
echo "1. 检查 Python 版本..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "✓ Python 版本: $PYTHON_VERSION"
else
    echo "✗ 错误: 未找到 Python 3"
    echo "  请先安装 Python 3.8 或更高版本"
    exit 1
fi

# 检查 pip
echo ""
echo "2. 检查 pip..."
if command -v pip3 &> /dev/null; then
    echo "✓ pip 已安装"
else
    echo "✗ 错误: 未找到 pip"
    exit 1
fi

# 安装依赖
echo ""
echo "3. 安装 Python 依赖..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ 依赖安装成功"
else
    echo "✗ 依赖安装失败"
    exit 1
fi

# 创建 .env 文件
echo ""
echo "4. 配置环境变量..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ 已创建 .env 文件"
    echo "  请编辑 .env 或 config.json 填写 API Keys"
else
    echo "✓ .env 文件已存在"
fi

# 设置脚本权限
echo ""
echo "5. 设置脚本权限..."
chmod +x scripts/*.sh
echo "✓ 脚本权限设置完成"

# 创建必要目录
echo ""
echo "6. 创建必要目录..."
mkdir -p logs output
echo "✓ 目录创建完成"

# 完成
echo ""
echo "=================================="
echo "✓ 安装完成！"
echo "=================================="
echo ""
echo "下一步："
echo ""
echo "1. 配置 API Keys"
echo "   编辑 config.json，填写："
echo "   - Anthropic API Key"
echo "   - 飞书 App ID 和 Secret"
echo "   - 飞书 User ID"
echo ""
echo "2. 测试运行"
echo "   python3 src/main.py --config config.json --mode summary"
echo ""
echo "3. 启动 Web 服务器"
echo "   cd scripts && ./serve.sh 8888"
echo "   然后访问: http://localhost:8888/papers.html"
echo ""
echo "4. 设置定时任务（可选）"
echo "   cd scripts && ./setup_cron.sh"
echo ""
echo "更多帮助请查看 QUICKSTART.md"
echo ""
