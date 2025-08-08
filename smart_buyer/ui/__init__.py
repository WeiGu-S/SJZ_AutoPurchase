"""
智能抢购助手的用户界面模块。

此包包含GUI和CLI界面:
- 使用tkinter的GUI界面
- 用于命令行使用的CLI界面
"""

from .gui import GUIInterface
from .cli import CLIInterface

__all__ = ["GUIInterface", "CLIInterface"]