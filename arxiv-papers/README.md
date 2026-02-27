# ArXiv Papers - Agent Memory 论文推荐系统

专注 Agent Memory / Agentic Memory 领域的智能论文推荐系统。

## ✨ 特性

- 🤖 **自动推荐**：每工作日 10:00 自动抓取、分析并推荐 3-5 篇高质量论文
- 🧠 **AI 分析**：使用 Claude AI 深度评估论文质量和价值
- 📊 **社区验证**：使用 Brave Search 获取 GitHub stars、社区讨论等社区信号
- 📬 **飞书推送**：自动推送每日推荐到飞书群组（Webhook）
- 🌐 **Web 展示**：精美的响应式论文库界面
- ✋ **手动添加**：支持手动添加论文及其前置工作

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.json`，填写必需的配置：

```json
{
  "feishu": {
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK"
  },
  "litellm": {
    "api_key": "your_litellm_api_key",
    "base_url": "http://your-litellm-server:8888"
  },
  "brave": {
    "api_key": "your_brave_api_key",
    "enabled": true,
    "max_enrich": 5
  }
}
```

**获取配置**：
- **飞书 Webhook**：在飞书群组添加自定义机器人，复制 Webhook URL
- **LiteLLM**：使用你的 LiteLLM 服务器地址和 API Key
- **Brave API**：访问 https://brave.com/search/api/ 获取（免费 2000 次/月）

### 3. 测试

```bash
# 运行所有测试
python3 tests/run_tests.py

# 运行指定测试
python3 tests/run_tests.py --test config
python3 tests/run_tests.py --test litellm
python3 tests/run_tests.py --test feishu
python3 tests/run_tests.py --test brave
```

### 4. 运行

```bash
# 每日推荐（默认混合搜索模式）
python3 src/main.py --mode daily

# 选择搜索模式
python3 src/main.py --mode daily -s hybrid    # 混合: arXiv + Semantic Scholar
python3 src/main.py --mode daily -s semantic  # 仅 Semantic Scholar 语义搜索
python3 src/main.py --mode daily -s arxiv     # 仅 arXiv 关键词搜索

# 详细日志模式
python3 src/main.py --mode daily -v

# 启动 Web 界面
cd scripts && ./serve.sh 8889
# 访问: http://localhost:8889/papers.html

# 手动添加论文
python3 src/main.py --mode add --url https://arxiv.org/abs/2512.13564

# 查看统计
python3 src/main.py --mode summary
```

### 5. 设置定时任务（可选）

```bash
cd scripts
./setup_cron.sh
```

## 🎯 工作流程

```
arXiv 搜索
  ↓
Claude AI 分析
  ↓
初步质量评分
  ↓
Brave 社区验证 ⭐
  ├─ GitHub stars
  ├─ Twitter 讨论
  ├─ Reddit 讨论
  └─ HN 提及
  ↓
调整后评分
  ↓
保存 + 推送
```

### 评分系统

**质量评分**（Claude AI，0-100）：
- 创新程度：30%
- 领域契合度：30%
- 技术深度：20%
- 实用价值：20%

**社交分数**（Brave Search，0-100）：
- GitHub stars：最多 40 分
- 讨论数量：最多 30 分
- 平台多样性：最多 15 分
- HN 讨论质量：最多 15 分

**最终评分**：
```
调整后评分 = 原始评分 × 0.8 + 社交分数 × 0.2
```

## 📊 数据结构

### papers.json

```json
{
  "metadata": {
    "last_updated": "2026-02-10",
    "total_papers": 10
  },
  "papers": [
    {
      "arxiv_id": "2512.13564",
      "title": "Memory in the Age of AI Agents",
      "authors": "...",
      "published": "2025-12-18",
      "recommend_date": "2026-02-10",
      "abstract": "...",
      "contributions": ["贡献1", "贡献2"],
      "key_results": ["结果1", "结果2"],
      "tags": ["Survey", "Agent Memory"],
      "quality_score_original": 85,
      "quality_score_adjusted": 83,
      "community_signals": {
        "github_repos": [...],
        "discussions": [...],
        "github_stars": 1540,
        "total_discussion_count": 12,
        "social_score": 75
      },
      "recommendation": "首个系统性综述",
      "arxiv_url": "https://arxiv.org/abs/2512.13564",
      "pdf_url": "https://arxiv.org/pdf/2512.13564"
    }
  ]
}
```

## 🔧 常见操作

### 查看论文库
```bash
cd scripts && ./serve.sh 8889
# 访问: http://localhost:8889/papers.html
```

### 手动添加论文
```bash
python3 src/main.py --mode add --url https://arxiv.org/abs/XXXX.XXXXX
```

### 查看统计
```bash
python3 src/main.py --mode summary
```

### 查看日志
```bash
# 今日日志
tail -f logs/daily_$(date +%Y%m%d).log

