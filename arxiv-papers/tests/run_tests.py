#!/usr/bin/env python3
"""
统一测试运行器
运行所有或指定的测试
"""
import os
import sys
import argparse

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_config_test():
    """测试配置加载"""
    print("\n" + "=" * 60)
    print("🔧 测试配置加载和验证")
    print("=" * 60)
    
    from src.utils import load_config, validate_config, ConfigError
    
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config.json'
    )
    
    try:
        config = load_config(config_path)
        print(f"✅ 配置加载成功")
        
        warnings = validate_config(config)
        if warnings:
            print("\n⚠️  配置警告:")
            for w in warnings:
                print(f"   {w}")
        else:
            print("✅ 配置验证通过")
        
        return True
    except ConfigError as e:
        print(f"❌ 配置错误: {e}")
        return False


def run_litellm_test():
    """测试 LiteLLM 连接"""
    print("\n" + "=" * 60)
    print("🤖 测试 LiteLLM/Claude API 连接")
    print("=" * 60)
    
    from src.utils import load_config
    from anthropic import Anthropic
    
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config.json'
    )
    
    try:
        config = load_config(config_path)
        
        if 'litellm' in config:
            api_key = config['litellm']['api_key']
            base_url = config['litellm'].get('base_url')
            print(f"   API: LiteLLM ({base_url})")
        else:
            api_key = config['anthropic']['api_key']
            base_url = None
            print("   API: Anthropic 直连")
        
        client = Anthropic(api_key=api_key, base_url=base_url)
        
        message = client.messages.create(
            model="anthropic/claude-sonnet-4.5",
            max_tokens=100,
            messages=[{"role": "user", "content": "Say 'API test successful' in one line."}]
        )
        
        response = message.content[0].text
        print(f"✅ API 响应: {response[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ API 测试失败: {e}")
        return False


def run_feishu_test():
    """测试飞书 Webhook"""
    print("\n" + "=" * 60)
    print("📬 测试飞书 Webhook")
    print("=" * 60)
    
    from src.utils import load_config
    from src.notifiers import FeishuNotifier
    
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config.json'
    )
    
    try:
        config = load_config(config_path)
        webhook_url = config.get('feishu', {}).get('webhook_url')
        
        if not webhook_url or 'YOUR_WEBHOOK' in webhook_url:
            print("⚠️  飞书 Webhook 未配置，跳过测试")
            return True
        
        notifier = FeishuNotifier(webhook_url)
        success = notifier.send_message("🧪 ArXiv Papers 测试消息")
        
        if success:
            print("✅ 飞书消息发送成功")
            return True
        else:
            print("❌ 飞书消息发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 飞书测试失败: {e}")
        return False


def run_brave_test():
    """测试 Brave Search API"""
    print("\n" + "=" * 60)
    print("🔍 测试 Brave Search API")
    print("=" * 60)
    
    from src.utils import load_config
    from src.fetchers import BraveSearcher
    
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config.json'
    )
    
    try:
        config = load_config(config_path)
        brave_config = config.get('brave', {})
        
        if not brave_config.get('enabled', False):
            print("⚠️  Brave Search 未启用，跳过测试")
            return True
        
        api_key = brave_config.get('api_key', '')
        if not api_key or api_key == 'YOUR_BRAVE_API_KEY':
            print("⚠️  Brave API Key 未配置，跳过测试")
            return True
        
        searcher = BraveSearcher(api_key)
        results = searcher.search_papers("agent memory", count=3, freshness="pm")
        
        if results:
            print(f"✅ 搜索成功，找到 {len(results)} 条结果")
            for r in results[:2]:
                print(f"   - {r['title'][:50]}...")
            return True
        else:
            print("⚠️  未找到结果（可能是 API 问题）")
            return True
            
    except Exception as e:
        print(f"❌ Brave 测试失败: {e}")
        return False


def run_arxiv_test():
    """测试 arXiv API"""
    print("\n" + "=" * 60)
    print("📚 测试 arXiv API")
    print("=" * 60)
    
    from src.utils import load_config
    from src.fetchers import ArxivFetcher
    
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config.json'
    )
    
    try:
        config = load_config(config_path)
        fetcher = ArxivFetcher(config)
        
        # 测试获取单篇论文
        print("   测试获取论文 2312.00752...")
        paper = fetcher.get_paper_by_id("2312.00752")
        
        if paper:
            print(f"✅ 获取成功: {paper['title'][:50]}...")
            return True
        else:
            print("❌ 获取失败")
            return False
            
    except Exception as e:
        print(f"❌ arXiv 测试失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='ArXiv Papers 测试运行器')
    parser.add_argument(
        '--test', '-t',
        choices=['all', 'config', 'litellm', 'feishu', 'brave', 'arxiv'],
        default='all',
        help='运行指定测试'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("🧪 ArXiv Papers 系统测试")
    print("=" * 60)
    
    results = {}
    
    if args.test in ['all', 'config']:
        results['config'] = run_config_test()
    
    if args.test in ['all', 'arxiv']:
        results['arxiv'] = run_arxiv_test()
    
    if args.test in ['all', 'litellm']:
        results['litellm'] = run_litellm_test()
    
    if args.test in ['all', 'feishu']:
        results['feishu'] = run_feishu_test()
    
    if args.test in ['all', 'brave']:
        results['brave'] = run_brave_test()
    
    # 汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
    
    print(f"\n   总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置")
        return 1


if __name__ == '__main__':
    sys.exit(main())
