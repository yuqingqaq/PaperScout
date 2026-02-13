#!/usr/bin/env python3
"""
测试 LiteLLM 连接
"""
import os
import sys

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anthropic import Anthropic
from src.utils import load_config

def test_litellm():
    """测试 LiteLLM 连接"""
    print("=" * 50)
    print("测试 LiteLLM 连接")
    print("=" * 50)

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

    # 检查配置
    if 'litellm' not in config:
        print("❌ 错误: config.json 中缺少 litellm 配置")
        print("\n请添加:")
        print('{')
        print('  "litellm": {')
        print('    "api_key": "your_api_key",')
        print('    "base_url": "http://47.253.161.79:8888"')
        print('  }')
        print('}')
        return False

    api_key = config['litellm'].get('api_key')
    base_url = config['litellm'].get('base_url')

    if not api_key:
        print("❌ 错误: 缺少 litellm.api_key")
        return False

    if not base_url:
        print("❌ 错误: 缺少 litellm.base_url")
        return False

    print(f"\n📡 API Key: {api_key[:20]}...")
    print(f"🌐 Base URL: {base_url}")

    # 测试连接
    print("\n正在测试连接...")
    try:
        client = Anthropic(
            api_key=api_key,
            base_url=base_url
        )

        # 发送测试请求
        message = client.messages.create(
            model="anthropic/claude-sonnet-4.5",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "你好，请回复'测试成功'"}
            ]
        )

        response = message.content[0].text
        print(f"\n✅ 连接成功!")
        print(f"📝 模型响应: {response}")
        return True

    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        print("\n请检查:")
        print("1. base_url 是否正确")
        print("2. LiteLLM 服务器是否运行")
        print("3. API Key 是否有效")
        print("4. 网络连接是否正常")
        return False

if __name__ == '__main__':
    success = test_litellm()
    sys.exit(0 if success else 1)
