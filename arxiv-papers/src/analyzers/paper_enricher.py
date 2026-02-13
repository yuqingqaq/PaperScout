"""
论文增强器
使用 Brave Search 获取社区信号：讨论、GitHub stars、推文等
使用 Claude AI 验证社区讨论相关性
"""
from typing import Dict, List, Optional
import re
import time
import math
import json
import anthropic

from ..fetchers import BraveSearcher
from ..utils import get_logger

logger = get_logger('analyzers.enricher')


class PaperEnricher:
    """使用社区信号增强论文元数据"""

    def __init__(self, brave_api_key: str, litellm_config: dict = None):
        """
        初始化论文增强器

        Args:
            brave_api_key: Brave Search API Key
            litellm_config: LiteLLM 配置（用于相关性验证）
        """
        self.searcher = BraveSearcher(brave_api_key)
        
        # 初始化 AI 客户端用于相关性验证
        self.ai_client = None
        if litellm_config:
            try:
                self.ai_client = anthropic.Anthropic(
                    api_key=litellm_config.get('api_key'),
                    base_url=litellm_config.get('base_url')
                )
                logger.info("✓ 社区讨论相关性验证已启用（Claude AI）")
            except Exception as e:
                logger.warning(f"⚠️ AI 相关性验证初始化失败: {e}")

    def enrich_paper(self, paper: Dict) -> Dict:
        """
        增强单篇论文的元数据

        Args:
            paper: 论文基本信息

        Returns:
            增强后的论文信息（包含社区信号）
        """
        arxiv_id = paper.get('arxiv_id')
        title = paper.get('title', '')

        logger.info(f"🔍 增强论文: {title[:60]}...")

        # 收集社区信号
        community_signals = {
            'discussions': [],
            'github_repos': [],
            'tweets': [],
            'total_discussion_count': 0,
            'github_stars': 0,
            'tweet_count': 0,
            'hacker_news_mentions': 0,
            'reddit_mentions': 0,
            'social_score': 0
        }

        # 1. 查找 GitHub 仓库
        github_repos = self._find_github_repos(arxiv_id, title)
        if github_repos:
            community_signals['github_repos'] = github_repos
            community_signals['github_stars'] = sum(r.get('stars', 0) for r in github_repos)
            logger.info(f"  ✓ 找到 {len(github_repos)} 个 GitHub 仓库，总 stars: {community_signals['github_stars']}")

        # 2. 查找社区讨论（带 AI 相关性验证）
        discussions = self._find_discussions(arxiv_id, title)
        
        # 使用 AI 验证相关性（如果启用）
        if discussions and self.ai_client:
            discussions = self._verify_discussions_relevance(paper, discussions)
        
        if discussions:
            community_signals['discussions'] = discussions
            community_signals['total_discussion_count'] = len(discussions)

            for disc in discussions:
                source = disc.get('source', '').lower()
                if 'twitter' in source:
                    community_signals['tweet_count'] += 1
                elif 'reddit' in source:
                    community_signals['reddit_mentions'] += 1
                elif 'hacker news' in source:
                    community_signals['hacker_news_mentions'] += 1

            logger.info(f"  ✓ 找到 {len(discussions)} 条相关讨论 (Twitter: {community_signals['tweet_count']}, "
                       f"Reddit: {community_signals['reddit_mentions']}, HN: {community_signals['hacker_news_mentions']})")

        # 3. 计算社交分数
        social_score = self._calculate_social_score(community_signals)
        community_signals['social_score'] = social_score
        logger.info(f"  📊 社交分数: {social_score}/100")

        # 4. 添加到论文信息
        paper['community_signals'] = community_signals

        # 5. 调整质量评分（如果已有）
        if 'quality_score' in paper:
            original_score = paper['quality_score']
            adjusted_score = int(original_score * 0.8 + social_score * 0.2)
            paper['quality_score_adjusted'] = adjusted_score
            paper['quality_score_original'] = original_score

            if adjusted_score != original_score:
                logger.info(f"  ⚡ 质量评分调整: {original_score} → {adjusted_score}")

        return paper

    def _find_github_repos(self, arxiv_id: str, title: str) -> List[Dict]:
        """查找相关的 GitHub 仓库"""
        repos = []

        query1 = f'"{arxiv_id}" site:github.com'
        results1 = self.searcher.search_papers(query1, count=5, freshness="py")

        title_keywords = ' '.join(title.split()[:5])
        query2 = f'"{title_keywords}" arxiv site:github.com'
        results2 = self.searcher.search_papers(query2, count=5, freshness="py")

        all_results = results1 + results2
        seen_urls = set()

        for result in all_results:
            url = result.get('url', '')

            if 'github.com' not in url or url in seen_urls:
                continue

            if any(x in url for x in ['/issues/', '/pull/', '/discussions/', '/wiki/']):
                continue

            seen_urls.add(url)

            repo_info = self._extract_github_info(result)
            if repo_info:
                repos.append(repo_info)

        return repos

    def _extract_github_info(self, result: Dict) -> Optional[Dict]:
        """从搜索结果中提取 GitHub 仓库信息"""
        url = result.get('url', '')
        title = result.get('title', '')
        description = result.get('description', '')

        match = re.search(r'github\.com/([^/]+/[^/]+)', url)
        if not match:
            return None

        repo_name = match.group(1)

        stars = 0
        star_match = re.search(r'(\d+(?:,\d+)?)\s*(?:stars?|⭐)', description, re.IGNORECASE)
        if star_match:
            stars_str = star_match.group(1).replace(',', '')
            stars = int(stars_str)

        return {
            'repo_name': repo_name,
            'url': url,
            'title': title,
            'description': description,
            'stars': stars,
            'age': result.get('age', '')
        }

    def _find_discussions(self, arxiv_id: str, title: str) -> List[Dict]:
        """查找社区讨论"""
        discussions = []

        query1 = f'"{arxiv_id}" (site:twitter.com OR site:reddit.com OR site:news.ycombinator.com)'
        results1 = self.searcher.search_papers(query1, count=10, freshness="pm")

        title_keywords = ' '.join(title.split()[:6])
        query2 = f'"{title_keywords}" arxiv (site:twitter.com OR site:reddit.com OR site:news.ycombinator.com)'
        results2 = self.searcher.search_papers(query2, count=10, freshness="pm")

        all_results = results1 + results2
        seen_urls = set()

        for result in all_results:
            url = result.get('url', '')
            title_text = result.get('title', '')
            description = result.get('description', '')

            if url in seen_urls:
                continue

            content = (title_text + ' ' + description).lower()

            relevant_keywords = ['arxiv', 'paper', 'research', 'ai', 'ml', 'llm', 'agent', 'memory']
            if not any(kw in content for kw in relevant_keywords):
                continue

            spam_keywords = ['scam', 'spam', 'debt', 'lawsuit', 'bank', 'call center']
            if any(kw in content for kw in spam_keywords):
                continue

            seen_urls.add(url)

            source = 'Unknown'
            if 'twitter.com' in url or 'x.com' in url:
                source = 'Twitter'
            elif 'reddit.com' in url:
                source = 'Reddit'
            elif 'news.ycombinator.com' in url:
                source = 'Hacker News'

            relevance = 'high' if arxiv_id in content else 'medium'
            if arxiv_id in url:
                relevance = 'very_high'

            discussions.append({
                'source': source,
                'url': url,
                'title': title_text,
                'description': description,
                'age': result.get('age', ''),
                'relevance': relevance
            })

        relevance_order = {'very_high': 0, 'high': 1, 'medium': 2}
        discussions.sort(key=lambda x: relevance_order.get(x['relevance'], 3))

        return discussions

    def _verify_discussions_relevance(self, paper: Dict, discussions: List[Dict]) -> List[Dict]:
        """
        使用 Claude AI 验证社区讨论与论文的相关性
        
        Args:
            paper: 论文信息
            discussions: 待验证的讨论列表
            
        Returns:
            过滤后的相关讨论列表
        """
        if not discussions or not self.ai_client:
            return discussions
        
        paper_title = paper.get('title', '')
        paper_abstract = paper.get('abstract', '')[:500]  # 限制长度
        arxiv_id = paper.get('arxiv_id', '')
        
        # 构建讨论摘要
        discussions_summary = []
        for i, d in enumerate(discussions[:10]):  # 最多验证10条
            discussions_summary.append({
                'index': i,
                'source': d.get('source', ''),
                'title': d.get('title', '')[:100],
                'description': d.get('description', '')[:200]
            })
        
        prompt = f"""你是一个学术论文相关性判断专家。请判断以下社区讨论是否与指定论文相关。

**论文信息**:
- 标题: {paper_title}
- arXiv ID: {arxiv_id}
- 摘要: {paper_abstract}

**待验证的社区讨论**:
{json.dumps(discussions_summary, ensure_ascii=False, indent=2)}

请判断每条讨论是否真正与该论文相关。
- "relevant": true 表示讨论确实在讨论这篇论文或其内容
- "relevant": false 表示讨论与该论文无关（如：讨论其他产品、垃圾信息、不相关的技术话题）

返回 JSON 格式：
```json
{{
  "results": [
    {{"index": 0, "relevant": true, "reason": "简短理由"}},
    {{"index": 1, "relevant": false, "reason": "简短理由"}}
  ]
}}
```

只返回 JSON，不要其他解释。"""

        try:
            message = self.ai_client.messages.create(
                model="anthropic/claude-sonnet-4.5",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # 解析 JSON
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(response_text)
            
            # 过滤不相关的讨论
            relevant_indices = set()
            for item in result.get('results', []):
                if item.get('relevant', False):
                    relevant_indices.add(item['index'])
            
            filtered = []
            for i, d in enumerate(discussions):
                if i < 10:  # 只验证了前10条
                    if i in relevant_indices:
                        d['ai_verified'] = True
                        filtered.append(d)
                    else:
                        logger.debug(f"  ✗ 排除不相关讨论: {d.get('title', '')[:50]}")
                else:
                    # 未验证的保留
                    filtered.append(d)
            
            removed_count = len(discussions) - len(filtered)
            if removed_count > 0:
                logger.info(f"  🤖 AI 过滤: 排除 {removed_count} 条不相关讨论")
            
            return filtered
            
        except Exception as e:
            logger.warning(f"  ⚠️ AI 相关性验证失败: {e}")
            return discussions  # 失败时返回原列表

    def _calculate_social_score(self, signals: Dict) -> int:
        """计算社交分数（0-100）"""
        score = 0

        # GitHub stars (最多 40 分)
        stars = signals.get('github_stars', 0)
        if stars > 0:
            star_score = min(40, int(10 * math.log10(stars + 1)))
            score += star_score

        # 讨论数量 (最多 30 分)
        total_discussions = signals.get('total_discussion_count', 0)
        if total_discussions > 0:
            discussion_score = min(30, total_discussions * 3)
            score += discussion_score

        # 平台多样性 (最多 15 分)
        platforms = 0
        if signals.get('tweet_count', 0) > 0:
            platforms += 1
        if signals.get('reddit_mentions', 0) > 0:
            platforms += 1
        if signals.get('hacker_news_mentions', 0) > 0:
            platforms += 1

        score += platforms * 5

        # HN 加成 (最多 15 分)
        hn_mentions = signals.get('hacker_news_mentions', 0)
        if hn_mentions > 0:
            hn_score = min(15, hn_mentions * 8)
            score += hn_score

        return min(100, score)

    def batch_enrich_papers(self, papers: List[Dict], max_papers: int = 10) -> List[Dict]:
        """批量增强论文"""
        logger.info(f"📊 批量增强论文（最多 {max_papers} 篇）")

        enriched_papers = []

        for i, paper in enumerate(papers[:max_papers], 1):
            logger.info(f"[{i}/{min(len(papers), max_papers)}]")

            try:
                enriched = self.enrich_paper(paper)
                enriched_papers.append(enriched)

                if i < min(len(papers), max_papers):
                    time.sleep(2)

            except Exception as e:
                logger.error(f"  ✗ 增强失败: {e}")
                enriched_papers.append(paper)

        if len(papers) > max_papers:
            enriched_papers.extend(papers[max_papers:])
            logger.warning(f"剩余 {len(papers) - max_papers} 篇论文未增强（节省 API 配额）")

        return enriched_papers

    def get_enrichment_summary(self, papers: List[Dict]) -> Dict:
        """获取增强结果统计"""
        summary = {
            'total_papers': len(papers),
            'enriched_papers': 0,
            'total_github_repos': 0,
            'total_stars': 0,
            'total_discussions': 0,
            'papers_with_github': 0,
            'papers_with_discussions': 0,
            'avg_social_score': 0
        }

        social_scores = []

        for paper in papers:
            signals = paper.get('community_signals')
            if signals:
                summary['enriched_papers'] += 1

                repos = signals.get('github_repos', [])
                if repos:
                    summary['papers_with_github'] += 1
                    summary['total_github_repos'] += len(repos)
                    summary['total_stars'] += signals.get('github_stars', 0)

                discussions = signals.get('discussions', [])
                if discussions:
                    summary['papers_with_discussions'] += 1
                    summary['total_discussions'] += len(discussions)

                social_score = signals.get('social_score', 0)
                if social_score > 0:
                    social_scores.append(social_score)

        if social_scores:
            summary['avg_social_score'] = int(sum(social_scores) / len(social_scores))

        return summary
