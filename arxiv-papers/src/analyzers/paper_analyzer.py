"""
论文分析和筛选模块
使用 Claude API 进行深度分析
支持基于知识库的分析和知识库更新建议
"""
import anthropic
from typing import List, Dict, Optional
import json
import re

from ..utils import get_logger

logger = get_logger('analyzers.paper')


class PaperAnalyzer:
    """使用 Claude 分析论文价值，支持知识库参考"""

    def __init__(self, api_key: str, base_url: str = None, knowledge_base_context: str = None):
        """
        初始化分析器

        Args:
            api_key: API Key
            base_url: 自定义 API endpoint (例如 LiteLLM)
            knowledge_base_context: 知识库上下文内容（用于增强分析）
        """
        if base_url:
            self.client = anthropic.Anthropic(
                api_key=api_key,
                base_url=base_url
            )
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
        
        self.knowledge_base_context = knowledge_base_context

    def set_knowledge_base_context(self, context: str):
        """设置知识库上下文"""
        self.knowledge_base_context = context

    def analyze_paper(self, paper: Dict) -> Dict:
        """
        深度分析单篇论文

        Args:
            paper: 论文基本信息（包含 title, abstract 等）

        Returns:
            分析结果，包含 contributions, key_results, tags, quality_score, kb_suggestions
        """
        # 构建知识库参考上下文
        kb_context = ""
        if self.knowledge_base_context:
            kb_context = f"""
---
**参考知识库** (Agent Memory 领域框架):
{self.knowledge_base_context[:2500]}
---

"""

        prompt = f"""你是一位专注于 Agent Memory / Agentic Memory 领域的研究专家。

{kb_context}请分析以下论文，首先判断该论文是否与 Agent Memory 领域相关，然后评估其在 Agent Memory 领域的价值：

**论文标题**: {paper['title']}

**作者**: {paper['authors']}

**摘要**: {paper['abstract']}

**arXiv ID**: {paper['arxiv_id']}

请从以下维度进行分析：

1. **领域相关度** (relevance): 0.0-1.0，判断该论文与 Agent Memory 领域的相关程度：
   - 1.0: 核心研究 Agent Memory（记忆机制、存储、检索、遗忘、长上下文记忆等）
   - 0.8-0.9: 直接相关（如对话历史管理等）
   - 0.5-0.7: 间接相关（领域RAG、通用 Agent 研究但涉及记忆组件）
   - 0.3-0.4: 轻微相关（LLM 研究但非记忆专题）
   - 0.0-0.2: 不相关

2. **核心贡献** (contributions): 列出2-4个主要贡献点（简洁，每条不超过20字）

3. **关键结果** (key_results): 列出1-3个关键实验结果或技术突破

4. **标签** (tags): 生成3-5个专业标签，参考知识库分类：
   - Memory Forms: Token-level Memory, Parametric Memory, Latent Memory, External Memory, Internal Memory
   - Memory Functions: Factual Memory, Episodic Memory, Working Memory, Sensory Memory, Semantic Memory, Procedural Memory
   - Memory Dynamics: Memory Formation, Memory Retrieval, Memory Evolution, Compression, Forgetting
   - Techniques: RAG, Fine-tuning, Self-Organizing Memory, RL-enabled Memory, Knowledge Graph, Prompt-based

5. **质量评分** (quality_score): 0-100分，综合考虑创新程度、技术深度、实用价值

6. **推荐理由** (recommendation): 一句话说明为什么值得推荐（不超过30字）

7. **知识库更新建议** (kb_suggestions): 仔细阅读知识库内容，判断论文贡献是否属于已有范畴。
   
   **核心原则：如果论文的方法/概念可以归入知识库已有的分类或章节，就不需要添加新条目！**
   
   例如：
   - 知识库已有"强化学习 (Reinforcement Learning)"分类 → 新的 RL 记忆方法不需要新建条目
   - 知识库已有"游戏与仿真"应用场景 → 新的游戏 Agent 系统不需要新建条目
   - 知识库已有"压缩与总结"操作机制 → 新的压缩方法不需要新建条目
   
   **只有以下情况才生成建议**：
   1. 提出了知识库中完全没有的新维度/新范畴（如首次出现"神经符号记忆融合"这一研究方向）
   2. 对现有章节有重要补充（使用 update_existing，在现有条目后补充新的子方法）
   
   **格式要求**：
   - content 可以使用系统名（如 MemGPT、Voyager），但不要用完整论文标题
   - 格式：简洁概念名 + 冒号 + 一句话描述，不超过40字
   
   类型说明：
   - **new_direction**：知识库完全没有覆盖的新研究范式
   - **new_concept**：知识库完全没有覆盖的新核心概念
   - **update_existing**：对已有章节的补充（需指定 section，如"三、 记忆学习策略"）
   
   **90%以上的论文不应该生成建议**，因为大多数工作是对已有范畴的具体实现。

请以 JSON 格式返回结果：
```json
{{
  "relevance": 0.85,
  "contributions": ["贡献1", "贡献2", "贡献3"],
  "key_results": ["结果1", "结果2"],
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "quality_score": 85,
  "recommendation": "一句话推荐理由",
  "kb_suggestions": [
    {{
      "type": "new_concept",
      "section": "三、 记忆学习策略",
      "content": "门控选择性记忆：通过可学习门控机制动态决策记忆写入时机",
      "reason": "为什么这是重要的新方向"
    }}
  ]
}}
```

注意：
- 只返回 JSON，不要其他解释文字
- kb_suggestions 对于大多数论文应该是空数组 []
- content 必须简洁，格式为"概念名称：一句话描述"，不超过40字
- 只有真正有宏观贡献的论文才生成建议"""

        try:
            message = self.client.messages.create(
                model="anthropic/claude-sonnet-4.5",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(1))
            else:
                analysis = json.loads(response_text)

            return analysis

        except Exception as e:
            logger.error(f"分析论文 {paper['arxiv_id']} 失败: {e}")
            return {
                'relevance': 0.5,
                'contributions': ['待分析'],
                'key_results': ['待分析'],
                'tags': ['待分类'],
                'quality_score': 50,
                'recommendation': '需要进一步分析',
                'kb_suggestions': []
            }

    def rank_papers(self, papers: List[Dict]) -> List[Dict]:
        """对论文进行排序"""
        return sorted(papers, key=lambda x: x.get('quality_score', 0), reverse=True)

    def extract_references(self, paper_abstract: str, paper_intro: str = "") -> List[str]:
        """从摘要和引言中提取可能的重要前置工作"""
        text = paper_abstract + " " + paper_intro

        prompt = f"""从以下论文文本中，识别被引用的重要前置工作或相关研究的关键词。

文本：
{text[:2000]}

请列出3-5个可能的重要前置工作关键词或论文标题片段（用于后续搜索）。

返回 JSON 格式：
```json
{{
  "references": ["keyword1", "keyword2", "keyword3"]
}}
```"""

        try:
            message = self.client.messages.create(
                model="anthropic/claude-sonnet-4.5",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                return result.get('references', [])
            return []

        except Exception as e:
            logger.error(f"提取参考文献失败: {e}")
            return []

    def generate_trend_summary(self, papers: List[Dict]) -> str:
        """生成本周/本日研究热点趋势总结"""
        if not papers:
            return "暂无新论文"

        all_tags = []
        for paper in papers:
            all_tags.extend(paper.get('tags', []))

        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        trend_text = "、".join([f"{tag}({count}篇)" for tag, count in top_tags])
        
        return f"研究热点集中在 {trend_text}"
