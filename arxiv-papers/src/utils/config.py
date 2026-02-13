"""
配置加载和验证模块
"""
import os
import json
from typing import Dict, Any, List, Optional


class ConfigError(Exception):
    """配置错误"""
    pass


def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
        
    Raises:
        ConfigError: 配置文件不存在或格式错误
    """
    if not os.path.exists(config_path):
        raise ConfigError(f"配置文件不存在: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        raise ConfigError(f"配置文件 JSON 格式错误: {e}")
    except Exception as e:
        raise ConfigError(f"加载配置文件失败: {e}")


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    验证配置完整性
    
    Args:
        config: 配置字典
        
    Returns:
        警告信息列表（空列表表示验证通过）
        
    Raises:
        ConfigError: 必需配置缺失
    """
    warnings = []
    
    # 1. 验证必需的 LiteLLM 或 Anthropic 配置
    if 'litellm' not in config and 'anthropic' not in config:
        raise ConfigError("必须配置 'litellm' 或 'anthropic' API")
    
    if 'litellm' in config:
        litellm = config['litellm']
        if not litellm.get('api_key'):
            raise ConfigError("litellm.api_key 未配置")
        if litellm.get('api_key') == 'your_litellm_api_key':
            raise ConfigError("请填写真实的 litellm.api_key")
    elif 'anthropic' in config:
        if not config['anthropic'].get('api_key'):
            raise ConfigError("anthropic.api_key 未配置")
    
    # 2. 验证飞书配置（可选但建议）
    if 'feishu' not in config:
        warnings.append("⚠️  未配置飞书通知，将跳过推送")
    elif not config['feishu'].get('webhook_url'):
        warnings.append("⚠️  飞书 webhook_url 未配置，将跳过推送")
    elif 'YOUR_WEBHOOK' in config['feishu'].get('webhook_url', ''):
        warnings.append("⚠️  请配置真实的飞书 webhook_url")
    
    # 3. 验证 arXiv 配置
    arxiv_config = config.get('arxiv', {})
    if not arxiv_config.get('search_keywords'):
        warnings.append("⚠️  未配置搜索关键词，将使用默认关键词")
    
    # 4. 验证 Brave 配置（可选）
    brave_config = config.get('brave', {})
    if brave_config.get('enabled', False):
        api_key = brave_config.get('api_key', '')
        if not api_key or api_key == 'YOUR_BRAVE_API_KEY':
            warnings.append("⚠️  Brave API Key 未配置，将禁用社区增强")
    
    return warnings


def get_default_config() -> Dict[str, Any]:
    """
    获取默认配置
    
    Returns:
        默认配置字典
    """
    return {
        'arxiv': {
            'search_keywords': [
                'agent memory',
                'agentic memory',
                'llm memory'
            ],
            'max_results_per_keyword': 20,
            'days_back': 14
        },
        'recommendation': {
            'max_papers': 10,
            'schedule_time': '10:00',
            'workdays_only': True,
            'strict_relevance': True
        },
        'brave': {
            'enabled': False,
            'max_enrich': 5,
            'verify_relevance': True
        }
    }


def merge_with_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    将用户配置与默认配置合并
    
    Args:
        config: 用户配置
        
    Returns:
        合并后的配置
    """
    defaults = get_default_config()
    
    # 深度合并
    for key, default_value in defaults.items():
        if key not in config:
            config[key] = default_value
        elif isinstance(default_value, dict):
            for sub_key, sub_value in default_value.items():
                if sub_key not in config[key]:
                    config[key][sub_key] = sub_value
    
    return config