# Cron 日志
tail -f logs/cron.log
```

## ⚙️ 性能优化

### arXiv 限流控制
- 请求延迟：3 秒/关键词
- 自动重试：最多 3 次
- 推荐关键词数：3-4 个（日常）

### Brave API 使用
- 每篇论文：约 4 次调用
- 每日推荐：约 20 次（5篇）
- 月度消耗：约 600 次
- 配额充足：2000 次/月

### 推荐配置

**稳定优先**（日常定时任务）：
```json
{
  "search_keywords": ["agent memory", "llm memory"],
  "max_results_per_keyword": 10,
  "brave": { "max_enrich": 3 }
}
```

**全面搜索**（手动执行）：
```json
{
  "search_keywords": ["agent memory", "agentic memory", "llm memory", "episodic memory llm"],
  "max_results_per_keyword": 15,
  "brave": { "max_enrich": 10 }
}
```

## 🐛 故障排除

### arXiv 频繁限流
```bash
# 减少关键词数量
"search_keywords": ["agent memory", "llm memory"]

# 或增加延迟
# 修改 src/fetchers/arxiv.py:
time.sleep(5)  # 从 3 秒改为 5 秒
```

### LiteLLM 连接失败
```bash
# 测试连接
python3 test_litellm.py

# 检查网络
curl http://47.253.161.79:8888
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
python3 test_brave_api.py

# 或临时禁用
"brave": { "enabled": false }
```

## 📚 相关资源

- **arXiv API**: https://arxiv.org/help/api
- **Brave Search API**: https://brave.com/search/api/
- **飞书开放平台**: https://open.feishu.cn/
- **LiteLLM**: https://docs.litellm.ai/

## 📖 领域知识

参考 `references/knowledge_base.md` 了解：
- Agent Memory 核心框架
- 重要研究方向
- 关键技术
- 前沿论文

## 🎯 论文筛选标准

| 维度 | 权重 | 指标 |
|------|------|------|
| 学术质量 | 40% | Claude AI 评估 |
| 创新程度 | 20% | 新范式、新架构 |
| 领域契合 | 20% | 与 Agent Memory 相关性 |
| 社区验证 | 20% | GitHub stars、讨论热度 |

## 🏗️ 项目结构

```
arxiv-papers/
├── src/                       # 核心代码
│   ├── __init__.py           # 模块导出 (v1.4.0)
│   ├── main.py               # 主程序入口
│   ├── fetchers/             # 数据获取模块
│   │   ├── arxiv.py          # arXiv API 抓取
│   │   ├── brave.py          # Brave Search API
│   │   └── hybrid.py         # 混合搜索策略
│   ├── analyzers/            # 分析模块
│   │   ├── paper_analyzer.py # Claude AI 分析
│   │   └── paper_enricher.py # 社区信号增强
│   ├── notifiers/            # 通知模块
│   │   └── feishu.py         # 飞书推送
│   ├── storage/              # 存储模块
│   │   └── paper_manager.py  # 数据持久化
│   └── utils/                # 工具模块
│       ├── config.py         # 配置加载/验证
│       └── logger.py         # 日志管理
├── tests/                     # 测试模块
│   └── run_tests.py          # 统一测试入口
├── output/                    # 输出文件
│   ├── papers.json           # 论文数据
│   └── papers.html           # Web 界面
├── logs/                      # 日志目录
├── scripts/                   # 脚本
└── config.json               # 配置文件
```

## 📝 License

MIT License

---

**维护者**: FeelingAI Team
**最后更新**: 2026-02-11
**版本**: 1.4.0
