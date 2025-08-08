"""
智能抢购助手的配置管理模块。

此包处理所有配置相关功能，包括:
- 默认配置值
- 配置验证
- 配置文件管理
"""

from .defaults import DEFAULT_CONFIG
from .manager import ConfigManager
from .validator import ConfigValidator

__all__ = ["DEFAULT_CONFIG", "ConfigManager", "ConfigValidator"]