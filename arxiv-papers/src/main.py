"""
ArXiv Papers 主程序
每日自动推荐或手动添加论文
"""
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# 添加项目根目录到路径，支持直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetchers import HybridFetcher, ArxivFetcher
from src.analyzers import PaperAnalyzer, PaperEnricher
from src.storage import PaperManager, KnowledgeBaseManager
from src.notifiers import FeishuNotifier
from src.utils import load_config, validate_config, ConfigError, setup_logging, get_logger


class ArxivPapersAgent:
    """ArXiv 论文推荐 Agent"""

    def __init__(self, config_path: str, search_mode: str = 'hybrid'):
        """
        初始化 Agent
        
        Args:
            config_path: 配置文件路径
            search_mode: 搜索模式 - 'hybrid'(混合), 'arxiv'(仅arXiv), 'semantic'(仅语义搜索)
        """
        self.logger = get_logger('agent')
        self.config_path = config_path
        
        # 加载和验证配置
        self.config = load_config(config_path)
        warnings = validate_config(self.config)
        for warning in warnings:
            self.logger.warning(warning)

        # 初始化知识库管理器
        self.kb_manager = KnowledgeBaseManager(
            kb_path=os.path.join(
                os.path.dirname(config_path),
                'references',
                'knowledge_base.md'
            )
        )
        self.logger.info("✓ 知识库管理器已初始化")

        # 初始化论文抓取器
        self.search_mode = search_mode
        if search_mode == 'semantic':
            self.fetcher = HybridFetcher(self.config, search_mode='semantic')
            self.logger.info("✓ 使用 Semantic Scholar 语义搜索模式")
        elif search_mode == 'hybrid' and self.config.get('brave', {}).get('enabled', False):
            self.fetcher = HybridFetcher(self.config, search_mode='hybrid')
            self.logger.info("✓ 使用混合搜索模式 (arXiv + Semantic + Brave)")
        else:
            self.fetcher = ArxivFetcher(self.config)
            self.logger.info("✓ 使用 arXiv 搜索模式")

        # 获取知识库上下文用于分析
        kb_context = self.kb_manager.get_context_for_analysis()

        # 初始化 AI 分析器（带知识库上下文）
        if 'litellm' in self.config:
            self.analyzer = PaperAnalyzer(
                api_key=self.config['litellm']['api_key'],
                base_url=self.config['litellm'].get('base_url'),
                knowledge_base_context=kb_context
            )
            self.logger.info("✓ 使用 LiteLLM API (带知识库上下文)")
        else:
            self.analyzer = PaperAnalyzer(
                api_key=self.config['anthropic']['api_key'],
                knowledge_base_context=kb_context
            )
            self.logger.info("✓ 使用 Anthropic API (带知识库上下文)")
            
        # 初始化论文管理器
        self.paper_manager = PaperManager(
            json_path=os.path.join(
                os.path.dirname(config_path),
                'output',
                'papers.json'
            )
        )
        
        # 初始化飞书通知
        self.notifier = self._init_notifier()

        # 初始化论文增强器
        self.enricher = self._init_enricher()

    def _init_notifier(self) -> Optional[FeishuNotifier]:
        """初始化飞书通知器"""
        feishu_config = self.config.get('feishu', {})
        webhook_url = feishu_config.get('webhook_url')
        
        if webhook_url and 'YOUR_WEBHOOK' not in webhook_url:
            self.logger.info("✓ 飞书通知已启用")
            return FeishuNotifier(webhook_url=webhook_url)
        else:
            self.logger.warning("⚠️  飞书通知未配置")
            return None

    def _init_enricher(self) -> Optional[PaperEnricher]:
        """初始化论文增强器"""
        brave_config = self.config.get('brave', {})
        
        if not brave_config.get('enabled', False):
            return None
            
        api_key = brave_config.get('api_key', '')
        if api_key and api_key != "YOUR_BRAVE_API_KEY":
            self.logger.info("✓ Brave Search 论文增强已启用")
            
            # 传递 LiteLLM 配置用于 AI 相关性验证
            litellm_config = self.config.get('litellm')
            return PaperEnricher(api_key, litellm_config=litellm_config)
        else:
            self.logger.warning("⚠️  Brave API Key 未配置，跳过论文增强")
            return None

    def daily_recommendation(self) -> List[Dict]:
        """
        每日论文推荐流程

        Returns:
            推荐的论文列表
        """
        self.logger.info(f"开始每日推荐流程...")

        # 1. 搜索论文
        self.logger.info("Step 1: 搜索论文...")
        days_back = self.config['arxiv'].get('days_back', 7)
        papers = self.fetcher.search_papers(days_back=days_back)
        self.logger.info(f"找到 {len(papers)} 篇论文")

        if not papers:
            self.logger.warning("未找到论文")
            return []

        # 1.5 排除已存在的论文和已分析过的论文
        existing_ids = set(self.paper_manager.get_all_arxiv_ids())
        analyzed_ids = self.paper_manager.load_analyzed_ids()
        skip_ids = existing_ids | analyzed_ids
        
        new_papers = [p for p in papers if p['arxiv_id'] not in skip_ids]
        
        skipped_existing = len([p for p in papers if p['arxiv_id'] in existing_ids])
        skipped_analyzed = len([p for p in papers if p['arxiv_id'] in analyzed_ids and p['arxiv_id'] not in existing_ids])
        
        if skipped_existing > 0 or skipped_analyzed > 0:
            self.logger.info(f"排除 {skipped_existing} 篇已推荐 + {skipped_analyzed} 篇已分析，剩余 {len(new_papers)} 篇新论文")
        
        if not new_papers:
            self.logger.info("✓ 没有新论文需要推荐")
            return []
        
        papers = new_papers

        # 2. 分析论文
        self.logger.info("Step 2: AI 分析论文...")
        analyzed_papers = []
        
        for i, paper in enumerate(papers, 1):
            self.logger.info(f"  [{i}/{len(papers)}] {paper['title'][:50]}...")
            analysis = self.analyzer.analyze_paper(paper)

            # 输出相关度信息
            relevance = analysis.get('relevance', 0)
            quality = analysis.get('quality_score', 0)
            self.logger.info(f"    → 相关度: {relevance:.2f} | 质量: {quality} | {'✓ 强相关' if relevance >= 0.7 else '✗ 弱相关'}")

            # 先不处理 kb_suggestions，等筛选后再处理
            # 合并分析结果
            paper.update(analysis)
            analyzed_papers.append(paper)

        # 2.5 记录所有已分析的论文 ID（包括弱相关的）
        analyzed_arxiv_ids = [p['arxiv_id'] for p in analyzed_papers]
        self.paper_manager.add_analyzed_ids(analyzed_arxiv_ids)
        self.logger.info(f"已记录 {len(analyzed_arxiv_ids)} 篇论文到已分析列表")

        # 3. 筛选高价值论文
        self.logger.info("Step 3: 排序和筛选论文...")
        ranked_papers = self.analyzer.rank_papers(analyzed_papers)

        max_papers = self.config['recommendation'].get('max_papers', 10)
        strict_relevance = self.config['recommendation'].get('strict_relevance', True)

        # 选择质量分数 >= 70 且领域强相关的论文
        if strict_relevance:
            # 严格模式：只选择领域强相关的论文（relevance >= 0.7）
            recommended = [
                p for p in ranked_papers
                if p.get('quality_score', 0) >= 70 and p.get('relevance', 0) >= 0.7
            ][:max_papers]
        else:
            recommended = [
                p for p in ranked_papers
                if p.get('quality_score', 0) >= 70
            ][:max_papers]

        # 不再补充低分论文，宁缺毋滥
        self.logger.info(f"筛选出 {len(recommended)} 篇强相关推荐论文")

        # 3.5 只从推荐论文中收集知识库建议（宏观层面）
        kb_suggestions_collected = []
        for paper in recommended:
            paper_kb_suggestions = paper.pop('kb_suggestions', [])
            if paper_kb_suggestions:
                for suggestion in paper_kb_suggestions:
                    suggestion['paper_arxiv_id'] = paper['arxiv_id']
                    suggestion['paper_title'] = paper['title']
                    kb_suggestions_collected.append(suggestion)
                self.logger.info(f"💡 {paper['title'][:40]}... 生成 {len(paper_kb_suggestions)} 条宏观建议")

        # 4. 使用 Brave 增强论文（如果启用）
        if self.enricher:
            self.logger.info("Step 4: 社区信号增强...")
            recommended = self.enricher.batch_enrich_papers(
                recommended,
                max_papers=self.config.get('brave', {}).get('max_enrich', 5)
            )

            # 显示增强统计
            summary = self.enricher.get_enrichment_summary(recommended)
            self.logger.info(f"📊 增强统计: {summary['enriched_papers']}/{summary['total_papers']} 篇, "
                           f"GitHub: {summary['total_github_repos']} 仓库 ({summary['total_stars']} stars), "
                           f"讨论: {summary['total_discussions']} 条")

            # 按调整后的质量分数重新排序
            recommended.sort(
                key=lambda x: x.get('quality_score_adjusted', x.get('quality_score', 0)),
                reverse=True
            )

        # 5. 添加到数据库
        self.logger.info("Step 5: 保存到数据库...")
        added_count = self.paper_manager.add_papers(recommended)
        self.logger.info(f"新增 {added_count} 篇论文")

        # 5.5 保存知识库更新建议
        if kb_suggestions_collected:
            self.logger.info("Step 5.5: 保存知识库更新建议...")
            suggestions_added = self.kb_manager.add_suggestions_batch(kb_suggestions_collected)
            self.logger.info(f"💡 新增 {suggestions_added} 条知识库建议（待用户确认）")

        # 6. 生成趋势总结
        trend_summary = self.analyzer.generate_trend_summary(recommended)

        # 7. 发送飞书通知
        if self.notifier:
            self.logger.info("Step 6: 发送飞书通知...")
            total_papers = self.paper_manager.get_total_count()

            # 优先使用卡片消息（更美观）
            success = self.notifier.send_card(
                papers=recommended,
                total_papers=total_papers,
                trend_summary=trend_summary
            )

            if success:
                self.logger.info("✓ 飞书卡片通知发送成功")
            else:
                # 卡片失败时回退到普通消息
                self.logger.warning("卡片消息失败，尝试普通消息...")
                success = self.notifier.send_daily_recommendation(
                    papers=recommended,
                    total_papers=total_papers,
                    trend_summary=trend_summary
                )
                if success:
                    self.logger.info("✓ 飞书通知发送成功")
                else:
                    self.logger.error("✗ 飞书通知发送失败")
        else:
            self.logger.info("Step 6: 跳过飞书通知（未配置）")

        # 7. 导出知识库 JSON 供前端使用
        self.logger.info("Step 7: 导出知识库数据...")
        kb_json_path = os.path.join(os.path.dirname(self.config_path), 'output', 'kb_data.json')
        self.kb_manager.export_to_json(kb_json_path)

        self.logger.info(f"✅ 每日推荐完成，共推荐 {len(recommended)} 篇论文")
        return recommended

    def add_paper_by_url(self, arxiv_url: str, include_references: bool = False) -> Optional[Dict]:
        """
        手动添加论文

        Args:
            arxiv_url: arXiv URL (例如: https://arxiv.org/abs/2512.13564)
            include_references: 是否同时添加前置工作

        Returns:
            添加的论文信息
        """
        # 提取 arXiv ID
        arxiv_id = arxiv_url.split('/')[-1].replace('abs/', '').replace('pdf/', '')
        self.logger.info(f"添加论文: {arxiv_id}")

        # 获取论文信息（使用基础 fetcher）
        if hasattr(self.fetcher, 'arxiv_fetcher'):
            paper = self.fetcher.arxiv_fetcher.get_paper_by_id(arxiv_id)
        else:
            paper = self.fetcher.get_paper_by_id(arxiv_id)
            
        if not paper:
            self.logger.error(f"获取论文失败: {arxiv_id}")
            return None

        # 分析论文
        self.logger.info(f"分析论文: {paper['title'][:50]}...")
        analysis = self.analyzer.analyze_paper(paper)
        paper.update(analysis)

        # 添加到数据库
        self.paper_manager.add_paper(paper)
        self.logger.info(f"✓ 已添加: {paper['title']}")

        # 如果需要，添加前置工作
        if include_references:
            self.logger.info("提取参考文献...")
            ref_keywords = self.analyzer.extract_references(
                paper['abstract']
            )

            for keyword in ref_keywords[:3]:  # 最多3个
                self.logger.info(f"搜索参考: {keyword}")
                # 这里可以扩展搜索逻辑

        return paper

    def get_papers_summary(self) -> Dict:
        """
        获取论文库统计信息

        Returns:
            统计信息字典
        """
        total = self.paper_manager.get_total_count()
        recent = len(self.paper_manager.get_recent_papers(days=7))

        return {
            'total_papers': total,
            'recent_7_days': recent
        }


