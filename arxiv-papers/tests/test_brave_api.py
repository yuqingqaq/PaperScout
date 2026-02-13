#!/usr/bin/env python3
"""
测试 Brave Search API
"""
import os
import sys

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import load_config
from src.fetchers import BraveSearcher


def test_basic_search():
    """测试基础搜索"""
    print("=" * 60)
    print("测试 1: 基础搜索")
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

    api_key = config.get('brave', {}).get('api_key')

    if not api_key or api_key == "YOUR_BRAVE_API_KEY":
        print("❌ 错误: 请先配置 Brave API Key")
        print("\n在 config.json 中设置:")
        print('{')
        print('  "brave": {')
        print('    "api_key": "YOUR_BRAVE_API_KEY",')
        print('    "enabled": true')
        print('  }')
        print('}')
        print("\n获取 API Key: https://brave.com/search/api/")
        return False

    print(f"✓ API Key: {api_key[:20]}...")

    searcher = BraveSearcher(api_key)

    # 测试搜索
    print("\n搜索: 'agent memory arxiv'")
    results = searcher.search_papers("agent memory arxiv", count=5, freshness="pw")

    if results:
        print(f"\n✅ 找到 {len(results)} 条结果:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            if 'arxiv_id' in result:
                print(f"   arXiv ID: {result['arxiv_id']}")
            print()
        return True
    else:
        print("❌ 未找到结果")
        return False


def test_arxiv_search():
    """测试 arXiv 专用搜索"""
    print("\n" + "=" * 60)
    print("测试 2: arXiv 专用搜索")
    print("=" * 60)

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

    searcher = BraveSearcher(api_key)

    # 测试 arXiv 搜索
    print("\n搜索 arXiv 论文: 'agent memory'")
    arxiv_ids = searcher.search_arxiv_papers("agent memory", days=7)

    if arxiv_ids:
        print(f"\n✅ 找到 {len(arxiv_ids)} 个 arXiv IDs:\n")
        for i, arxiv_id in enumerate(arxiv_ids, 1):
            print(f"{i}. {arxiv_id}")
            print(f"   https://arxiv.org/abs/{arxiv_id}")
        return True
    else:
        print("❌ 未找到 arXiv 论文")
        return False


def test_trending_search():
    """测试热门论文搜索"""
    print("\n" + "=" * 60)
    print("测试 3: 热门论文搜索")
    print("=" * 60)

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

    searcher = BraveSearcher(api_key)

    # 测试热门论文搜索
    topics = ["agent memory", "agentic memory", "llm memory"]
    print(f"\n搜索热门论文: {topics}")

    results = searcher.search_trending_papers(topics, days=7)

    if results:
        print(f"\n✅ 找到 {len(results)} 条热门结果:\n")
        for i, result in enumerate(results[:10], 1):  # 只显示前10条
            print(f"{i}. [{result['topic']}] {result['title']}")
            print(f"   {result['url']}")
            if 'arxiv_id' in result:
                print(f"   arXiv ID: {result['arxiv_id']}")
            print()
        return True
    else:
        print("❌ 未找到热门论文")
        return False


def test_discussions_search():
    """测试论文讨论搜索"""
    print("\n" + "=" * 60)
    print("测试 4: 论文讨论搜索")
    print("=" * 60)

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

    searcher = BraveSearcher(api_key)

    # 测试论文讨论搜索
    arxiv_id = "2512.13564"  # Memory in the Age of AI Agents
    print(f"\n搜索论文讨论: {arxiv_id}")

    discussions = searcher.search_paper_discussions(arxiv_id)

    if discussions:
        print(f"\n✅ 找到 {len(discussions)} 条讨论:\n")
        for i, disc in enumerate(discussions, 1):
            print(f"{i}. [{disc['source']}] {disc['title']}")
            print(f"   {disc['url']}")
            print(f"   {disc['age']}")
            print()
        return True
    else:
        print("⚠️ 未找到讨论（这是正常的，不是所有论文都有讨论）")
        return True  # 不算失败


def main():
    """主函数"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                                                          ║")
    print("║          Brave Search API 测试                           ║")
    print("║                                                          ║")
    print("╚══════════════════════════════════════════════════════════╝")

    results = []

    # 测试 1: 基础搜索
    try:
        result1 = test_basic_search()
        results.append(("基础搜索", result1))
    except Exception as e:
        print(f"❌ 测试 1 异常: {e}")
        results.append(("基础搜索", False))

    # 测试 2: arXiv 搜索
    try:
        result2 = test_arxiv_search()
        results.append(("arXiv 专用搜索", result2))
    except Exception as e:
        print(f"❌ 测试 2 异常: {e}")
        results.append(("arXiv 专用搜索", False))

    # 测试 3: 热门论文搜索
    try:
        result3 = test_trending_search()
        results.append(("热门论文搜索", result3))
    except Exception as e:
        print(f"❌ 测试 3 异常: {e}")
        results.append(("热门论文搜索", False))

    # 测试 4: 论文讨论搜索
    try:
        result4 = test_discussions_search()
        results.append(("论文讨论搜索", result4))
    except Exception as e:
        print(f"❌ 测试 4 异常: {e}")
        results.append(("论文讨论搜索", False))

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
        print("\n🎉 所有测试通过！Brave API 配置正确。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查配置。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
