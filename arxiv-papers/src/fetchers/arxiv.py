"""
arXiv 论文抓取模块
"""
import arxiv
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

from ..utils import get_logger

logger = get_logger('fetchers.arxiv')


class ArxivFetcher:
    """从 arXiv 抓取论文"""

    def __init__(self, config: dict):
        self.config = config
        self.arxiv_config = config.get('arxiv', {})

    def search_papers(self, days_back: int = 7) -> List[Dict]:
        """
        搜索最近的论文

        Args:
            days_back: 搜索最近多少天的论文

        Returns:
            论文列表
        """
        all_papers = []
        keywords = self.arxiv_config.get('search_keywords', [])
        max_results = self.arxiv_config.get('max_results_per_keyword', 10)

        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        logger.info(f"搜索 {len(keywords)} 个关键词，请求间隔 3 秒")

        for i, keyword in enumerate(keywords, 1):
            # 添加延迟以避免触发 arXiv 限流
            if i > 1:
                logger.debug(f"等待 3 秒...")
                time.sleep(3)

            try:
                logger.info(f"[{i}/{len(keywords)}] 搜索: '{keyword}'")

                # 使用 arxiv API 搜索，添加重试逻辑
                max_retries = 3
                retry_count = 0

                while retry_count < max_retries:
                    try:
                        search = arxiv.Search(
                            query=keyword,
                            max_results=max_results,
                            sort_by=arxiv.SortCriterion.SubmittedDate,
                            sort_order=arxiv.SortOrder.Descending
                        )

                        papers_found = 0
                        for result in search.results():
                            # 检查发布日期
                            if result.published.replace(tzinfo=None) < start_date:
                                continue

                            paper = {
                                'arxiv_id': result.entry_id.split('/')[-1],
                                'title': result.title.replace('\n', ' ').strip(),
                                'authors': ', '.join([author.name for author in result.authors]),
                                'published': result.published.strftime('%Y-%m-%d'),
                                'abstract': result.summary.replace('\n', ' ').strip(),
                                'arxiv_url': result.entry_id,
                                'pdf_url': result.pdf_url,
                                'categories': result.categories,
                                'primary_category': result.primary_category
                            }

                            # 避免重复
                            if not any(p['arxiv_id'] == paper['arxiv_id'] for p in all_papers):
                                all_papers.append(paper)
                                papers_found += 1

                        logger.info(f"  ✓ 找到 {papers_found} 篇新论文")
                        break  # 成功，退出重试循环

                    except Exception as e:
                        retry_count += 1
                        error_msg = str(e)

                        if 'HTTP 429' in error_msg or 'HTTP 503' in error_msg:
                            if retry_count < max_retries:
                                wait_time = retry_count * 10  # 递增等待时间
                                logger.warning(f"  ⚠ 触发限流，等待 {wait_time}s 后重试 {retry_count}/{max_retries}...")
                                time.sleep(wait_time)
                            else:
                                logger.error(f"  ✗ 重试 {max_retries} 次后失败: {error_msg}")
                        else:
                            logger.error(f"  ✗ 错误: {error_msg}")
                            break

            except Exception as e:
                logger.error(f"  ✗ 关键词 '{keyword}' 搜索异常: {e}")
                continue

        logger.info(f"共找到 {len(all_papers)} 篇唯一论文")
        return all_papers

    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        根据 arXiv ID 获取单篇论文

        Args:
            arxiv_id: arXiv ID (例如: 2512.13564)

        Returns:
            论文信息字典
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                search = arxiv.Search(id_list=[arxiv_id])
                result = next(search.results())

                paper = {
                    'arxiv_id': result.entry_id.split('/')[-1],
                    'title': result.title.replace('\n', ' ').strip(),
                    'authors': ', '.join([author.name for author in result.authors]),
                    'published': result.published.strftime('%Y-%m-%d'),
                    'abstract': result.summary.replace('\n', ' ').strip(),
                    'arxiv_url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'categories': result.categories,
                    'primary_category': result.primary_category
                }

                return paper

            except Exception as e:
                retry_count += 1
                error_msg = str(e)

                if 'HTTP 429' in error_msg or 'HTTP 503' in error_msg:
                    if retry_count < max_retries:
                        wait_time = retry_count * 5
                        logger.warning(f"触发限流，等待 {wait_time}s 后重试 {retry_count}/{max_retries}...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"获取论文 {arxiv_id} 失败（重试 {max_retries} 次）: {e}")
                        return None
                else:
                    logger.error(f"获取论文 {arxiv_id} 失败: {e}")
                    return None

        return None

    def search_semantic_scholar(self, query: str, limit: int = 10) -> List[Dict]:
        """
        从 Semantic Scholar 搜索论文（补充来源）

        Args:
            query: 搜索关键词
            limit: 返回结果数量

        Returns:
            论文列表
        """
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                'query': query,
                'limit': limit,
                'fields': 'title,authors,year,abstract,citationCount,influentialCitationCount,externalIds,url'
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                papers = []

                for item in data.get('data', []):
                    # 提取 arXiv ID（如果有）
                    arxiv_id = None
                    external_ids = item.get('externalIds', {})
                    if 'ArXiv' in external_ids:
                        arxiv_id = external_ids['ArXiv']

                    paper = {
                        'title': item.get('title', ''),
                        'authors': ', '.join([a.get('name', '') for a in item.get('authors', [])]),
                        'year': item.get('year'),
                        'abstract': item.get('abstract', ''),
                        'citation_count': item.get('citationCount', 0),
                        'influential_citation_count': item.get('influentialCitationCount', 0),
                        'url': item.get('url', ''),
                        'arxiv_id': arxiv_id
                    }

                    papers.append(paper)

                return papers

        except Exception as e:
            logger.error(f"Semantic Scholar 搜索失败: {e}")
            return []
