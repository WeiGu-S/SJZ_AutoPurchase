"""
Smart Buyer - 智能抢购助手

功能强大的自动化购买工具，具有GUI和CLI界面，
具备智能倒计时识别、配置管理和全面的日志记录功能。
"""

__version__ = "2.0.0"
__author__ = "Smart Buyer Team"

from .main import main, gui_main, cli_main, console_main

__all__ = ["main", "gui_main", "cli_main", "console_main"]