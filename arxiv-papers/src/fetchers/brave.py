"""
Brave Search API 模块
用于补充 arXiv 搜索，发现热门论文和讨论
"""
import requests
import re
from typing import List, Dict, Optional

from ..utils import get_logger

logger = get_logger('fetchers.brave')


class BraveSearcher:
    """使用 Brave Search API 搜索论文相关内容"""

    def __init__(self, api_key: str):
        """
        初始化 Brave 搜索器

        Args:
            api_key: Brave Search API Key
        """
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    def search_papers(self, query: str, count: int = 10, freshness: str = "pw") -> List[Dict]:
        """
        搜索论文相关内容

        Args:
            query: 搜索关键词
            count: 返回结果数量（最多20）
            freshness: 时间范围
                - pd: 过去一天 (past day)
                - pw: 过去一周 (past week)
                - pm: 过去一月 (past month)
                - py: 过去一年 (past year)

        Returns:
            搜索结果列表
        """
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }

        params = {
            "q": query,
            "count": min(count, 20),
            "freshness": freshness,
            "text_decorations": False,
            "search_lang": "en"
        }

        try:
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get('web', {}).get('results', []):
                    result = {
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'description': item.get('description', ''),
                        'age': item.get('age', ''),
                        'published': item.get('meta_url', {}).get('netloc', ''),
                        'extra_snippets': item.get('extra_snippets', [])
                    }

                    # 尝试提取 arXiv ID
                    arxiv_id = self._extract_arxiv_id(item.get('url', ''))
                    if arxiv_id:
                        result['arxiv_id'] = arxiv_id

                    results.append(result)

                return results

            else:
                logger.error(f"Brave Search API 错误: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Brave 搜索失败: {e}")
            return []

    def search_arxiv_papers(self, topic: str = "agent memory", days: int = 7) -> List[Dict]:
        """
        专门搜索 arXiv 论文（增强版）

        Args:
            topic: 主题
            days: 最近几天

        Returns:
            包含 arXiv ID 和元数据的列表
        """
        query = f'site:arxiv.org/abs "{topic}"'

        if days <= 1:
            freshness = "pd"
        elif days <= 7:
            freshness = "pw"
        elif days <= 30:
            freshness = "pm"
        else:
            freshness = "py"

        results = self.search_papers(query, count=20, freshness=freshness)

        arxiv_papers = []
        seen_ids = set()

        for result in results:
            arxiv_id = result.get('arxiv_id')

            if arxiv_id and 'arxiv.org' in result.get('url', ''):
                if arxiv_id not in seen_ids:
                    seen_ids.add(arxiv_id)
                    arxiv_papers.append({
                        'arxiv_id': arxiv_id,
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'description': result.get('description', ''),
                        'age': result.get('age', '')
                    })

        return arxiv_papers

    def search_trending_papers(self, topics: List[str], days: int = 7) -> List[Dict]:
        """
        搜索多个主题的热门论文

        Args:
            topics: 主题列表
            days: 最近几天

        Returns:
            去重后的搜索结果
        """
        all_results = []
        seen_urls = set()

        for topic in topics:
            query = f'"{topic}" arxiv OR "research paper"'

            if days <= 1:
                freshness = "pd"
            elif days <= 7:
                freshness = "pw"
            elif days <= 30:
                freshness = "pm"
            else:
                freshness = "py"

            results = self.search_papers(query, count=10, freshness=freshness)

            for result in results:
                url = result.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result['topic'] = topic
                    all_results.append(result)

        return all_results

    def search_paper_discussions(self, arxiv_id: str, paper_title: str = None) -> List[Dict]:
        """
        搜索论文的讨论（Twitter, Reddit, HN 等）

        Args:
            arxiv_id: arXiv ID
            paper_title: 论文标题（可选）

        Returns:
            讨论列表
        """
        query1 = f'"{arxiv_id}" arxiv (site:twitter.com OR site:reddit.com OR site:news.ycombinator.com)'
        results1 = self.search_papers(query1, count=5, freshness="pm")

        results2 = []
        if paper_title:
            title_keywords = ' '.join(paper_title.split()[:5])
            query2 = f'"{title_keywords}" arxiv paper (site:twitter.com OR site:reddit.com OR site:news.ycombinator.com)'
            results2 = self.search_papers(query2, count=5, freshness="pm")

        all_results = results1 + results2
        discussions = []
        seen_urls = set()

        for result in all_results:
            url = result.get('url', '')
            title = result.get('title', '')
            description = result.get('description', '')

            content = (title + ' ' + description).lower()
            relevant_keywords = ['arxiv', 'paper', 'research', 'ai', 'ml', 'agent', 'memory']

            if not any(kw in content for kw in relevant_keywords):
                continue

            spam_keywords = ['scam', 'call', 'debt', 'lawsuit', 'phone', 'bank']
            if any(kw in content for kw in spam_keywords):
                continue

            if url and url not in seen_urls:
                seen_urls.add(url)

                source = "unknown"
                if 'twitter.com' in url or 'x.com' in url:
                    source = "Twitter"
                elif 'reddit.com' in url:
                    source = "Reddit"
                elif 'news.ycombinator.com' in url:
                    source = "Hacker News"

                discussions.append({
                    'source': source,
                    'title': title,
                    'url': url,
                    'description': description,
                    'age': result.get('age', ''),
                    'relevance': 'high' if arxiv_id in content else 'medium'
                })

        discussions.sort(key=lambda x: 0 if x['relevance'] == 'high' else 1)
        return discussions

    def _extract_arxiv_id(self, url: str) -> Optional[str]:
        """从 URL 中提取 arXiv ID"""
        patterns = [
            r'arxiv\.org/abs/(\d{4}\.\d{4,5})',
            r'arxiv\.org/pdf/(\d{4}\.\d{4,5})',
            r'arxiv\.org/abs/([a-z\-]+/\d{7})'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def get_popular_papers(self, keywords: List[str], count: int = 20) -> List[Dict]:
        """获取热门论文"""
        all_papers = []
        seen_ids = set()

        for keyword in keywords:
            papers = self.search_arxiv_papers(keyword, days=7)

            for paper in papers:
                arxiv_id = paper['arxiv_id']
                if arxiv_id not in seen_ids:
                    seen_ids.add(arxiv_id)
                    paper['search_keyword'] = keyword
                    all_papers.append(paper)

        all_papers.sort(key=lambda x: x.get('age', ''), reverse=False)
        return all_papers[:count]

    def get_paper_metadata_from_brave(self, arxiv_id: str) -> Dict:
        """从 Brave 搜索获取论文元数据"""
        query = f'"{arxiv_id}" site:arxiv.org'
        results = self.search_papers(query, count=3, freshness="py")

        if results:
            result = results[0]
            return {
                'title': result.get('title', ''),
                'description': result.get('description', ''),
                'url': result.get('url', ''),
                'arxiv_id': arxiv_id,
                'age': result.get('age', '')
            }

        return {'arxiv_id': arxiv_id}
