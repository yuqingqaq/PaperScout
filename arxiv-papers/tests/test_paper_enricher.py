#!/usr/bin/env python3
"""
测试论文增强功能
"""
import os
import sys

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import load_config
from src.analyzers import PaperEnricher


def test_single_paper():
    """测试增强单篇论文"""
    print("="*60)
    print("测试 1: 增强单篇论文")
    print("="*60)

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

    api_key = config.get('brave', {}).get('api_key')

    if not api_key or api_key == "YOUR_BRAVE_API_KEY":
        print("❌ 错误: 请先配置 Brave API Key")
        return False

    print(f"✓ API Key: {api_key[:20]}...")

    enricher = PaperEnricher(api_key)

    # 测试论文（Memory in the Age of AI Agents）
    test_paper = {
        'arxiv_id': '2512.13564',
        'title': 'Memory in the Age of AI Agents: A Survey on Paradigms and Challenges',
        'authors': 'Example Authors',
        'quality_score': 85
    }

    print(f"\n测试论文: {test_paper['title'][:60]}...")
    print(f"原始质量分数: {test_paper['quality_score']}")

    # 增强论文
    enriched = enricher.enrich_paper(test_paper)

    # 显示结果
    signals = enriched.get('community_signals', {})

    print("\n" + "="*60)
    print("📊 增强结果")
    print("="*60)

    print(f"\n🔢 社交分数: {signals.get('social_score', 0)}/100")

    if 'quality_score_adjusted' in enriched:
        print(f"📈 质量分数: {enriched['quality_score_original']} → {enriched['quality_score_adjusted']}")

    print(f"\n🐙 GitHub 仓库: {len(signals.get('github_repos', []))}")
    for repo in signals.get('github_repos', []):
        print(f"  - {repo['repo_name']}")
        print(f"    Stars: {repo['stars']}, URL: {repo['url']}")

    print(f"\n💬 社区讨论: {signals.get('total_discussion_count', 0)}")
    print(f"  - Twitter: {signals.get('tweet_count', 0)}")
    print(f"  - Reddit: {signals.get('reddit_mentions', 0)}")
    print(f"  - Hacker News: {signals.get('hacker_news_mentions', 0)}")

    if signals.get('discussions'):
        print(f"\n讨论详情:")
        for i, disc in enumerate(signals['discussions'][:5], 1):
            print(f"  {i}. [{disc['source']}] {disc['title'][:60]}")
            print(f"     {disc['url']}")
            print(f"     相关性: {disc['relevance']}")

    return True


def test_batch_enrichment():
    """测试批量增强"""
    print("\n" + "="*60)
    print("测试 2: 批量增强论文")
    print("="*60)

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

    api_key = config.get('brave', {}).get('api_key')

    if not api_key or api_key == "YOUR_BRAVE_API_KEY":
        print("❌ 错误: 请先配置 Brave API Key")
        return False

    enricher = PaperEnricher(api_key)

    # 测试论文列表
    test_papers = [
        {
            'arxiv_id': '2512.13564',
            'title': 'Memory in the Age of AI Agents',
            'quality_score': 85
        },
        {
            'arxiv_id': '2602.08990',
            'title': 'InternAgent-1.5: Long-Horizon Scientific Discovery',
            'quality_score': 82
        },
        {
            'arxiv_id': '2602.09000',
            'title': 'iGRPO: Self-Feedback-Driven LLM Reasoning',
            'quality_score': 72
        }
    ]

    print(f"\n批量增强 {len(test_papers)} 篇论文...")

    # 批量增强
    enriched_papers = enricher.batch_enrich_papers(test_papers, max_papers=2)

    # 统计
    summary = enricher.get_enrichment_summary(enriched_papers)

    print("\n" + "="*60)
    print("📊 批量增强统计")
    print("="*60)

    print(f"\n总论文数: {summary['total_papers']}")
    print(f"已增强: {summary['enriched_papers']}")
    print(f"有 GitHub 的: {summary['papers_with_github']}")
    print(f"有讨论的: {summary['papers_with_discussions']}")
    print(f"总 GitHub 仓库: {summary['total_github_repos']}")
    print(f"总 stars: {summary['total_stars']}")
    print(f"总讨论: {summary['total_discussions']}")
    print(f"平均社交分数: {summary['avg_social_score']}/100")

    # 显示每篇论文的社交分数
    print("\n论文排名（按社交分数）:")
    sorted_papers = sorted(
        enriched_papers,
        key=lambda x: x.get('community_signals', {}).get('social_score', 0),
        reverse=True
    )

    for i, paper in enumerate(sorted_papers, 1):
        signals = paper.get('community_signals', {})
        social_score = signals.get('social_score', 0)
        title = paper['title'][:50]
        print(f"{i}. {title}... | 社交分数: {social_score}/100")

    return True


