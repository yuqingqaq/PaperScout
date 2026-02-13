"""
日志模块
统一的日志配置和管理
"""
import logging
import os
from datetime import datetime
from typing import Optional


def setup_logging(
    log_dir: Optional[str] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    配置全局日志
    
    Args:
        log_dir: 日志文件目录，None 则不写文件
        level: 日志级别
        console: 是否输出到控制台
        
    Returns:
        根 logger
    """
    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 简洁格式（控制台用）
    console_formatter = logging.Formatter(
        fmt='%(asctime)s %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 获取根 logger
    root_logger = logging.getLogger('arxiv_papers')
    root_logger.setLevel(level)
    
    # 清除已有 handlers
    root_logger.handlers.clear()
    
    # 控制台 handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # 文件 handler
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(
            log_dir, 
            f"daily_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取子 logger
    
    Args:
        name: 模块名
        
    Returns:
        logger 实例
    """
    return logging.getLogger(f'arxiv_papers.{name}')
