"""
ArXiv Papers - Agent Memory 论文推荐系统

模块结构:
- fetchers/: 论文抓取模块
  - arxiv.py: arXiv API
  - brave.py: Brave Search API
  - hybrid.py: 混合搜索策略
- analyzers/: 分析模块
  - paper_analyzer.py: Claude AI 分析
  - paper_enricher.py: 社区信号增强
- storage/: 数据存储模块
  - paper_manager.py: 论文数据持久化
- notifiers/: 通知模块
  - feishu.py: 飞书通知
- utils/: 工具模块
  - config.py: 配置加载/验证
  - logger.py: 日志管理
"""

__version__ = '1.4.0'
__author__ = 'FeelingAI Team'

from .fetchers import ArxivFetcher, BraveSearcher, HybridFetcher
from .analyzers import PaperAnalyzer, PaperEnricher
from .storage import PaperManager
from .notifiers import FeishuNotifier
from .main import ArxivPapersAgent

__all__ = [
    'ArxivFetcher',
    'BraveSearcher', 
    'HybridFetcher',
    'PaperAnalyzer',
    'PaperEnricher',
    'PaperManager',
    'FeishuNotifier',
    'ArxivPapersAgent',
]