def test_social_score_calculation():
    """测试社交分数计算逻辑"""
    print("\n" + "="*60)
    print("测试 3: 社交分数计算")
    print("="*60)

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

    api_key = config.get('brave', {}).get('api_key')
    enricher = PaperEnricher(api_key)

    # 测试不同场景
    test_cases = [
        {
            'name': '高热度论文（多 stars + 多讨论）',
            'signals': {
                'github_stars': 1000,
                'total_discussion_count': 15,
                'tweet_count': 5,
                'reddit_mentions': 5,
                'hacker_news_mentions': 5
            }
        },
        {
            'name': '中等热度（有 GitHub，少量讨论）',
            'signals': {
                'github_stars': 100,
                'total_discussion_count': 5,
                'tweet_count': 3,
                'reddit_mentions': 2,
                'hacker_news_mentions': 0
            }
        },
        {
            'name': '低热度（仅少量讨论）',
            'signals': {
                'github_stars': 0,
                'total_discussion_count': 2,
                'tweet_count': 2,
                'reddit_mentions': 0,
                'hacker_news_mentions': 0
            }
        },
        {
            'name': 'HN 高质量讨论',
            'signals': {
                'github_stars': 50,
                'total_discussion_count': 3,
                'tweet_count': 0,
                'reddit_mentions': 0,
                'hacker_news_mentions': 3
            }
        }
    ]

    print()
    for test in test_cases:
        score = enricher._calculate_social_score(test['signals'])
        print(f"场景: {test['name']}")
        print(f"  GitHub stars: {test['signals']['github_stars']}")
        print(f"  讨论数: {test['signals']['total_discussion_count']}")
        print(f"  平台: Twitter({test['signals']['tweet_count']}), Reddit({test['signals']['reddit_mentions']}), HN({test['signals']['hacker_news_mentions']})")
        print(f"  → 社交分数: {score}/100")
        print()

    return True


def main():
    """主函数"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                                                          ║")
    print("║          论文增强功能测试                                 ║")
    print("║                                                          ║")
    print("╚══════════════════════════════════════════════════════════╝")

    results = []

    # 测试 1: 单篇论文
    try:
        result1 = test_single_paper()
        results.append(("单篇论文增强", result1))
    except Exception as e:
        print(f"❌ 测试 1 异常: {e}")
        results.append(("单篇论文增强", False))

    # 测试 2: 批量增强
    try:
        result2 = test_batch_enrichment()
        results.append(("批量增强", result2))
    except Exception as e:
        print(f"❌ 测试 2 异常: {e}")
        results.append(("批量增强", False))

    # 测试 3: 社交分数计算
    try:
        result3 = test_social_score_calculation()
        results.append(("社交分数计算", result3))
    except Exception as e:
        print(f"❌ 测试 3 异常: {e}")
        results.append(("社交分数计算", False))

    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试汇总")
    print("="*60)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s} {status}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！论文增强功能正常工作。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查配置。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
