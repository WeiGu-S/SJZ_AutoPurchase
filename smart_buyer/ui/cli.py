"""
智能抢购助手的CLI界面模块。

此模块为自动化购买提供命令行界面，
具有参数解析和基于控制台的交互功能。
"""

import argparse
import sys
import time
from typing import Optional, List
from ..config.manager import ConfigManager
from ..core.ocr import OCRProcessor
from ..core.automation import AutomationEngine, AutomationState
from ..core.exceptions import SmartBuyerError, ConfigurationError
from ..utils.logging import get_logger, setup_logging
from ..utils.helpers import format_time_remaining


class CLIInterface:
    """智能抢购助手的命令行界面。"""
    
    def __init__(self):
        """初始化CLI界面。"""
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.ocr_processor = OCRProcessor(
            tesseract_path=self.config_manager.get('tesseract_path', ''),
            ocr_config=self.config_manager.get('ocr_config', '--psm 8')
        )
        self.automation_engine = AutomationEngine(self.ocr_processor)
        
        # CLI state
        self.verbose = False
        self.quiet = False
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run CLI interface with command line arguments.
        
        Args:
            args: Command line arguments (None to use sys.argv)
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Parse arguments
            parsed_args = self._parse_arguments(args)
            
            # Setup logging based on verbosity
            log_level = "DEBUG" if parsed_args.verbose else "INFO"
            if parsed_args.quiet:
                log_level = "ERROR"
            
            setup_logging(
                log_level=log_level,
                log_file=self.config_manager.get('log_file', '抢购日志.log'),
                enable_console=not parsed_args.quiet
            )
            
            self.verbose = parsed_args.verbose
            self.quiet = parsed_args.quiet
            
            # Execute command
            return self._execute_command(parsed_args)
            
        except KeyboardInterrupt:
            self._print_message("\\n程序被用户中断")
            return 130  # Standard exit code for SIGINT
        except Exception as e:
            self.logger.error(f"CLI execution failed: {e}")
            self._print_error(f"执行失败: {e}")
            return 1
    
    def _parse_arguments(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Parse command line arguments.
        
        Args:
            args: Arguments to parse (None for sys.argv)
            
        Returns:
            Parsed arguments namespace
        """
        parser = argparse.ArgumentParser(
            description="智能抢购助手 - 自动化购买工具",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  %(prog)s --console                    # 控制台模式运行
  %(prog)s --test-ocr                   # 测试OCR识别
  %(prog)s --test-click                 # 测试点击位置
  %(prog)s --config config.json        # 使用指定配置文件
  %(prog)s --set countdown_box "[100,200,300,400]"  # 设置配置项
            """
        )
        
        # Mode selection
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument(
            '--console', 
            action='store_true',
            help='控制台模式运行（开始监控）'
        )
        mode_group.add_argument(
            '--gui', 
            action='store_true',
            help='图形界面模式运行（默认）'
        )
        
        # Testing options
        test_group = parser.add_mutually_exclusive_group()
        test_group.add_argument(
            '--test-ocr',
            action='store_true',
            help='测试OCR倒计时识别'
        )
        test_group.add_argument(
            '--test-click',
            action='store_true',
            help='测试购买按钮点击位置'
        )
        test_group.add_argument(
            '--validate-config',
            action='store_true',
            help='验证当前配置'
        )
        
        # Configuration options
        parser.add_argument(
            '--config', '-c',
            metavar='FILE',
            help='指定配置文件路径'
        )
        parser.add_argument(
            '--set',
            nargs=2,
            metavar=('KEY', 'VALUE'),
            action='append',
            help='设置配置项 (可多次使用)'
        )
        parser.add_argument(
            '--get',
            metavar='KEY',
            help='获取配置项值'
        )
        parser.add_argument(
            '--list-config',
            action='store_true',
            help='列出所有配置项'
        )
        
        # Output options
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='详细输出模式'
        )
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='静默模式（仅错误输出）'
        )
        
        # Monitoring options
        parser.add_argument(
            '--timeout',
            type=int,
            metavar='SECONDS',
            help='监控超时时间（秒）'
        )
        parser.add_argument(
            '--no-confirm',
            action='store_true',
            help='禁用确认按钮点击'
        )
        
        return parser.parse_args(args)
    
    def _execute_command(self, args: argparse.Namespace) -> int:
        """
        Execute the specified command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code
        """
        try:
            # Load custom config file if specified
            if args.config:
                if not self.config_manager.load_from_file(args.config):
                    self._print_error(f"无法加载配置文件: {args.config}")
                    return 1
                self._print_message(f"已加载配置文件: {args.config}")
            
            # Apply configuration overrides
            if args.set:
                for key, value in args.set:
                    if not self._set_config_value(key, value):
                        return 1
            
            # Apply command-line overrides
            if args.no_confirm:
                self.config_manager.set('enable_confirm_click', False)
            
            # Execute specific commands
            if args.test_ocr:
                return self._test_ocr()
            elif args.test_click:
                return self._test_click()
            elif args.validate_config:
                return self._validate_config()
            elif args.get:
                return self._get_config_value(args.get)
            elif args.list_config:
                return self._list_config()
            elif args.console:
                return self._run_console_mode(args.timeout)
            else:
                # Default to GUI mode
                return self._run_gui_mode()
                
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            self._print_error(f"命令执行失败: {e}")
            return 1
    
    def _run_console_mode(self, timeout: Optional[int] = None) -> int:
        """
        Run in console monitoring mode.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            Exit code
        """
        self._print_message("准备开始控制台监控模式...")
        
        try:
            # Validate configuration
            countdown_region = tuple(self.config_manager.get('countdown_box'))
            buy_button_pos = tuple(self.config_manager.get('buy_btn_pos'))
            confirm_button_pos = tuple(self.config_manager.get('confirm_btn_pos'))
            
            is_valid, errors = self.automation_engine.validate_configuration(
                countdown_region=countdown_region,
                buy_button_pos=buy_button_pos,
                confirm_button_pos=confirm_button_pos
            )
            
            if not is_valid:
                self._print_error("配置验证失败:")
                for error in errors:
                    self._print_error(f"  - {error}")
                return 1
            
            # Show configuration summary
            if self.verbose:
                self._print_config_summary()
            
            self._print_message("开始监控倒计时...")
            self._print_message("按 Ctrl+C 停止监控")
            
            # Start monitoring with timeout handling
            if timeout:
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"监控超时 ({timeout}秒)")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout)
            
            try:
                config = self.config_manager.get_all()
                
                self.automation_engine.start_monitoring(
                    countdown_region=tuple(config['countdown_box']),
                    countdown_formats=config['countdown_formats'],
                    buy_button_pos=tuple(config['buy_btn_pos']),
                    confirm_button_pos=tuple(config['confirm_btn_pos']) if config['enable_confirm_click'] else None,
                    check_interval=config['check_interval'],
                    click_delay=config['click_delay'],
                    max_retries=config['max_retries'],
                    enable_confirm_click=config['enable_confirm_click'],
                    callback=self._console_callback
                )
                
                # Check final state
                final_state = self.automation_engine.get_state()
                if final_state == AutomationState.COMPLETED:
                    self._print_message("✓ 购买操作完成！")
                    return 0
                elif final_state == AutomationState.ERROR:
                    self._print_error("✗ 自动化执行出错")
                    return 1
                elif final_state == AutomationState.STOPPED:
                    self._print_message("监控已停止")
                    return 0
                else:
                    return 0
                    
            finally:
                if timeout:
                    signal.alarm(0)  # Cancel timeout
                    
        except TimeoutError as e:
            self._print_error(str(e))
            return 124  # Standard timeout exit code
        except Exception as e:
            self.logger.error(f"Console mode failed: {e}")
            self._print_error(f"控制台模式执行失败: {e}")
            return 1
    
    def _run_gui_mode(self) -> int:
        """
        Run in GUI mode.
        
        Returns:
            Exit code
        """
        try:
            from .gui import GUIInterface
            gui = GUIInterface()
            gui.run()
            return 0
        except ImportError as e:
            self._print_error(f"GUI模式不可用: {e}")
            self._print_message("请使用 --console 参数运行控制台模式")
            return 1
        except Exception as e:
            self.logger.error(f"GUI mode failed: {e}")
            self._print_error(f"GUI模式执行失败: {e}")
            return 1
    
    def _test_ocr(self) -> int:
        """
        Test OCR countdown recognition.
        
        Returns:
            Exit code
        """
        self._print_message("测试OCR倒计时识别...")
        
        try:
            countdown_region = tuple(self.config_manager.get('countdown_box'))
            countdown_formats = self.config_manager.get('countdown_formats')
            
            self._print_message(f"倒计时区域: {countdown_region}")
            self._print_message("准备识别，请确保倒计时可见...")
            time.sleep(2)
            
            seconds = self.ocr_processor.read_countdown(
                region=countdown_region,
                countdown_formats=countdown_formats
            )
            
            if seconds is not None:
                formatted_time = format_time_remaining(seconds)
                self._print_message(f"✓ OCR识别成功: {seconds}秒 ({formatted_time})")
                return 0
            else:
                self._print_error("✗ OCR识别失败，请检查:")
                self._print_error("  - 倒计时区域设置是否正确")
                self._print_error("  - 倒计时是否清晰可见")
                self._print_error("  - Tesseract是否正确安装")
                return 1
                
        except Exception as e:
            self.logger.error(f"OCR test failed: {e}")
            self._print_error(f"OCR测试失败: {e}")
            return 1
    
    def _test_click(self) -> int:
        """
        Test button click positions.
        
        Returns:
            Exit code
        """
        self._print_message("测试按钮点击位置...")
        
        try:
            buy_button_pos = tuple(self.config_manager.get('buy_btn_pos'))
            confirm_button_pos = tuple(self.config_manager.get('confirm_btn_pos'))
            enable_confirm = self.config_manager.get('enable_confirm_click')
            
            self._print_message(f"购买按钮位置: {buy_button_pos}")
            self._print_message("3秒后测试购买按钮点击...")
            time.sleep(3)
            
            success = self.automation_engine.test_click_position(buy_button_pos)
            if success:
                self._print_message("✓ 购买按钮测试成功")
            else:
                self._print_error("✗ 购买按钮测试失败")
                return 1
            
            if enable_confirm:
                self._print_message(f"确认按钮位置: {confirm_button_pos}")
                self._print_message("3秒后测试确认按钮点击...")
                time.sleep(3)
                
                success = self.automation_engine.test_click_position(confirm_button_pos)
                if success:
                    self._print_message("✓ 确认按钮测试成功")
                else:
                    self._print_error("✗ 确认按钮测试失败")
                    return 1
            
            self._print_message("✓ 所有按钮测试完成")
            return 0
            
        except Exception as e:
            self.logger.error(f"Click test failed: {e}")
            self._print_error(f"点击测试失败: {e}")
            return 1
    
    def _validate_config(self) -> int:
        """
        Validate current configuration.
        
        Returns:
            Exit code
        """
        self._print_message("验证配置...")
        
        try:
            countdown_region = tuple(self.config_manager.get('countdown_box'))
            buy_button_pos = tuple(self.config_manager.get('buy_btn_pos'))
            confirm_button_pos = tuple(self.config_manager.get('confirm_btn_pos'))
            
            is_valid, errors = self.automation_engine.validate_configuration(
                countdown_region=countdown_region,
                buy_button_pos=buy_button_pos,
                confirm_button_pos=confirm_button_pos
            )
            
            if is_valid:
                self._print_message("✓ 配置验证通过")
                if self.verbose:
                    self._print_config_summary()
                return 0
            else:
                self._print_error("✗ 配置验证失败:")
                for error in errors:
                    self._print_error(f"  - {error}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Config validation failed: {e}")
            self._print_error(f"配置验证失败: {e}")
            return 1
    
    def _set_config_value(self, key: str, value: str) -> bool:
        """
        Set configuration value from string.
        
        Args:
            key: Configuration key
            value: String value to parse and set
            
        Returns:
            True if successful
        """
        try:
            # Parse value based on key type
            parsed_value = self._parse_config_value(key, value)
            
            success = self.config_manager.set(key, parsed_value)
            if success:
                self._print_message(f"配置已更新: {key} = {parsed_value}")
                return True
            else:
                self._print_error(f"配置更新失败: {key}")
                return False
                
        except Exception as e:
            self._print_error(f"配置值解析失败 {key}={value}: {e}")
            return False
    
    def _parse_config_value(self, key: str, value: str):
        """根据键类型从字符串解析配置值。"""
        # Handle list values (coordinates)
        if key in ['countdown_box', 'buy_btn_pos', 'confirm_btn_pos']:
            from ..utils.helpers import parse_coordinate_string
            return parse_coordinate_string(value)
        
        # Handle boolean values
        if key in ['enable_confirm_click', 'enable_console_logging']:
            return value.lower() in ('true', '1', 'yes', 'on')
        
        # Handle numeric values
        if key in ['check_interval', 'click_delay']:
            return float(value)
        
        if key in ['max_retries', 'min_countdown_value', 'max_countdown_value']:
            return int(value)
        
        # Handle string values
        return value
    
    def _get_config_value(self, key: str) -> int:
        """
        Get and display configuration value.
        
        Args:
            key: Configuration key
            
        Returns:
            Exit code
        """
        try:
            value = self.config_manager.get(key)
            if value is not None:
                self._print_message(f"{key} = {value}")
                return 0
            else:
                self._print_error(f"配置项不存在: {key}")
                return 1
        except Exception as e:
            self._print_error(f"获取配置失败: {e}")
            return 1
    
    def _list_config(self) -> int:
        """
        List all configuration values.
        
        Returns:
            Exit code
        """
        try:
            config = self.config_manager.get_all()
            self._print_message("当前配置:")
            
            for key, value in sorted(config.items()):
                self._print_message(f"  {key} = {value}")
            
            return 0
        except Exception as e:
            self._print_error(f"列出配置失败: {e}")
            return 1
    
    def _print_config_summary(self) -> None:
        """打印配置摘要。"""
        config = self.config_manager.get_all()
        
        self._print_message("配置摘要:")
        self._print_message(f"  倒计时区域: {config['countdown_box']}")
        self._print_message(f"  购买按钮: {config['buy_btn_pos']}")
        self._print_message(f"  确认按钮: {config['confirm_btn_pos']}")
        self._print_message(f"  检查间隔: {config['check_interval']}秒")
        self._print_message(f"  启用确认点击: {config['enable_confirm_click']}")
    
    def _console_callback(self, message: str) -> None:
        """
        Callback for console status updates.
        
        Args:
            message: Status message
        """
        self._print_message(message)
    
    def _print_message(self, message: str) -> None:
        """如果不在静默模式下则打印消息。"""
        if not self.quiet:
            print(message)
    
    def _print_error(self, message: str) -> None:
        """将错误消息打印到stderr。"""
        print(f"错误: {message}", file=sys.stderr)