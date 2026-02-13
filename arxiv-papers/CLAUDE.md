# ArXiv Papers Agent - 维护指南

## 项目概述

专注 **Agent Memory / Agentic Memory** 领域的智能论文推荐系统。

**核心功能**：
- 自动抓取 arXiv 论文（带限流控制）
- Claude AI 深度分析
- Brave Search 社区验证（GitHub stars、讨论等）
- 飞书 Webhook 推送
- Web 展示界面

## 文件结构

```
arxiv-papers/
├── output/
│   ├── papers.json              # 论文数据库（唯一数据源）
│   ├── papers.html              # Web 展示页面
│   └── kb_data.json             # 知识库数据（启动时自动生成）
├── src/
│   ├── __init__.py              # 模块导出
│   ├── main.py                  # 主程序
│   ├── fetchers/                # 数据获取模块
│   │   ├── __init__.py
│   │   ├── arxiv.py             # arXiv 抓取（限流+重试）
│   │   ├── brave.py             # Brave Search
│   │   └── hybrid.py            # 混合搜索
│   ├── analyzers/               # 分析模块
│   │   ├── __init__.py
│   │   ├── paper_analyzer.py    # Claude AI 分析
│   │   └── paper_enricher.py    # Brave 社区验证
│   ├── notifiers/               # 通知模块
│   │   ├── __init__.py
│   │   └── feishu.py            # 飞书推送（Webhook）
│   ├── storage/                 # 存储模块
│   │   ├── __init__.py
│   │   ├── knowledge_base.py    # 知识库管理
│   │   └── paper_manager.py     # 数据管理
│   └── utils/                   # 工具模块
│       ├── __init__.py
│       ├── config.py            # 配置加载
│       └── logger.py            # 日志管理
├── tests/                       # 测试文件
│   └── run_tests.py
├── scripts/
│   ├── server.py                # HTTP 服务器（含 API）
│   ├── serve.sh                 # 启动服务器脚本
│   ├── daily_run.sh             # cron 定时任务
│   └── setup_cron.sh            # 设置定时任务
├── references/
│   ├── knowledge_base.md        # 领域知识库
│   └── kb_suggestions.json      # 待确认的知识库更新建议
├── logs/                        # 日志目录
├── config.json                  # 配置文件
├── CLAUDE.md                    # 本文件
└── README.md                    # 用户文档
```

## 核心流程

### 每日推荐流程

```
1. arXiv 搜索 (arxiv_fetcher.py)
   • 6 个关键词，最近 7 天
   • 限流控制：3秒延迟 + 自动重试
   ↓
2. Claude 分析 (paper_analyzer.py)
   • 提取贡献、结果、标签
   • 质量评分（0-100）
   ↓
3. 初步筛选
   • 按分数排序
   • 选择 >= 70 分的前 3-5 篇
   ↓
4. Brave 增强 (paper_enricher.py) ⭐
   • 查找 GitHub 仓库 + stars
   • 查找社区讨论（Twitter/Reddit/HN）
   • 计算社交分数（0-100）
   • 调整质量评分 = 原始×0.8 + 社交×0.2
   ↓
5. 重新排序
   • 按调整后分数排序
   ↓
6. 保存 (paper_manager.py)
   • 更新 papers.json
   ↓
7. 飞书推送 (feishu_notifier.py)
   • Webhook 方式
   • 文本或卡片格式
```

## 配置说明

### config.json

```json
{
  "feishu": {
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK"
  },
  "litellm": {
    "api_key": "sk--xxx",
    "base_url": "http://47.253.161.79:8888"
  },
  "arxiv": {
    "search_keywords": [
      "agent memory",
      "agentic memory",
      "llm memory"
    ],
    "max_results_per_keyword": 10,
    "days_back": 7
  },
  "recommendation": {
    "min_papers": 3,
    "max_papers": 5,
    "schedule_time": "10:00",
    "workdays_only": true
  },
  "brave": {
    "api_key": "BSA_xxx",
    "enabled": true,
    "max_enrich": 5
  }
}
```

**关键参数**：
- `brave.enabled` - 是否启用社区验证
- `brave.max_enrich` - 最多增强几篇论文
- `arxiv.search_keywords` - 减少关键词可降低限流风险
- `recommendation.max_papers` - 每日推荐数量

## 常用命令

```bash
# 启动 Web 服务器（推荐方式）
cd scripts && ./serve.sh 8889

# 然后在浏览器中：
# - 点击 🔄 按钮更新论文
# - 点击 📚 知识库管理建议
```

### 命令行方式（备用）

```bash
# 每日推荐
python3 src/main.py --mode daily

# 手动添加论文
python3 src/main.py --mode add --url https://arxiv.org/abs/XXXX

# 知识库管理（建议使用 Web 界面）
python3 src/main.py --mode kb                              # 查看统计
python3 src/main.py --mode kb-approve --suggestion-id 1    # 采纳建议
python3 src/main.py --mode kb-reject --suggestion-id 1     # 拒绝建议
```

### 定时任务

```bash
# 设置 cron 定时任务（每工作日 10:00 自动运行）
cd scripts && ./setup_cron.sh
```

### 测试

```bash
python3 tests/run_tests.py              # 运行所有测试
python3 tests/test_litellm.py           # LiteLLM 连接
python3 tests/test_feishu_webhook.py    # 飞书推送
```

