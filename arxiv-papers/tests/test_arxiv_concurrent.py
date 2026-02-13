#!/usr/bin/env python3
"""
测试 arXiv API 并发性能
"""
import os
import sys

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import arxiv


def search_single_keyword(keyword: str, max_results: int = 10) -> dict:
    """
    单个关键词搜索

    Args:
        keyword: 搜索关键词
        max_results: 最大结果数

    Returns:
        搜索结果统计
    """
    start_time = time.time()

    try:
        search = arxiv.Search(
            query=keyword,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        papers_count = 0
        for result in search.results():
            papers_count += 1

        elapsed_time = time.time() - start_time

        return {
            'keyword': keyword,
            'success': True,
            'papers_count': papers_count,
            'elapsed_time': elapsed_time,
            'error': None
        }

    except Exception as e:
        elapsed_time = time.time() - start_time
        return {
            'keyword': keyword,
            'success': False,
            'papers_count': 0,
            'elapsed_time': elapsed_time,
            'error': str(e)
        }


def test_sequential(keywords: list, max_results: int = 10):
    """顺序测试"""
    print("\n" + "="*60)
    print("测试 1: 顺序执行（Sequential）")
    print("="*60)

    start_time = time.time()
    results = []

    for keyword in keywords:
        print(f"搜索: {keyword}")
        result = search_single_keyword(keyword, max_results)

        if result['success']:
            print(f"  ✓ 找到 {result['papers_count']} 篇论文，耗时 {result['elapsed_time']:.2f}s")
        else:
            print(f"  ✗ 失败: {result['error']}")

        results.append(result)

    total_time = time.time() - start_time

    print(f"\n总耗时: {total_time:.2f}s")
    print(f"平均每个关键词: {total_time/len(keywords):.2f}s")

    return results, total_time


def test_parallel_threads(keywords: list, max_results: int = 10, max_workers: int = 3):
    """线程池并发测试"""
    print("\n" + "="*60)
    print(f"测试 2: 线程池并发（{max_workers} workers）")
    print("="*60)

    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_keyword = {
            executor.submit(search_single_keyword, kw, max_results): kw
            for kw in keywords
        }

        # 收集结果
        for future in as_completed(future_to_keyword):
            result = future.result()

            if result['success']:
                print(f"✓ {result['keyword']}: {result['papers_count']} 篇论文，耗时 {result['elapsed_time']:.2f}s")
            else:
                print(f"✗ {result['keyword']}: 失败 - {result['error']}")

            results.append(result)

    total_time = time.time() - start_time

    print(f"\n总耗时: {total_time:.2f}s")
    print(f"加速比: {(total_time/len(keywords)) / (results[0]['elapsed_time'] if results else 1):.2f}x")

    return results, total_time


def test_with_delay(keywords: list, max_results: int = 10, delay: float = 3.0):
    """带延迟的顺序测试"""
    print("\n" + "="*60)
    print(f"测试 3: 带延迟的顺序执行（延迟 {delay}s）")
    print("="*60)

    start_time = time.time()
    results = []

    for i, keyword in enumerate(keywords):
        if i > 0:
            print(f"等待 {delay}s...")
            time.sleep(delay)

        print(f"搜索: {keyword}")
        result = search_single_keyword(keyword, max_results)

        if result['success']:
            print(f"  ✓ 找到 {result['papers_count']} 篇论文，耗时 {result['elapsed_time']:.2f}s")
        else:
            print(f"  ✗ 失败: {result['error']}")

        results.append(result)

    total_time = time.time() - start_time

    print(f"\n总耗时: {total_time:.2f}s")
    print(f"实际搜索时间: {sum(r['elapsed_time'] for r in results):.2f}s")
    print(f"延迟时间: {delay * (len(keywords) - 1):.2f}s")

    return results, total_time


def test_batch_concurrent(keywords: list, max_results: int = 10, batch_size: int = 3, delay: float = 5.0):
    """分批并发测试"""
    print("\n" + "="*60)
    print(f"测试 4: 分批并发（batch_size={batch_size}, delay={delay}s）")
    print("="*60)

    start_time = time.time()
    all_results = []

    # 分批
    for i in range(0, len(keywords), batch_size):
        batch = keywords[i:i+batch_size]
        print(f"\n批次 {i//batch_size + 1}: {batch}")

        if i > 0:
            print(f"等待 {delay}s...")
            time.sleep(delay)

        # 并发执行当前批次
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_keyword = {
                executor.submit(search_single_keyword, kw, max_results): kw
                for kw in batch
            }

            for future in as_completed(future_to_keyword):
                result = future.result()

                if result['success']:
                    print(f"  ✓ {result['keyword']}: {result['papers_count']} 篇，{result['elapsed_time']:.2f}s")
                else:
                    print(f"  ✗ {result['keyword']}: {result['error']}")

                all_results.append(result)

    total_time = time.time() - start_time

    print(f"\n总耗时: {total_time:.2f}s")
    print(f"成功率: {sum(1 for r in all_results if r['success'])}/{len(all_results)}")

    return all_results, total_time


def analyze_results(test_name: str, results: list, total_time: float):
    """分析测试结果"""
    print(f"\n📊 {test_name} - 统计分析")
    print("-" * 60)

    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count
    total_papers = sum(r['papers_count'] for r in results if r['success'])

    print(f"总请求数: {len(results)}")
    print(f"成功: {success_count} | 失败: {fail_count}")
    print(f"成功率: {success_count/len(results)*100:.1f}%")
    print(f"总论文数: {total_papers}")
    print(f"总耗时: {total_time:.2f}s")

    if results:
        avg_time = sum(r['elapsed_time'] for r in results) / len(results)
        print(f"平均请求时间: {avg_time:.2f}s")

    # 列出失败的请求
    if fail_count > 0:
        print(f"\n失败的请求:")
        for r in results:
            if not r['success']:
                print(f"  - {r['keyword']}: {r['error']}")


def main():
    """主函数"""
    print("="*60)
    print("arXiv API 并发性能测试")
    print("="*60)
    print(f"测试时间: {datetime.now()}")

    # 测试关键词
    keywords = [
        "agent memory",
        "agentic memory",
        "llm memory",
        "ai agent memory management",
        "episodic memory llm",
        "memory-augmented agents"
    ]

    print(f"\n测试关键词 ({len(keywords)} 个):")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i}. {kw}")

    max_results = 10

    # 测试 1: 顺序执行
    results_seq, time_seq = test_sequential(keywords, max_results)
    analyze_results("顺序执行", results_seq, time_seq)

    # 测试 2: 3线程并发
    results_parallel_3, time_parallel_3 = test_parallel_threads(keywords, max_results, max_workers=3)
    analyze_results("3线程并发", results_parallel_3, time_parallel_3)

    # 测试 3: 6线程并发
    results_parallel_6, time_parallel_6 = test_parallel_threads(keywords, max_results, max_workers=6)
    analyze_results("6线程并发", results_parallel_6, time_parallel_6)

    # 测试 4: 带延迟顺序执行
    results_delay, time_delay = test_with_delay(keywords, max_results, delay=3.0)
    analyze_results("带延迟顺序执行", results_delay, time_delay)

    # 测试 5: 分批并发
    results_batch, time_batch = test_batch_concurrent(keywords, max_results, batch_size=3, delay=5.0)
    analyze_results("分批并发", results_batch, time_batch)

    # 综合对比
    print("\n" + "="*60)
    print("📈 综合对比")
    print("="*60)

    tests = [
        ("顺序执行", time_seq, results_seq),
        ("3线程并发", time_parallel_3, results_parallel_3),
        ("6线程并发", time_parallel_6, results_parallel_6),
        ("带延迟顺序", time_delay, results_delay),
        ("分批并发", time_batch, results_batch)
    ]

    for name, total_time, results in tests:
        success_rate = sum(1 for r in results if r['success']) / len(results) * 100
        print(f"{name:15s} | 耗时: {total_time:6.2f}s | 成功率: {success_rate:5.1f}%")

    # 推荐策略
    print("\n" + "="*60)
    print("💡 推荐策略")
    print("="*60)

    best_success_rate = max((sum(1 for r in res if r['success']) / len(res), name)
                           for name, _, res in tests)

    print(f"最佳成功率: {best_success_rate[1]} ({best_success_rate[0]*100:.1f}%)")

    # 找出最快且成功率 > 80% 的
    good_tests = [(name, t, r) for name, t, r in tests
                 if sum(1 for x in r if x['success']) / len(r) >= 0.8]

    if good_tests:
        fastest = min(good_tests, key=lambda x: x[1])
        print(f"最快方案: {fastest[0]} ({fastest[1]:.2f}s)")

    print("\n建议:")
    print("1. 如果成功率优先: 使用带延迟的顺序执行（3秒延迟）")
    print("2. 如果速度优先: 使用分批并发（batch_size=3, delay=5s）")
    print("3. 避免使用: 6线程并发（容易触发限流）")


if __name__ == '__main__':
    main()
