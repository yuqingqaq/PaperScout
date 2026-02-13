#!/usr/bin/env python3
"""
测试飞书 Webhook 推送
"""
import os
import sys

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import load_config
from src.notifiers import FeishuNotifier


def test_simple_message():
    """测试简单文本消息"""
    print("=" * 60)
    print("测试 1: 简单文本消息")
    print("=" * 60)

    # 加载配置
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config.json'
    )
    
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

    webhook_url = config.get('feishu', {}).get('webhook_url')

    if not webhook_url or webhook_url == "YOUR_FEISHU_WEBHOOK_URL":
        print("❌ 错误: 请先配置飞书 Webhook URL")
        print("\n在 config.json 中设置:")
        print('{')
        print('  "feishu": {')
        print('    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK"')
        print('  }')
        print('}')
        return False

    print(f"✓ Webhook URL: {webhook_url[:50]}...")

    # 发送测试消息
    notifier = FeishuNotifier(webhook_url)

    message = "🧪 这是一条测试消息\n\n来自 ArXiv Papers Agent 系统测试"

    print("\n发送消息...")
    success = notifier.send_message(message)

    if success:
        print("✅ 消息发送成功！")
        return True
    else:
        print("❌ 消息发送失败")
        return False


def test_daily_recommendation():
    """测试每日推荐格式"""
    print("\n" + "=" * 60)
    print("测试 2: 每日推荐消息")
    print("=" * 60)

    # 加载配置
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config.json'
    )
    
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

    webhook_url = config.get('feishu', {}).get('webhook_url')

    if not webhook_url or webhook_url == "YOUR_FEISHU_WEBHOOK_URL":
        print("❌ 错误: 请先配置飞书 Webhook URL")
        return False

    notifier = FeishuNotifier(webhook_url)

    # 模拟论文数据
    test_papers = [
        {
            'title': 'Memory in the Age of AI Agents: A Survey',
            'tags': ['Survey', 'Agent Memory', 'Taxonomy'],
            'recommendation': '首个系统性综述 Agent Memory 领域的论文',
            'quality_score': 95,
            'arxiv_url': 'https://arxiv.org/abs/2512.13564'
        },
        {
            'title': 'InternAgent-1.5: Long-Horizon Scientific Discovery',
            'tags': ['Long-horizon Memory', 'Multi-agent'],
            'recommendation': '长时程记忆支持科学发现的完整Agent系统',
            'quality_score': 82,
            'arxiv_url': 'https://arxiv.org/abs/2602.08990'
        },
        {
            'title': 'iGRPO: Self-Feedback-Driven LLM Reasoning',
            'tags': ['Working Memory', 'RL-enabled Memory'],
            'recommendation': '自我反馈迭代机制为Agent工作记忆优化提供新思路',
            'quality_score': 72,
            'arxiv_url': 'https://arxiv.org/abs/2602.09000'
        }
    ]

    print("\n发送每日推荐...")
    success = notifier.send_daily_recommendation(
        papers=test_papers,
        total_papers=8,
        trend_summary="研究热点集中在 Episodic Memory(2篇)、Long-horizon Memory(1篇)"
    )

    if success:
        print("✅ 每日推荐发送成功！")
        return True
    else:
        print("❌ 每日推荐发送失败")
        return False


def test_card_message():
    """测试卡片消息"""
    print("\n" + "=" * 60)
    print("测试 3: 卡片消息（富文本）")
    print("=" * 60)

    # 加载配置
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config.json'
    )
    
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

    webhook_url = config.get('feishu', {}).get('webhook_url')

    if not webhook_url or webhook_url == "YOUR_FEISHU_WEBHOOK_URL":
        print("❌ 错误: 请先配置飞书 Webhook URL")
        return False

    notifier = FeishuNotifier(webhook_url)

    # 模拟论文数据
    test_papers = [
        {
            'title': 'Memory in the Age of AI Agents',
            'tags': ['Survey', 'Agent Memory'],
            'recommendation': '首个系统性综述',
            'quality_score': 95,
            'arxiv_url': 'https://arxiv.org/abs/2512.13564'
        },
        {
            'title': 'InternAgent-1.5',
            'tags': ['Long-horizon Memory'],
            'recommendation': '长时程记忆支持',
            'quality_score': 82,
            'arxiv_url': 'https://arxiv.org/abs/2602.08990'
        }
    ]

    print("\n发送卡片消息...")
    success = notifier.send_card(
        papers=test_papers,
        total_papers=8,
        trend_summary="研究热点集中在长时程记忆"
    )

    if success:
        print("✅ 卡片消息发送成功！")
        return True
    else:
        print("❌ 卡片消息发送失败")
        return False


def main():
    """主函数"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                                                          ║")
    print("║          飞书 Webhook 推送测试                            ║")
    print("║                                                          ║")
    print("╚══════════════════════════════════════════════════════════╝")

    results = []

    # 测试 1: 简单消息
    try:
        result1 = test_simple_message()
        results.append(("简单文本消息", result1))
    except Exception as e:
        print(f"❌ 测试 1 异常: {e}")
        results.append(("简单文本消息", False))

    # 测试 2: 每日推荐
    try:
        result2 = test_daily_recommendation()
        results.append(("每日推荐消息", result2))
    except Exception as e:
        print(f"❌ 测试 2 异常: {e}")
        results.append(("每日推荐消息", False))

    # 测试 3: 卡片消息
    try:
        result3 = test_card_message()
        results.append(("卡片消息", result3))
    except Exception as e:
        print(f"❌ 测试 3 异常: {e}")
        results.append(("卡片消息", False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试汇总")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s} {status}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！飞书 Webhook 配置正确。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查配置。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
