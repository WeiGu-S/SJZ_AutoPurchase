"""
智能抢购助手的自动化引擎模块。

此模块处理核心自动化逻辑，包括倒计时监控、
购买执行和带回调支持的状态管理。
"""

import time
import pyautogui
from typing import Optional, Callable, Tuple, List
from enum import Enum
from ..core.exceptions import AutomationError
from ..core.ocr import OCRProcessor
from ..utils.logging import get_logger


class AutomationState(Enum):
    """自动化引擎状态枚举。"""
    IDLE = "idle"
    MONITORING = "monitoring"
    EXECUTING = "executing"
    COMPLETED = "completed"
    STOPPED = "stopped"
    ERROR = "error"


class AutomationEngine:
    """用于购买执行的核心自动化引擎。"""
    
    def __init__(self, ocr_processor: OCRProcessor):
        """
        初始化自动化引擎。
        
        参数:
            ocr_processor: 用于倒计时识别的OCR处理器实例
        """
        self.logger = get_logger(__name__)
        self.ocr_processor = ocr_processor
        self.state = AutomationState.IDLE
        self._is_running = False
        self._callback = None
    
    def start_monitoring(
        self,
        countdown_region: Tuple[int, int, int, int],
        countdown_formats: List[str],
        buy_button_pos: Tuple[int, int],
        confirm_button_pos: Optional[Tuple[int, int]] = None,
        check_interval: float = 0.1,
        click_delay: float = 0.05,
        max_retries: int = 3,
        enable_confirm_click: bool = True,
        callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Start countdown monitoring and automated purchase execution.
        
        Args:
            countdown_region: Screen region for countdown detection
            countdown_formats: List of regex patterns for countdown formats
            buy_button_pos: Position of buy button (x, y)
            confirm_button_pos: Position of confirm button (x, y), optional
            check_interval: Interval between countdown checks in seconds
            click_delay: Delay between clicks in seconds
            max_retries: Maximum retries for OCR recognition failures
            enable_confirm_click: Whether to click confirm button after buy
            callback: Optional callback function for status updates
        """
        if self._is_running:
            raise AutomationError("Automation engine is already running")
        
        self.logger.info("Starting countdown monitoring...")
        self.state = AutomationState.MONITORING
        self._is_running = True
        self._callback = callback
        
        try:
            self._monitor_countdown(
                countdown_region=countdown_region,
                countdown_formats=countdown_formats,
                check_interval=check_interval,
                max_retries=max_retries
            )
            
            if self._is_running:  # Only execute if not stopped
                self._execute_purchase(
                    buy_button_pos=buy_button_pos,
                    confirm_button_pos=confirm_button_pos,
                    click_delay=click_delay,
                    enable_confirm_click=enable_confirm_click
                )
                
        except Exception as e:
            self.state = AutomationState.ERROR
            self.logger.error(f"Automation failed: {e}")
            self._notify_callback(f"自动化执行失败: {e}")
            raise AutomationError(f"Automation execution failed: {str(e)}")
        
        finally:
            self._is_running = False
    
    def stop_monitoring(self) -> None:
        """停止自动化引擎。"""
        if self._is_running:
            self.logger.info("正在停止自动化引擎...")
            self._is_running = False
            self.state = AutomationState.STOPPED
            self._notify_callback("监控已停止")
    
    def _monitor_countdown(
        self,
        countdown_region: Tuple[int, int, int, int],
        countdown_formats: List[str],
        check_interval: float,
        max_retries: int
    ) -> None:
        """
        Monitor countdown until it reaches zero or monitoring is stopped.
        
        Args:
            countdown_region: Screen region for countdown detection
            countdown_formats: List of regex patterns for countdown formats
            check_interval: Interval between checks in seconds
            max_retries: Maximum consecutive failures allowed
        """
        retry_count = 0
        
        while self._is_running:
            try:
                # Read countdown value
                seconds_remaining = self.ocr_processor.read_countdown(
                    region=countdown_region,
                    countdown_formats=countdown_formats,
                    enable_preprocessing=True
                )
                
                # Update status
                if seconds_remaining is not None:
                    self._notify_callback(f"剩余时间: {seconds_remaining}秒")
                    self.logger.info(f"Countdown: {seconds_remaining} seconds remaining")
                    retry_count = 0  # Reset retry count on successful read
                    
                    # Check if countdown has ended
                    if seconds_remaining <= 0:
                        self.logger.info("Countdown reached zero, proceeding to purchase")
                        break
                        
                    # Wait for next check (but not longer than remaining time)
                    sleep_time = min(check_interval, seconds_remaining)
                    time.sleep(sleep_time)
                    
                else:
                    # OCR failed
                    retry_count += 1
                    self._notify_callback(f"倒计时识别失败 (重试 {retry_count}/{max_retries})")
                    self.logger.warning(f"OCR failed, retry {retry_count}/{max_retries}")
                    
                    if retry_count >= max_retries:
                        self.logger.warning("Max retries reached, assuming countdown ended")
                        self._notify_callback("连续识别失败，可能倒计时已结束")
                        break
                    
                    time.sleep(check_interval)
                    
            except Exception as e:
                self.logger.error(f"Error during countdown monitoring: {e}")
                self._notify_callback(f"监控过程出错: {e}")
                time.sleep(check_interval)
    
    def _execute_purchase(
        self,
        buy_button_pos: Tuple[int, int],
        confirm_button_pos: Optional[Tuple[int, int]],
        click_delay: float,
        enable_confirm_click: bool
    ) -> None:
        """
        Execute the purchase sequence.
        
        Args:
            buy_button_pos: Position of buy button
            confirm_button_pos: Position of confirm button (optional)
            click_delay: Delay between clicks
            enable_confirm_click: Whether to click confirm button
        """
        if not self._is_running:
            return
        
        self.state = AutomationState.EXECUTING
        self.logger.info("Executing purchase sequence...")
        self._notify_callback("正在执行购买操作...")
        
        try:
            # Click buy button
            self._click_button(buy_button_pos, "购买按钮", click_delay)
            
            # Click confirm button if enabled and position provided
            if enable_confirm_click and confirm_button_pos:
                time.sleep(click_delay)
                self._click_button(confirm_button_pos, "确认按钮", click_delay)
            
            self.state = AutomationState.COMPLETED
            self.logger.info("Purchase sequence completed successfully")
            self._notify_callback("购买操作完成！")
            
        except Exception as e:
            self.state = AutomationState.ERROR
            error_msg = f"Purchase execution failed: {str(e)}"
            self.logger.error(error_msg)
            self._notify_callback(f"购买操作失败: {e}")
            raise AutomationError(error_msg, "purchase_execution")
    
    def _click_button(self, position: Tuple[int, int], button_name: str, delay: float) -> None:
        """
        在指定位置点击按钮。
        
        Args:
            position: 按钮位置 (x, y)
            button_name: 按钮名称（用于日志记录）
            delay: 移动延迟
            
        Raises:
            AutomationError: 如果点击操作失败
        """
        try:
            x, y = position
            self.logger.info(f"Clicking {button_name} at position ({x}, {y})")
            
            # Move to position and click
            pyautogui.moveTo(x, y, duration=delay)
            pyautogui.click()
            
            self.logger.info(f"Successfully clicked {button_name}")
            
        except Exception as e:
            error_msg = f"Failed to click {button_name} at {position}: {str(e)}"
            self.logger.error(error_msg)
            raise AutomationError(error_msg, f"click_{button_name}")
    
    def _notify_callback(self, message: str) -> None:
        """
        通过回调函数发送状态消息。
        
        Args:
            message: 要发送的状态消息
        """
        if self._callback:
            try:
                self._callback(message)
            except Exception as e:
                self.logger.warning(f"Callback notification failed: {e}")
    
    def get_state(self) -> AutomationState:
        """
        获取当前自动化状态。
        
        Returns:
            当前自动化状态
        """
        return self.state
    
    def is_running(self) -> bool:
        """
        检查自动化引擎是否正在运行。
        
        Returns:
            如果正在运行返回True，否则返回False
        """
        return self._is_running
    
    def test_click_position(self, position: Tuple[int, int], delay: float = 0.05) -> bool:
        """
        测试在特定位置点击（用于配置测试）。
        
        Args:
            position: 要测试点击的位置 (x, y)
            delay: 移动延迟
            
        Returns:
            成功返回True，否则返回False
        """
        try:
            self.logger.info(f"Testing click at position {position}")
            self._click_button(position, "测试位置", delay)
            return True
        except Exception as e:
            self.logger.error(f"Test click failed: {e}")
            return False
    
    def validate_configuration(
        self,
        countdown_region: Tuple[int, int, int, int],
        buy_button_pos: Tuple[int, int],
        confirm_button_pos: Optional[Tuple[int, int]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate automation configuration.
        
        Args:
            countdown_region: Screen region for countdown detection
            buy_button_pos: Buy button position
            confirm_button_pos: Confirm button position (optional)
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate countdown region
        if len(countdown_region) != 4:
            errors.append("倒计时区域必须包含4个坐标值")
        else:
            left, top, right, bottom = countdown_region
            if left >= right or top >= bottom:
                errors.append("倒计时区域坐标无效")
            if any(coord < 0 for coord in countdown_region):
                errors.append("倒计时区域坐标不能为负数")
        
        # Validate button positions
        if len(buy_button_pos) != 2:
            errors.append("购买按钮位置必须包含2个坐标值")
        elif any(coord < 0 for coord in buy_button_pos):
            errors.append("购买按钮坐标不能为负数")
        
        if confirm_button_pos:
            if len(confirm_button_pos) != 2:
                errors.append("确认按钮位置必须包含2个坐标值")
            elif any(coord < 0 for coord in confirm_button_pos):
                errors.append("确认按钮坐标不能为负数")
        
        is_valid = len(errors) == 0
        return is_valid, errors