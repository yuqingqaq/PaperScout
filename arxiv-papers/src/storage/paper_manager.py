"""
论文管理模块
负责 papers.json 的读写和维护
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from ..utils import get_logger

logger = get_logger('storage.manager')


class PaperManager:
    """管理 papers.json 数据"""

    def __init__(self, json_path: str):
        self.json_path = json_path
        self._ensure_dir_exists()
        self.ensure_file_exists()

    def _ensure_dir_exists(self):
        """确保目录存在"""
        dir_path = os.path.dirname(self.json_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    def ensure_file_exists(self):
        """确保 papers.json 文件存在"""
        if not os.path.exists(self.json_path):
            initial_data = {
                "metadata": {
                    "last_updated": datetime.now().strftime('%Y-%m-%d'),
                    "total_papers": 0
                },
                "papers": []
            }
            self.save_data(initial_data)

    def load_data(self) -> Dict:
        """加载 papers.json 数据"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载 papers.json 失败: {e}")
            return {
                "metadata": {
                    "last_updated": datetime.now().strftime('%Y-%m-%d'),
                    "total_papers": 0
                },
                "papers": []
            }

    def save_data(self, data: Dict):
        """保存数据到 papers.json"""
        try:
            data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            data['metadata']['total_papers'] = len(data['papers'])

            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存 papers.json 失败: {e}")

    def add_paper(self, paper: Dict) -> bool:
        """
        添加论文到数据库

        Args:
            paper: 论文数据（必须包含 arxiv_id）

        Returns:
            是否成功添加
        """
        data = self.load_data()

        arxiv_id = paper.get('arxiv_id')
        if any(p.get('arxiv_id') == arxiv_id for p in data['papers']):
            logger.debug(f"论文 {arxiv_id} 已存在，跳过")
            return False

        paper['recommend_date'] = datetime.now().strftime('%Y-%m-%d')
        data['papers'].insert(0, paper)

        self.save_data(data)
        logger.info(f"已添加: {paper.get('title', 'Unknown')[:50]}...")
        return True

    def add_papers(self, papers: List[Dict]) -> int:
        """批量添加论文"""
        count = 0
        for paper in papers:
            if self.add_paper(paper):
                count += 1
        return count

    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """根据 arXiv ID 获取论文"""
        data = self.load_data()
        for paper in data['papers']:
            if paper.get('arxiv_id') == arxiv_id:
                return paper
        return None

    def get_recent_papers(self, days: int = 7) -> List[Dict]:
        """获取最近几天推荐的论文"""
        data = self.load_data()
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        recent_papers = [
            paper for paper in data['papers']
            if paper.get('recommend_date', '') >= cutoff_date
        ]

        return recent_papers

    def get_all_papers(self) -> List[Dict]:
        """获取所有论文"""
        data = self.load_data()
        return data['papers']

    def get_all_arxiv_ids(self) -> List[str]:
        """获取所有已存在的 arXiv ID 列表"""
        data = self.load_data()
        return [paper.get('arxiv_id') for paper in data['papers'] if paper.get('arxiv_id')]

    def get_total_count(self) -> int:
        """获取论文总数"""
        data = self.load_data()
        return len(data['papers'])

    def update_paper(self, arxiv_id: str, updates: Dict) -> bool:
        """更新论文信息"""
        data = self.load_data()

        for paper in data['papers']:
            if paper.get('arxiv_id') == arxiv_id:
                paper.update(updates)
                self.save_data(data)
                return True

        return False

    def delete_paper(self, arxiv_id: str) -> bool:
        """删除论文"""
        data = self.load_data()
        initial_count = len(data['papers'])

        data['papers'] = [
            paper for paper in data['papers']
            if paper.get('arxiv_id') != arxiv_id
        ]

        if len(data['papers']) < initial_count:
            self.save_data(data)
            return True

        return False
    # ========== 已分析论文跟踪 ==========
    
    def _get_analyzed_path(self) -> str:
        """获取 analyzed_papers.json 路径"""
        dir_path = os.path.dirname(self.json_path)
        return os.path.join(dir_path, 'analyzed_papers.json')
    
    def load_analyzed_ids(self) -> set:
        """加载已分析过的论文 ID 集合"""
        path = self._get_analyzed_path()
        if not os.path.exists(path):
            return set()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('analyzed_ids', []))
        except Exception:
            return set()
    
    def add_analyzed_ids(self, arxiv_ids: List[str]):
        """记录已分析的论文 ID"""
        path = self._get_analyzed_path()
        existing = self.load_analyzed_ids()
        existing.update(arxiv_ids)
        
        data = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_analyzed': len(existing),
            'analyzed_ids': list(existing)
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"已记录 {len(arxiv_ids)} 篇分析过的论文，总计 {len(existing)} 篇")