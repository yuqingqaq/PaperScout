"""
混合论文抓取器
结合 arXiv API、Brave Search 和 Semantic Scholar，智能选择最佳策略
"""
from typing import List, Dict, Optional
import time
import requests

from .arxiv import ArxivFetcher
from .brave import BraveSearcher
from ..utils import get_logger

logger = get_logger('fetchers.hybrid')


class HybridFetcher:
    """混合使用 arXiv、Brave 和 Semantic Scholar 的智能抓取器"""

    def __init__(self, config: dict):
        self.config = config
        self.arxiv_fetcher = ArxivFetcher(config)

        # 检查是否启用 Brave
        self.brave_enabled = config.get('brave', {}).get('enabled', False)
        if self.brave_enabled:
            brave_api_key = config.get('brave', {}).get('api_key')
            if brave_api_key and brave_api_key != "YOUR_BRAVE_API_KEY":
                self.brave_searcher = BraveSearcher(brave_api_key)
            else:
                logger.warning("Brave API 未配置，仅使用 arXiv")
                self.brave_enabled = False
                self.brave_searcher = None
        else:
            self.brave_searcher = None
        
        # Semantic Scholar 配置
        self.semantic_scholar_enabled = config.get('semantic_scholar', {}).get('enabled', True)

    def search_papers(self, days_back: int = 7, use_brave_fallback: bool = True) -> List[Dict]:
        """
        智能搜索论文

        策略：
        1. 优先使用 arXiv API（带限流控制）
        2. 使用 Semantic Scholar 补充高引用论文
        3. 如果 arXiv 失败或结果太少，使用 Brave 补充
        4. 合并去重

        Args:
            days_back: 搜索最近多少天
            use_brave_fallback: 是否使用 Brave 作为备用

        Returns:
            论文列表
        """
        logger.info("=" * 50)
        logger.info("🔍 混合搜索模式")
        logger.info("=" * 50)

        # Step 1: arXiv 搜索
        logger.info("Phase 1: arXiv API 搜索")
        arxiv_papers = []
        try:
            arxiv_papers = self.arxiv_fetcher.search_papers(days_back=days_back)
            logger.info(f"✓ arXiv 找到 {len(arxiv_papers)} 篇论文")
        except Exception as e:
            logger.error(f"✗ arXiv 搜索失败: {e}")

        # Step 2: Semantic Scholar 补充
        semantic_papers = []
        if self.semantic_scholar_enabled:
            logger.info("Phase 2: Semantic Scholar 补充（高引用论文）")
            try:
                semantic_papers = self._search_with_semantic_scholar()
                logger.info(f"✓ Semantic Scholar 找到 {len(semantic_papers)} 篇论文")
            except Exception as e:
                logger.error(f"✗ Semantic Scholar 搜索失败: {e}")

        # Step 3: Brave 搜索（如果启用且需要）
        brave_papers = []
        if self.brave_enabled and use_brave_fallback:
            if len(arxiv_papers) + len(semantic_papers) < 10:
                logger.info("Phase 3: Brave Search 补充（结果较少）")
                try:
                    brave_papers = self._search_with_brave(days_back)
                    logger.info(f"✓ Brave 找到 {len(brave_papers)} 篇额外论文")
                except Exception as e:
                    logger.error(f"✗ Brave 搜索失败: {e}")

        # Step 4: 合并和去重
        logger.info("Phase 4: 合并和去重")
        merged_papers = self._merge_papers(arxiv_papers, semantic_papers, brave_papers)
        logger.info(f"✓ 总共 {len(merged_papers)} 篇唯一论文")

        return merged_papers

    def _search_with_semantic_scholar(self, limit: int = 20) -> List[Dict]:
        """使用 Semantic Scholar 搜索高引用论文"""
        keywords = self.config.get('arxiv', {}).get('search_keywords', [])
        all_papers = []
        seen_ids = set()
        
        # 获取 API key（如果配置了）
        api_key = self.config.get('semantic_scholar', {}).get('api_key', '')
        headers = {'x-api-key': api_key} if api_key else {}
        
        # 只用一个最核心的关键词
        main_keyword = keywords[0] if keywords else 'LLM memory agent'
        
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            'query': main_keyword,
            'limit': limit,
            'year': '2024-',  # 只要 2024 年及之后的论文
            'fields': 'title,year,citationCount,externalIds',
            'fieldsOfStudy': 'Computer Science'
        }
        
        # 重试机制：每秒尝试一次，最多10次
        max_retries = 10
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"  Semantic Scholar 搜索 (尝试 {attempt}/{max_retries}): {main_keyword}")
                response = requests.get(url, params=params, headers=headers, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"    ✓ Semantic Scholar 返回 {len(data.get('data', []))} 条结果")
                    
                    for item in data.get('data', []):
                        # 提取 arXiv ID
                        external_ids = item.get('externalIds', {}) or {}
                        arxiv_id = external_ids.get('ArXiv')
                        
                        if not arxiv_id or arxiv_id in seen_ids:
                            continue
                        
                        seen_ids.add(arxiv_id)
                        
                        # 获取完整的 arXiv 信息
                        full_paper = self.arxiv_fetcher.get_paper_by_id(arxiv_id)
                        
                        if full_paper:
                            full_paper['citation_count'] = item.get('citationCount', 0)
                            full_paper['source'] = 'semantic_scholar'
                            all_papers.append(full_paper)
                            logger.debug(f"    ✓ 添加论文: {full_paper.get('title', '')[:40]}... (引用: {item.get('citationCount', 0)})")
                        
                        time.sleep(0.3)  # arXiv API 限流保护
                    
                    break  # 成功，退出重试循环
                    
                elif response.status_code == 429:
                    if attempt < max_retries:
                        logger.warning(f"    Semantic Scholar 限流 (429)，1秒后重试 ({attempt}/{max_retries})...")
                        time.sleep(1)
                    else:
                        logger.warning(f"    Semantic Scholar 限流，已重试 {max_retries} 次，跳过")
                else:
                    logger.warning(f"    Semantic Scholar API 返回 {response.status_code}")
                    break
                    
            except Exception as e:
                logger.warning(f"  Semantic Scholar 搜索失败: {e}")
                break
        
        # 按引用数排序
        all_papers.sort(key=lambda x: x.get('citation_count', 0), reverse=True)
        return all_papers

    def _search_with_brave(self, days: int = 7) -> List[Dict]:
        """使用 Brave 搜索论文"""
        keywords = self.config.get('arxiv', {}).get('search_keywords', [])
        brave_papers = []

        for keyword in keywords[:3]:
            logger.debug(f"  Brave 搜索: {keyword}")
            try:
                papers = self.brave_searcher.search_arxiv_papers(keyword, days=days)

                for paper in papers:
                    arxiv_id = paper['arxiv_id']
                    full_paper = self.arxiv_fetcher.get_paper_by_id(arxiv_id)

                    if full_paper:
                        brave_papers.append(full_paper)
                    else:
                        brave_papers.append({
                            'arxiv_id': arxiv_id,
                            'title': paper.get('title', 'Unknown'),
                            'authors': 'Unknown',
                            'published': 'Unknown',
                            'abstract': paper.get('description', ''),
                            'arxiv_url': f"https://arxiv.org/abs/{arxiv_id}",
                            'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}",
                            'source': 'brave'
                        })

                time.sleep(1)

            except Exception as e:
                logger.error(f"  Brave 关键词 '{keyword}' 搜索失败: {e}")
                continue

        return brave_papers

    def _merge_papers(self, arxiv_papers: List[Dict], semantic_papers: List[Dict], brave_papers: List[Dict]) -> List[Dict]:
        """合并 arXiv、Semantic Scholar 和 Brave 的结果，去重"""
        merged = []
        seen_ids = set()

        # 优先级：arXiv > Semantic Scholar > Brave
        for paper in arxiv_papers:
            arxiv_id = paper.get('arxiv_id')
            if arxiv_id and arxiv_id not in seen_ids:
                seen_ids.add(arxiv_id)
                if 'source' not in paper:
                    paper['source'] = 'arxiv'
                merged.append(paper)

        for paper in semantic_papers:
            arxiv_id = paper.get('arxiv_id')
            if arxiv_id and arxiv_id not in seen_ids:
                seen_ids.add(arxiv_id)
                merged.append(paper)

        for paper in brave_papers:
            arxiv_id = paper.get('arxiv_id')
            if arxiv_id and arxiv_id not in seen_ids:
                seen_ids.add(arxiv_id)
                if 'source' not in paper:
                    paper['source'] = 'brave'
                merged.append(paper)

        return merged

    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """获取单篇论文（代理到 arxiv_fetcher）"""
        return self.arxiv_fetcher.get_paper_by_id(arxiv_id)

    def get_paper_with_metadata(self, arxiv_id: str) -> Optional[Dict]:
        """获取论文及其补充元数据"""
        paper = self.arxiv_fetcher.get_paper_by_id(arxiv_id)

        if not paper:
            return None

        if self.brave_enabled:
            try:
                discussions = self.brave_searcher.search_paper_discussions(
                    arxiv_id,
                    paper_title=paper.get('title')
                )

                if discussions:
                    paper['discussions'] = discussions
                    paper['discussion_count'] = len(discussions)
                    logger.info(f"  找到 {len(discussions)} 条讨论")

            except Exception as e:
                logger.warning(f"  获取讨论失败: {e}")

        return paper

    def get_trending_papers(self, count: int = 10) -> List[Dict]:
        """获取热门论文（基于 Brave 搜索）"""
        if not self.brave_enabled:
            logger.warning("Brave Search 未启用，无法获取热门论文")
            return []

        keywords = self.config.get('arxiv', {}).get('search_keywords', [])
        logger.info(f"🔥 搜索热门论文（{len(keywords)} 个关键词）...")

        try:
            popular_papers = self.brave_searcher.get_popular_papers(
                keywords=keywords,
                count=count
            )

            enriched_papers = []
            for paper in popular_papers:
                arxiv_id = paper['arxiv_id']
                full_paper = self.arxiv_fetcher.get_paper_by_id(arxiv_id)

                if full_paper:
                    full_paper['brave_metadata'] = {
                        'age': paper.get('age', ''),
                        'search_keyword': paper.get('search_keyword', '')
                    }
                    enriched_papers.append(full_paper)
                    time.sleep(1)

            return enriched_papers

        except Exception as e:
            logger.error(f"获取热门论文失败: {e}")
            return []