def main():
    """主函数"""
    import argparse

    # 获取脚本所在目录的上级目录（项目根目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    default_config = os.path.join(project_root, 'config.json')
    log_dir = os.path.join(project_root, 'logs')

    parser = argparse.ArgumentParser(description='ArXiv Papers Agent')
    parser.add_argument(
        '--config',
        default=default_config,
        help='Path to config.json'
    )
    parser.add_argument(
        '--mode',
        choices=['daily', 'add', 'summary', 'kb', 'kb-approve', 'kb-reject'],
        default='daily',
        help='Run mode: daily recommendation, add paper, show summary, kb management'
    )
    parser.add_argument(
        '--url',
        help='ArXiv URL (for add mode)'
    )
    parser.add_argument(
        '--suggestion-id',
        type=int,
        help='Suggestion ID (for kb-approve/kb-reject modes)'
    )
    parser.add_argument(
        '--reject-reason',
        help='Rejection reason (for kb-reject mode)'
    )
    parser.add_argument(
        '--include-refs',
        action='store_true',
        help='Include references when adding paper'
    )
    parser.add_argument(
        '--search-mode', '-s',
        choices=['hybrid', 'arxiv', 'semantic'],
        default='hybrid',
        help='Search mode: hybrid (default), arxiv (keyword only), semantic (Semantic Scholar only)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # 设置日志
    import logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_dir=log_dir, level=log_level)
    logger = get_logger('main')

    try:
        # 初始化 Agent
        agent = ArxivPapersAgent(
            args.config, 
            search_mode=args.search_mode
        )

        if args.mode == 'daily':
            # 每日推荐
            agent.daily_recommendation()

        elif args.mode == 'add':
            # 手动添加论文
            if not args.url:
                logger.error("Error: --url is required for add mode")
                sys.exit(1)

            agent.add_paper_by_url(args.url, include_references=args.include_refs)

        elif args.mode == 'summary':
            # 显示统计信息
            summary = agent.get_papers_summary()
            logger.info(f"论文库统计:")
            logger.info(f"  总论文数: {summary['total_papers']}")
            logger.info(f"  近7天: {summary['recent_7_days']}")

        elif args.mode == 'kb':
            # 显示知识库统计和待处理建议
            kb_stats = agent.kb_manager.get_stats()
            logger.info(f"知识库统计:")
            logger.info(f"  章节数: {kb_stats['total_sections']}")
            logger.info(f"  子章节数: {kb_stats['total_subsections']}")
            logger.info(f"  引用论文: {kb_stats['total_referenced_papers']}")
            logger.info(f"  内容长度: {kb_stats['content_length']} 字符")
            logger.info(f"待处理建议:")
            logger.info(f"  待确认: {kb_stats['pending_suggestions']}")
            logger.info(f"  已采纳: {kb_stats['approved_suggestions']}")
            logger.info(f"  已拒绝: {kb_stats['rejected_suggestions']}")
            
            # 列出待确认建议
            pending = agent.kb_manager.get_pending_suggestions()
            if pending:
                logger.info(f"\n待确认的建议:")
                for s in pending:
                    logger.info(f"  [{s['id']}] {s.get('suggestion_type', s.get('type', 'unknown'))} - {s.get('content', '')[:60]}...")
                    logger.info(f"      来源: {s.get('paper_title', s.get('paper_arxiv_id', 'unknown'))}")

        elif args.mode == 'kb-approve':
            # 批准知识库建议
            if not args.suggestion_id:
                logger.error("Error: --suggestion-id is required for kb-approve mode")
                sys.exit(1)
            
            success = agent.kb_manager.approve_suggestion(args.suggestion_id)
            if success:
                logger.info(f"✓ 建议 {args.suggestion_id} 已应用到知识库")
            else:
                logger.error(f"✗ 应用建议 {args.suggestion_id} 失败")

        elif args.mode == 'kb-reject':
            # 拒绝知识库建议
            if not args.suggestion_id:
                logger.error("Error: --suggestion-id is required for kb-reject mode")
                sys.exit(1)
            
            reason = args.reject_reason or ""
            success = agent.kb_manager.reject_suggestion(args.suggestion_id, reason)
            if success:
                logger.info(f"✓ 建议 {args.suggestion_id} 已拒绝")
            else:
                logger.error(f"✗ 拒绝建议 {args.suggestion_id} 失败")

    except ConfigError as e:
        logger.error(f"配置错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("用户中断")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"运行错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
