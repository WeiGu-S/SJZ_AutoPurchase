"""
智能抢购助手的主入口点。

此模块提供集成所有组件的主入口点，
并保持与原始sjz.py执行的向后兼容性。
"""

import sys
import os
from typing import List, Optional
from .ui.cli import CLIInterface
from .ui.gui import GUIInterface
from .utils.logging import setup_logging, get_logger
from .core.exceptions import SmartBuyerError


def main(args: Optional[List[str]] = None) -> int:
    """
    智能抢购助手的主入口点。
    
    此函数根据命令行参数确定是在GUI还是CLI模式下运行，
    并提供向后兼容性。
    
    参数:
        args: 命令行参数（None表示使用sys.argv）
        
    返回:
        退出代码（0表示成功，非零表示错误）
    """
    try:
        # 初始化基本日志
        setup_logging(log_level="INFO", enable_console=True)
        logger = get_logger(__name__)
        
        # 解析参数以确定模式
        if args is None:
            args = sys.argv[1:]
        
        # 检查CLI特定参数
        cli_args = {
            '--console', '--test-ocr', '--test-click', '--validate-config',
            '--get', '--list-config', '--set', '--config', '-c',
            '--verbose', '-v', '--quiet', '-q', '--timeout', '--no-confirm'
        }
        
        # 确定是否应该在CLI模式下运行
        should_use_cli = any(arg in cli_args for arg in args) or '--console' in args
        
        if should_use_cli:
            # 运行CLI界面
            logger.info("在CLI模式下启动智能抢购助手")
            cli = CLIInterface()
            return cli.run(args)
        else:
            # 运行GUI界面（默认）
            logger.info("在GUI模式下启动智能抢购助手")
            gui = GUIInterface()
            gui.run()
            return 0
            
    except KeyboardInterrupt:
        print("\\n程序被用户中断")
        return 130
    except ImportError as e:
        print(f"导入错误: {e}", file=sys.stderr)
        print("请确保所有依赖包已正确安装", file=sys.stderr)
        return 1
    except SmartBuyerError as e:
        print(f"Smart Buyer错误: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        return 1


def gui_main() -> int:
    """
    专门用于GUI模式的入口点。
    
    Returns:
        退出代码
    """
    try:
        setup_logging(log_level="INFO", enable_console=True)
        logger = get_logger(__name__)
        logger.info("Starting Smart Buyer GUI")
        
        gui = GUIInterface()
        gui.run()
        return 0
        
    except Exception as e:
        print(f"GUI启动失败: {e}", file=sys.stderr)
        return 1


def cli_main() -> int:
    """
    专门用于CLI模式的入口点。
    
    Returns:
        退出代码
    """
    try:
        cli = CLIInterface()
        return cli.run()
        
    except Exception as e:
        print(f"CLI启动失败: {e}", file=sys.stderr)
        return 1


def console_main() -> int:
    """
    控制台模式的入口点（向后兼容）。
    
    此函数提供与原始控制台模式执行的向后兼容性。
    
    Returns:
        退出代码
    """
    return cli_main()


# Backward compatibility: Allow direct execution as script
if __name__ == '__main__':
    sys.exit(main())