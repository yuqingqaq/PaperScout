"""
知识库管理模块
负责 knowledge_base.md 的读取、解析和更新建议管理
"""
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional

from ..utils import get_logger

logger = get_logger('storage.knowledge_base')


class KnowledgeBaseManager:
    """管理 Agent Memory 领域知识库"""

    def __init__(self, kb_path: str, suggestions_path: str = None):
        """
        初始化知识库管理器

        Args:
            kb_path: knowledge_base.md 文件路径
            suggestions_path: 待确认的更新建议 JSON 文件路径
        """
        self.kb_path = kb_path
        self.suggestions_path = suggestions_path or os.path.join(
            os.path.dirname(kb_path),
            'kb_suggestions.json'
        )
        self._ensure_suggestions_file()

    def _ensure_suggestions_file(self):
        """确保建议文件存在"""
        if not os.path.exists(self.suggestions_path):
            self._save_suggestions({
                "metadata": {
                    "last_updated": datetime.now().strftime('%Y-%m-%d'),
                    "total_pending": 0
                },
                "suggestions": []
            })

    def load_knowledge_base(self) -> str:
        """
        加载知识库内容

        Returns:
            知识库的完整文本内容
        """
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"知识库文件不存在: {self.kb_path}")
            return ""
        except Exception as e:
            logger.error(f"加载知识库失败: {e}")
            return ""

    def parse_knowledge_base(self) -> Dict:
        """
        解析知识库为结构化数据

        Returns:
            解析后的知识库结构
        """
        content = self.load_knowledge_base()
        if not content:
            return {}

        sections = {}
        current_section = None
        current_subsection = None
        current_content = []

        for line in content.split('\n'):
            # 一级标题
            if line.startswith('# '):
                if current_section:
                    self._save_section_content(sections, current_section, current_subsection, current_content)
                sections['title'] = line[2:].strip()
                current_section = None
                current_subsection = None
                current_content = []
            # 二级标题
            elif line.startswith('## '):
                if current_section:
                    self._save_section_content(sections, current_section, current_subsection, current_content)
                current_section = line[3:].strip()
                current_subsection = None
                current_content = []
                if current_section not in sections:
                    sections[current_section] = {'content': [], 'subsections': {}}
            # 三级标题
            elif line.startswith('### '):
                if current_section and current_subsection:
                    self._save_section_content(sections, current_section, current_subsection, current_content)
                current_subsection = line[4:].strip()
                current_content = []
            else:
                current_content.append(line)

        # 保存最后一个部分
        if current_section:
            self._save_section_content(sections, current_section, current_subsection, current_content)

        return sections

    def _save_section_content(self, sections: Dict, section: str, subsection: Optional[str], content: List[str]):
        """保存章节内容"""
        clean_content = '\n'.join(content).strip()
        if not clean_content:
            return

        if section not in sections:
            sections[section] = {'content': [], 'subsections': {}}

        if subsection:
            sections[section]['subsections'][subsection] = clean_content
        else:
            sections[section]['content'].append(clean_content)

    def get_context_for_analysis(self, max_chars: int = 5000) -> str:
        """
        获取用于论文分析的知识库上下文

        Args:
            max_chars: 最大字符数，默认 5000（知识库不长，直接全喂）

        Returns:
            知识库上下文
        """
        content = self.load_knowledge_base()
        if not content:
            return ""

        # 知识库不长，直接返回全部内容
        if len(content) <= max_chars:
            return content

        # 如果超过限制，截断
        return content[:max_chars] + "\n\n[... 知识库内容已截断 ...]"

    def get_taxonomy(self) -> Dict:
        """
        获取知识库中的分类体系

        Returns:
            分类体系字典
        """
        content = self.load_knowledge_base()
        taxonomy = {
            'memory_substrate': [],
            'cognitive_mechanism': [],
            'memory_subject': [],
            'key_techniques': [],
            'benchmarks': []
        }

        # 提取存储介质
        substrate_match = re.search(r'\*\*存储介质.*?\*\*：(.*?)(?=\*\*认知机制|\Z)', content, re.DOTALL)
        if substrate_match:
            items = re.findall(r'\*\*([^*]+)\*\*', substrate_match.group(1))
            taxonomy['memory_substrate'] = items

        # 提取认知机制
        cognitive_match = re.search(r'\*\*认知机制.*?\*\*：(.*?)(?=\*\*记忆主体|\Z)', content, re.DOTALL)
        if cognitive_match:
            items = re.findall(r'\*\*([^*]+)\*\*', cognitive_match.group(1))
            taxonomy['cognitive_mechanism'] = items

        # 提取关键技术
        technique_patterns = [
            r'RAG', r'Fine-tuning', r'Reinforcement Learning',
            r'Self-Organizing', r'Knowledge Graph', r'时间感知'
        ]
        for pattern in technique_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                taxonomy['key_techniques'].append(pattern)

        return taxonomy

    # =============== 建议管理功能 ===============

    def load_suggestions(self) -> Dict:
        """加载待确认的建议"""
        try:
            with open(self.suggestions_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载建议文件失败: {e}")
            return {"metadata": {}, "suggestions": []}

    def _save_suggestions(self, data: Dict):
        """保存建议到文件"""
        try:
            data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            data['metadata']['total_pending'] = len([
                s for s in data['suggestions']
                if s.get('status') == 'pending'
            ])

            with open(self.suggestions_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存建议文件失败: {e}")

    def add_suggestion(self, suggestion: Dict) -> bool:
        """
        添加新的知识库更新建议

        Args:
            suggestion: 建议内容，包含以下字段:
                - paper_arxiv_id: 来源论文 ID
                - paper_title: 来源论文标题
                - suggestion_type: 建议类型 (new_concept, new_paper, update_section, new_technique)
                - section: 目标章节
                - content: 建议内容
                - reason: 推荐理由

        Returns:
            是否成功添加
        """
        data = self.load_suggestions()

        # 检查是否已存在相同建议
        for existing in data['suggestions']:
            if (existing.get('paper_arxiv_id') == suggestion.get('paper_arxiv_id') and
                existing.get('content') == suggestion.get('content')):
                logger.debug(f"建议已存在，跳过: {suggestion.get('content', '')[:50]}")
                return False

        suggestion['id'] = len(data['suggestions']) + 1
        suggestion['status'] = 'pending'
        suggestion['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        data['suggestions'].append(suggestion)
        self._save_suggestions(data)

        logger.info(f"已添加知识库建议: {suggestion.get('suggestion_type')} - {suggestion.get('content', '')[:50]}")
        return True

    def add_suggestions_batch(self, suggestions: List[Dict]) -> int:
        """批量添加建议"""
        count = 0
        for suggestion in suggestions:
            if self.add_suggestion(suggestion):
                count += 1
        return count

    def get_pending_suggestions(self) -> List[Dict]:
        """获取所有待确认的建议"""
        data = self.load_suggestions()
        return [s for s in data['suggestions'] if s.get('status') == 'pending']

    def get_all_suggestions(self) -> List[Dict]:
        """获取所有建议"""
        data = self.load_suggestions()
        return data['suggestions']

    def approve_suggestion(self, suggestion_id: int) -> bool:
        """
        确认并应用建议到知识库

        Args:
            suggestion_id: 建议 ID

        Returns:
            是否成功
        """
        data = self.load_suggestions()

        for suggestion in data['suggestions']:
            if suggestion.get('id') == suggestion_id:
                if suggestion.get('status') != 'pending':
                    logger.warning(f"建议 {suggestion_id} 已处理过")
                    return False

                # 应用到知识库
                success = self._apply_suggestion(suggestion)

                if success:
                    suggestion['status'] = 'approved'
                    suggestion['approved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._save_suggestions(data)
                    logger.info(f"建议 {suggestion_id} 已应用到知识库")
                    return True
                else:
                    logger.error(f"应用建议 {suggestion_id} 失败")
                    return False

        logger.error(f"未找到建议 ID: {suggestion_id}")
        return False

    def reject_suggestion(self, suggestion_id: int, reason: str = "") -> bool:
        """
        拒绝建议

        Args:
            suggestion_id: 建议 ID
            reason: 拒绝理由

        Returns:
            是否成功
        """
        data = self.load_suggestions()

        for suggestion in data['suggestions']:
            if suggestion.get('id') == suggestion_id:
                suggestion['status'] = 'rejected'
                suggestion['rejected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                suggestion['reject_reason'] = reason

                self._save_suggestions(data)
                logger.info(f"建议 {suggestion_id} 已拒绝")
                return True

        return False

    def _find_section_end(self, content: str, start_pos: int) -> int:
        """
        找到章节末尾位置（在 --- 分隔符或下一个 ## 标题之前）
        
        Args:
            content: 完整内容
            start_pos: 章节标题后的起始位置
            
        Returns:
            插入位置
        """
        section_content = content[start_pos:]
        separator = re.search(r'\n---\s*\n', section_content)
        next_section = re.search(r'\n## ', section_content)
        
        if separator and (not next_section or separator.start() < next_section.start()):
            return start_pos + separator.start()
        elif next_section:
            return start_pos + next_section.start()
        else:
            return len(content)

    def _extract_section_keyword(self, section: str) -> str:
        """从 section 路径中提取最核心的匹配关键词
        
        例如：
        - "一、 核心综述框架 - 2. 三维统一分类法 - 记忆主体" -> "记忆主体"
        - "三、 记忆学习策略" -> "记忆学习策略"
        - "核心操作机制" -> "核心操作机制"
        """
        # 如果有 - 分隔的路径，取最后一个部分
        if ' - ' in section:
            section = section.split(' - ')[-1]
        
        # 去除序号（如 "一、"、"2."、"###" 等）
        section = re.sub(r'^[一二三四五六七八九十\d]+[、.．]\s*', '', section)
        section = re.sub(r'^#+\s*', '', section)
        
        # 去除括号内的英文说明
        section = re.sub(r'\s*\([^)]+\)', '', section)
        
        return section.strip()

    def _find_section_in_content(self, content: str, section: str) -> Optional[re.Match]:
        """在内容中查找章节，支持多种匹配策略"""
        keyword = self._extract_section_keyword(section)
        
        # 策略1: 精确匹配章节标题（## 或 ###）
        pattern = rf'(#{{2,}}\s+.*?{re.escape(keyword)}.*?\n)'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match
        
        # 策略2: 匹配加粗的子项（如 **记忆主体 (Memory Subject)**）
        pattern = rf'(\*\*{re.escape(keyword)}[^*]*\*\*[：:][^\n]*\n)'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match
        
        # 策略3: 如果 section 有多级路径，尝试匹配上一级
        if ' - ' in section:
            parent_section = ' - '.join(section.split(' - ')[:-1])
            return self._find_section_in_content(content, parent_section)
        
        return None

    def _apply_suggestion(self, suggestion: Dict) -> bool:
        """
        将建议应用到知识库文件

        Args:
            suggestion: 建议内容

        Returns:
            是否成功
        """
        try:
            content = self.load_knowledge_base()
            suggestion_type = suggestion.get('type') or suggestion.get('suggestion_type')
            section = suggestion.get('section', '')
            new_content = suggestion.get('content', '')
            paper_title = suggestion.get('paper_title', '')
            paper_id = suggestion.get('paper_arxiv_id', '')

            if suggestion_type == 'new_direction':
                # 在 "未来方向" 章节添加新研究方向
                pattern = r'(##\s+.*?未来方向.*?\n)'
                match = re.search(pattern, content)
                if match:
                    insert_pos = self._find_section_end(content, match.end())
                    entry = f"*   **{new_content}** ({paper_id})\n"
                    content = content[:insert_pos] + entry + content[insert_pos:]
                else:
                    content += f"\n*   **{new_content}**\n"

            elif suggestion_type == 'new_taxonomy':
                # 在分类法章节添加新分类维度
                pattern = r'(## .*?分类法.*?\n|### .*?三维统一分类法.*?\n)'
                match = re.search(pattern, content)
                if match:
                    insert_pos = self._find_section_end(content, match.end())
                    entry = f"*   **{new_content}**\n"
                    content = content[:insert_pos] + entry + content[insert_pos:]

            elif suggestion_type == 'new_concept':
                # 在指定章节或核心框架添加新概念
                if section:
                    match = self._find_section_in_content(content, section)
                else:
                    match = self._find_section_in_content(content, '核心框架')
                
                if match:
                    insert_pos = self._find_section_end(content, match.end())
                    entry = f"*   **{new_content}** ({paper_id})\n"
                    content = content[:insert_pos] + entry + content[insert_pos:]
                else:
                    # 如果找不到匹配的章节，添加到文件末尾
                    logger.warning(f"未找到章节 '{section}'，添加到末尾")
                    content += f"\n*   **{new_content}** ({paper_id})\n"

            elif suggestion_type == 'new_milestone':
                # 在 "研究趋势与前沿论文" 章节添加里程碑论文
                pattern = r'(## .*?研究趋势与前沿论文.*?\n)'
                match = re.search(pattern, content)
                if match:
                    insert_pos = match.end()
                    # 提取年份
                    year = paper_id[:2] if paper_id else '2026'
                    year = f"20{year}" if len(year) == 2 else year
                    entry = f"*   **{paper_title} ({year})**：{new_content}\n"
                    content = content[:insert_pos] + entry + content[insert_pos:]
                else:
                    content += f"\n*   **{paper_title}**：{new_content}\n"

            elif suggestion_type == 'update_existing':
                # 在指定章节附近添加更新说明，而不是覆盖原有内容
                if section:
                    match = self._find_section_in_content(content, section)
                    if match:
                        insert_pos = self._find_section_end(content, match.end())
                        entry = f"*   **[更新]** {new_content} ({paper_id})\n"
                        content = content[:insert_pos] + entry + content[insert_pos:]
                    else:
                        logger.warning(f"未找到章节 '{section}'，添加到末尾")
                        content += f"\n*   **[更新]** {new_content} ({paper_id})\n"
                else:
                    # 没有指定章节，添加到末尾
                    content += f"\n*   **[更新]** {new_content} ({paper_id})\n"

            # 保存更新后的知识库
            with open(self.kb_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"应用建议失败: {e}")
            return False

    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        content = self.load_knowledge_base()
        suggestions_data = self.load_suggestions()

        # 统计章节数
        sections = re.findall(r'^## ', content, re.MULTILINE)
        subsections = re.findall(r'^### ', content, re.MULTILINE)

        # 统计论文引用数
        papers = re.findall(r'\*\*([^*]+)\s*\(\d{4}\)\*\*', content)

        return {
            'total_sections': len(sections),
            'total_subsections': len(subsections),
            'total_referenced_papers': len(papers),
            'content_length': len(content),
            'pending_suggestions': len([s for s in suggestions_data['suggestions'] if s.get('status') == 'pending']),
            'approved_suggestions': len([s for s in suggestions_data['suggestions'] if s.get('status') == 'approved']),
            'rejected_suggestions': len([s for s in suggestions_data['suggestions'] if s.get('status') == 'rejected'])
        }

    def export_to_json(self, output_path: str) -> bool:
        """
        将知识库内容和建议导出为 JSON 文件供前端使用
        
        Args:
            output_path: 输出 JSON 文件路径
            
        Returns:
            是否成功
        """
        try:
            content = self.load_knowledge_base()
            suggestions_data = self.load_suggestions()
            stats = self.get_stats()
            
            export_data = {
                "metadata": {
                    "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "source_file": self.kb_path
                },
                "stats": stats,
                "content": content,
                "suggestions": suggestions_data.get('suggestions', [])
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"知识库已导出到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出知识库失败: {e}")
            return False
