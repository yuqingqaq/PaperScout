"""
飞书消息推送模块（Webhook 方式）
"""
import requests
from datetime import datetime
from typing import List, Dict

from ..utils import get_logger

logger = get_logger('notifiers.feishu')


class FeishuNotifier:
    """飞书消息推送（使用 Webhook）"""

    def __init__(self, webhook_url: str):
        """
        初始化飞书通知器

        Args:
            webhook_url: 飞书机器人 Webhook URL
        """
        self.webhook_url = webhook_url

    def send_message(self, content: str, msg_type: str = "text") -> bool:
        """
        发送消息到飞书群组

        Args:
            content: 消息内容
            msg_type: 消息类型（text, post, interactive）

        Returns:
            是否发送成功
        """
        try:
            if msg_type == "text":
                payload = {
                    "msg_type": "text",
                    "content": {
                        "text": content
                    }
                }
            elif msg_type == "post":
                payload = content
            else:
                payload = {
                    "msg_type": msg_type,
                    "content": content
                }

            response = requests.post(
                self.webhook_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=10
            )

            result = response.json()

            if result.get('code') == 0 or result.get('StatusCode') == 0:
                logger.info("✓ 飞书消息发送成功")
                return True
            else:
                logger.error(f"✗ 飞书消息发送失败: {result}")
                return False

        except Exception as e:
            logger.error(f"✗ 发送飞书消息异常: {e}")
            return False

    def send_markdown(self, title: str, content: str) -> bool:
        """发送 Markdown 格式消息"""
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": self._parse_markdown_to_post(content)
                    }
                }
            }
        }

        try:
            response = requests.post(
                self.webhook_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=10
            )

            result = response.json()

            if result.get('code') == 0 or result.get('StatusCode') == 0:
                logger.info("✓ 飞书 Markdown 消息发送成功")
                return True
            else:
                logger.error(f"✗ 发送 Markdown 消息失败: {result}")
                return False

        except Exception as e:
            logger.error(f"✗ 发送 Markdown 消息异常: {e}")
            return False

    def _parse_markdown_to_post(self, content: str) -> List[List[Dict]]:
        """将简单的 Markdown 转换为飞书 post 格式"""
        lines = content.strip().split('\n')
        post_content = []

        for line in lines:
            if line.strip():
                post_content.append([{"tag": "text", "text": line}])

        return post_content

    def format_daily_recommendation(
        self,
        papers: List[Dict],
        total_papers: int,
        trend_summary: str = ""
    ) -> str:
        """格式化每日推荐消息"""
        today = datetime.now().strftime('%Y-%m-%d')
        count = len(papers)

        message = f"📚 {today} Agent Memory 论文推荐\n\n"
        message += f"今日新增 {count}篇 高价值论文：\n\n"

        for i, paper in enumerate(papers, 1):
            title = paper.get('title', '')
            short_title = title.split(':')[0] if ':' in title else title[:60]

            tags = paper.get('tags', [])
            main_tag = tags[0] if tags else '未分类'

            recommendation = paper.get('recommendation', '高质量论文')
            quality_score = paper.get('quality_score', 0)

            message += f"{i}. {short_title}\n"
            message += f"   标签: {main_tag} | 评分: {quality_score}\n"
            message += f"   {recommendation}\n"
            message += f"   🔗 {paper.get('arxiv_url', '')}\n\n"

        message += "─────────────────────\n"

        if trend_summary:
            message += f"📊 趋势: {trend_summary}\n"

        message += f"📂 论文库: http://localhost:8889/papers.html ({total_papers}篇)\n"

        return message

    def send_daily_recommendation(
        self,
        papers: List[Dict],
        total_papers: int,
        trend_summary: str = ""
    ) -> bool:
        """发送每日推荐"""
        message = self.format_daily_recommendation(papers, total_papers, trend_summary)
        return self.send_message(message)

    def send_card(self, papers: List[Dict], total_papers: int, trend_summary: str = "") -> bool:
        """
        发送精美卡片消息
        
        Args:
            papers: 推荐论文列表
            total_papers: 论文库总数
            trend_summary: 趋势总结
            
        Returns:
            是否发送成功
        """
        today = datetime.now().strftime('%Y-%m-%d')
        count = len(papers)

        elements = []
        
        # 摘要信息
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"🎯 今日新增 **{count}** 篇高价值论文，已入库 **{total_papers}** 篇"
            }
        })
        elements.append({"tag": "hr"})

        # 论文列表
        for i, paper in enumerate(papers, 1):
            title = paper.get('title', '')
            # 截取标题（冒号前或前60字符）
            short_title = title.split(':')[0] if ':' in title else title[:60]
            if len(short_title) < len(title):
                short_title += "..."
            
            tags = paper.get('tags', [])
            tags_str = " | ".join(tags[:3]) if tags else "未分类"
            
            recommendation = paper.get('recommendation', '高质量论文')
            
            arxiv_url = paper.get('arxiv_url', '')
            pdf_url = paper.get('pdf_url', arxiv_url.replace('/abs/', '/pdf/'))
            
            # 构建论文卡片内容（不显示评分）
            content = f"**{i}. {short_title}**\n"
            content += f"🏷️ {tags_str}\n"
            content += f"💡 {recommendation}"
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": content
                }
            })
            
            # 添加按钮
            elements.append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "📄 查看论文"
                        },
                        "type": "primary",
                        "url": arxiv_url
                    },
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "📑 PDF"
                        },
                        "type": "default",
                        "url": pdf_url
                    }
                ]
            })
            
            # 论文之间的分隔（最后一篇不加）
            if i < count:
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "plain_text",
                        "content": ""
                    }
                })

        elements.append({"tag": "hr"})

        # 趋势总结
        if trend_summary:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📊 **趋势分析**: {trend_summary}"
                }
            })

        # 底部说明
        elements.append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": f"🤖 由 Claude AI 分析评分 | Brave Search 社区验证"
                }
            ]
        })

        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "template": "blue",
                    "title": {
                        "tag": "plain_text",
                        "content": f"📚 {today} Agent Memory 论文推荐"
                    }
                },
                "elements": elements
            }
        }

        try:
            response = requests.post(
                self.webhook_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=10
            )

            result = response.json()

            if result.get('code') == 0 or result.get('StatusCode') == 0:
                logger.info("✓ 飞书卡片消息发送成功")
                return True
            else:
                logger.error(f"✗ 发送卡片消息失败: {result}")
                return False

        except Exception as e:
            logger.error(f"✗ 发送卡片消息异常: {e}")
            return False
