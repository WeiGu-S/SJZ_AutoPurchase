"""
智能抢购助手的集中式日志配置。

此模块为所有组件提供一致的日志设置，
具有文件和控制台输出功能。
"""

import logging
import os
from typing import Optional
from datetime import datetime


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> logging.Logger:
    """
    设置集中式日志配置。
    
    参数:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 可选的日志文件路径。如果为None，使用默认的'抢购日志.log'
        enable_console: 是否启用控制台输出
        
    返回:
        配置的日志记录器实例
    """
    if log_file is None:
        log_file = '抢购日志.log'
    
    # Create logger
    logger = logging.getLogger('smart_buyer')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file {log_file}: {e}")
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    为特定模块获取日志记录器实例。
    
    Args:
        name: 日志记录器名称（通常是__name__）
        
    Returns:
        日志记录器实例
    """
    return logging.getLogger(f'smart_buyer.{name}')


def log_operation(logger: logging.Logger, operation: str, details: Optional[str] = None):
    """
    记录带有时间戳和可选详细信息的操作。
    
    Args:
        logger: 日志记录器实例
        operation: 操作描述
        details: 可选的附加详细信息
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    message = f"[{timestamp}] {operation}"
    if details:
        message += f": {details}"
    logger.info(message)