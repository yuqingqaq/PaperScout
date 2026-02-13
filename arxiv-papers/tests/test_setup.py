#!/usr/bin/env python3
"""
安装验证脚本
检查所有依赖和配置是否正确
"""
import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

def check_python_version():
    """检查 Python 版本"""
    print("1. 检查 Python 版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ✗ Python 版本过低: {version.major}.{version.minor}")
        print("   需要 Python 3.8 或更高版本")
        return False

def check_dependencies():
    """检查依赖包"""
    print("\n2. 检查依赖包...")
    required_packages = [
        'arxiv',
        'requests',
        'feedparser',
        'beautifulsoup4',
        'anthropic',
        'dateutil',
        'schedule'
    ]

    missing = []
    for package in required_packages:
        try:
            if package == 'dateutil':
                __import__('dateutil')
            elif package == 'beautifulsoup4':
                __import__('bs4')
            else:
                __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package} 未安装")
            missing.append(package)

    if missing:
        print(f"\n   缺少依赖: {', '.join(missing)}")
        print("   运行: pip install -r requirements.txt")
        return False
    return True

def check_config():
    """检查配置文件"""
    print("\n3. 检查配置文件...")

    if not os.path.exists('config.json'):
        print("   ✗ config.json 不存在")
        print("   请复制 config.example.json 为 config.json 并填写配置")
        return False

    try:
        with open('config.json', 'r') as f:
            config = json.load(f)

        print("   ✓ config.json 存在")

        # 检查必需字段
        issues = []

        if 'feishu' in config:
            if config['feishu']['app_id'].startswith('cli_'):
                print("   ✓ 飞书 App ID 已配置")
            else:
                issues.append("飞书 App ID 未配置")
        else:
            issues.append("缺少 feishu 配置")

        if 'anthropic' in config:
            if config['anthropic']['api_key'].startswith('sk-ant-'):
                print("   ✓ Anthropic API Key 已配置")
            else:
                issues.append("Anthropic API Key 未配置")
        else:
            issues.append("缺少 anthropic 配置")

        if issues:
            print("\n   配置问题:")
            for issue in issues:
                print(f"   - {issue}")
            return False

        return True

    except json.JSONDecodeError:
        print("   ✗ config.json 格式错误")
        return False
    except Exception as e:
        print(f"   ✗ 读取配置失败: {e}")
        return False

def check_directories():
    """检查目录结构"""
    print("\n4. 检查目录结构...")

    required_dirs = ['src', 'scripts', 'output', 'references', 'logs']
    all_ok = True

    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"   ✓ {dir_name}/")
        else:
            print(f"   ✗ {dir_name}/ 不存在")
            all_ok = False

    return all_ok

def check_files():
    """检查必要文件"""
    print("\n5. 检查必要文件...")

    required_files = [
        'src/main.py',
        'src/arxiv_fetcher.py',
        'src/paper_analyzer.py',
        'src/paper_manager.py',
        'src/feishu_notifier.py',
        'scripts/serve.sh',
        'scripts/daily_run.sh',
        'output/papers.json',
        'output/papers.html'
    ]

    all_ok = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✓ {file_path}")
        else:
            print(f"   ✗ {file_path} 不存在")
            all_ok = False

    return all_ok

def main():
    """主函数"""
    print("=" * 50)
    print("ArXiv Papers Agent - 安装验证")
    print("=" * 50)
    print()

    checks = [
        check_python_version(),
        check_dependencies(),
        check_config(),
        check_directories(),
        check_files()
    ]

    print("\n" + "=" * 50)
    if all(checks):
        print("✓ 所有检查通过！")
        print("=" * 50)
        print("\n下一步:")
        print("1. 启动 Web 服务器: cd scripts && ./serve.sh 8888")
        print("2. 测试添加论文: python src/main.py --mode add --url https://arxiv.org/abs/2512.13564")
        print("3. 设置定时任务: cd scripts && ./setup_cron.sh")
        return 0
    else:
        print("✗ 部分检查未通过")
        print("=" * 50)
        print("\n请根据上述提示修复问题")
        return 1

if __name__ == '__main__':
    sys.exit(main())