## 知识库管理

### 工作流程

```
1. 每日推荐时，Claude AI 会参考 knowledge_base.md 进行分析
   ↓
2. 如果论文有显著创新，AI 会生成知识库更新建议
   • new_paper - 新增论文到前沿论文章节
   • new_concept - 新增概念到相关章节
   • new_technique - 新增技术
   • update_section - 更新章节内容
   ↓
3. 建议保存到 references/kb_suggestions.json（待确认状态）
   ↓
4. 用户在 Web 界面确认：
   • 点击 📚 知识库按钮
   • 切换到「待确认建议」标签
   • 点击「采纳」或「拒绝」
   ↓
5. 确认后，内容自动添加到 knowledge_base.md
```

### 后端 API

服务器提供以下 API：

| API | 方法 | 说明 |
|-----|------|------|
| `/api/run-daily` | POST | 触发每日论文更新 |
| `/api/approve-suggestion` | POST | 采纳知识库建议 |
| `/api/reject-suggestion` | POST | 拒绝知识库建议 |

### 前端知识库功能

在 Web 界面（papers.html）中：
- 点击左侧 **📚 知识库** 按钮进入知识库视图
- **知识库内容** 标签：预览完整的领域知识框架
- **待确认建议** 标签：查看 AI 生成的更新建议，可采纳或拒绝
- **历史记录** 标签：查看已处理的建议

## 关键特性

### 1. arXiv 限流处理
- 请求间延迟：3 秒/关键词
- 自动重试：最多 3 次，递增等待（10s, 20s, 30s）
- 错误检测：区分限流（429/503）和其他错误
- 详细日志：显示进度和状态

### 2. Brave 社区验证 ⭐
- **不是搜索论文来源**，而是验证 arXiv 论文的社区热度
- 查找 GitHub 仓库和 stars
- 查找 Twitter/Reddit/HN 讨论
- 计算社交分数（0-100）
- 调整质量评分

### 3. 智能过滤
- 垃圾内容过滤（scam/spam/debt等）
- 相关性验证（必须包含 arxiv/paper/research）
- 讨论相关性排序

### 4. 社交分数算法
```
分数 = min(40, 10*log10(stars+1))     # GitHub stars
     + min(30, discussions × 3)        # 讨论数量
     + platforms × 5                   # 平台多样性
     + min(15, hn_mentions × 8)        # HN 加成

调整后评分 = 原始评分 × 0.8 + 社交分数 × 0.2
```

## 维护任务

### 日常
- 监控 cron 日志：`tail -f logs/cron.log`
- 查看每日日志：`tail -f logs/daily_$(date +%Y%m%d).log`
- 检查 papers.json 大小

### 定期
- 备份 papers.json
- 检查 API 配额使用
- 调整搜索关键词
- 审查推荐质量

### 优化
- 如果频繁限流：减少关键词或增加延迟
- 如果结果太少：增加 days_back 或关键词
- 如果质量不高：调整 quality_threshold
- 如果社交分数不准：调整权重

## API 配额

### LiteLLM
- 每日推荐：约 15 次调用
- 月度：约 450 次（工作日）
- 成本：自定义

### Brave Search
- 每篇增强：约 4 次调用
- 每日推荐：约 20 次（5篇×4）
- 月度：约 600 次
- 配额：2000 次/月（充足）

## 故障排除

### arXiv 限流
```bash
# 症状：HTTP 429/503
# 解决：减少关键词或增加延迟
# 修改 config.json:
"search_keywords": ["agent memory", "llm memory"]  # 只保留 2-3 个
```

### Claude 分析失败
```bash
# 测试连接
python3 tests/test_litellm.py

# 检查配置
cat config.json | grep -A 3 litellm
```

### 飞书推送失败
```bash
# 测试 Webhook
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"test"}}'
```

### Brave 增强失败
```bash
# 测试 API
python3 tests/test_brave_api.py

# 或暂时禁用
# config.json: "brave.enabled": false
```

## 代码规范

### 模块导入方式
```python
# 从子模块导入
from src.fetchers import ArxivFetcher, BraveSearcher, HybridFetcher
from src.analyzers import PaperAnalyzer, PaperEnricher
from src.notifiers import FeishuNotifier
from src.storage import PaperManager
from src.utils import load_config, get_logger
```

### 添加新功能
1. 在对应子模块目录创建新文件
2. 更新子模块 `__init__.py` 导出
3. 更新 `main.py` 集成
4. 添加测试脚本
5. 更新 CLAUDE.md

### 修改搜索逻辑
- 优先修改 `src/fetchers/arxiv.py`
- Brave 仅用于增强，不用于主搜索
- 保持限流控制

### 修改分析逻辑
- 修改 `src/analyzers/paper_analyzer.py` 的 prompt
- 调整质量评分权重
- 更新 `src/analyzers/paper_enricher.py` 的社交分数计算

## 监控指标

### 成功率
```bash
grep "Added.*papers" logs/daily_*.log | tail -5
```

### 限流情况
```bash
grep "Rate limited" logs/daily_*.log | wc -l
```

### 增强统计
```bash
grep "增强统计" logs/daily_*.log | tail -1
```

---

**维护者注意**：
- 保持配置简洁，避免过度复杂
- 优先使用 arXiv，Brave 仅作验证
- 定期审查推荐质量
- 备份 papers.json
