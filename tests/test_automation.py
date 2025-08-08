"""
Unit tests for automation engine functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from smart_buyer.core.automation import AutomationEngine, AutomationState
from smart_buyer.core.ocr import OCRProcessor
from smart_buyer.core.exceptions import AutomationError


class TestAutomationEngine(unittest.TestCase):
    """Test cases for AutomationEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_ocr = Mock(spec=OCRProcessor)
        self.automation_engine = AutomationEngine(self.mock_ocr)
        
        # Test configuration
        self.countdown_region = (100, 200, 300, 400)
        self.countdown_formats = [r'(\d{1,2}):(\d{2}):(\d{2})']
        self.buy_button_pos = (500, 600)
        self.confirm_button_pos = (550, 650)
    
    def test_initial_state(self):
        """Test initial state of automation engine."""
        self.assertEqual(self.automation_engine.get_state(), AutomationState.IDLE)
        self.assertFalse(self.automation_engine.is_running())
    
    def test_validate_configuration_valid(self):
        """Test configuration validation with valid parameters."""
        is_valid, errors = self.automation_engine.validate_configuration(
            countdown_region=self.countdown_region,
            buy_button_pos=self.buy_button_pos,
            confirm_button_pos=self.confirm_button_pos
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_configuration_invalid_region(self):
        """Test configuration validation with invalid countdown region."""
        invalid_region = (300, 200, 100, 400)  # left > right
        is_valid, errors = self.automation_engine.validate_configuration(
            countdown_region=invalid_region,
            buy_button_pos=self.buy_button_pos
        )
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_validate_configuration_negative_coordinates(self):
        """Test configuration validation with negative coordinates."""
        invalid_pos = (-100, 200)
        is_valid, errors = self.automation_engine.validate_configuration(
            countdown_region=self.countdown_region,
            buy_button_pos=invalid_pos
        )
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_validate_configuration_wrong_length(self):
        """Test configuration validation with wrong coordinate lengths."""
        invalid_region = (100, 200, 300)  # Missing one coordinate
        is_valid, errors = self.automation_engine.validate_configuration(
            countdown_region=invalid_region,
            buy_button_pos=self.buy_button_pos
        )
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    @patch('smart_buyer.core.automation.pyautogui.moveTo')
    @patch('smart_buyer.core.automation.pyautogui.click')
    def test_click_button_success(self, mock_click, mock_move):
        """Test successful button clicking."""
        position = (500, 600)
        self.automation_engine._click_button(position, "测试按钮", 0.05)
        
        mock_move.assert_called_once_with(500, 600, duration=0.05)
        mock_click.assert_called_once()
    
    @patch('smart_buyer.core.automation.pyautogui.moveTo')
    def test_click_button_failure(self, mock_move):
        """Test button clicking failure."""
        mock_move.side_effect = Exception("Mouse movement failed")
        
        with self.assertRaises(AutomationError):
            self.automation_engine._click_button((500, 600), "测试按钮", 0.05)
    
    @patch('smart_buyer.core.automation.pyautogui.moveTo')
    @patch('smart_buyer.core.automation.pyautogui.click')
    def test_test_click_position_success(self, mock_click, mock_move):
        """Test successful position click testing."""
        result = self.automation_engine.test_click_position((500, 600))
        self.assertTrue(result)
        mock_move.assert_called_once()
        mock_click.assert_called_once()
    
    @patch('smart_buyer.core.automation.pyautogui.moveTo')
    def test_test_click_position_failure(self, mock_move):
        """Test position click testing failure."""
        mock_move.side_effect = Exception("Test failed")
        
        result = self.automation_engine.test_click_position((500, 600))
        self.assertFalse(result)
    
    def test_stop_monitoring_when_not_running(self):
        """Test stopping monitoring when not running."""
        # Should not raise an exception
        self.automation_engine.stop_monitoring()
        self.assertEqual(self.automation_engine.get_state(), AutomationState.IDLE)
    
    def test_start_monitoring_when_already_running(self):
        """Test starting monitoring when already running."""
        self.automation_engine._is_running = True
        
        with self.assertRaises(AutomationError):
            self.automation_engine.start_monitoring(
                countdown_region=self.countdown_region,
                countdown_formats=self.countdown_formats,
                buy_button_pos=self.buy_button_pos
            )
    
    def test_notify_callback_success(self):
        """Test successful callback notification."""
        callback_mock = Mock()
        self.automation_engine._callback = callback_mock
        
        self.automation_engine._notify_callback("测试消息")
        callback_mock.assert_called_once_with("测试消息")
    
    def test_notify_callback_failure(self):
        """Test callback notification failure handling."""
        callback_mock = Mock()
        callback_mock.side_effect = Exception("Callback failed")
        self.automation_engine._callback = callback_mock
        
        # Should not raise exception, just log warning
        self.automation_engine._notify_callback("测试消息")
    
    def test_notify_callback_none(self):
        """Test callback notification when callback is None."""
        self.automation_engine._callback = None
        
        # Should not raise exception
        self.automation_engine._notify_callback("测试消息")
    
    @patch('smart_buyer.core.automation.time.sleep')
    def test_monitor_countdown_success(self, mock_sleep):
        """Test successful countdown monitoring."""
        # Mock OCR to return decreasing countdown values
        self.mock_ocr.read_countdown.side_effect = [10, 5, 1, 0]
        
        # Mock the automation engine to stop after countdown reaches 0
        original_monitor = self.automation_engine._monitor_countdown
        
        def mock_monitor(*args, **kwargs):
            self.automation_engine._is_running = True
            original_monitor(*args, **kwargs)
            self.automation_engine._is_running = False
        
        with patch.object(self.automation_engine, '_monitor_countdown', side_effect=mock_monitor):
            # This should complete without raising an exception
            pass
    
    def test_monitor_countdown_ocr_failure(self):
        """Test countdown monitoring with OCR failures."""
        # Mock OCR to return None (failure) multiple times
        self.mock_ocr.read_countdown.return_value = None
        
        self.automation_engine._is_running = True
        
        # Should handle failures gracefully and eventually break
        with patch('smart_buyer.core.automation.time.sleep'):
            self.automation_engine._monitor_countdown(
                countdown_region=self.countdown_region,
                countdown_formats=self.countdown_formats,
                check_interval=0.1,
                max_retries=2
            )
    
    @patch('smart_buyer.core.automation.pyautogui.moveTo')
    @patch('smart_buyer.core.automation.pyautogui.click')
    @patch('smart_buyer.core.automation.time.sleep')
    def test_execute_purchase_success(self, mock_sleep, mock_click, mock_move):
        """Test successful purchase execution."""
        self.automation_engine._is_running = True
        
        self.automation_engine._execute_purchase(
            buy_button_pos=self.buy_button_pos,
            confirm_button_pos=self.confirm_button_pos,
            click_delay=0.05,
            enable_confirm_click=True
        )
        
        # Should click both buy and confirm buttons
        self.assertEqual(mock_move.call_count, 2)
        self.assertEqual(mock_click.call_count, 2)
        self.assertEqual(self.automation_engine.get_state(), AutomationState.COMPLETED)
    
    @patch('smart_buyer.core.automation.pyautogui.moveTo')
    @patch('smart_buyer.core.automation.pyautogui.click')
    def test_execute_purchase_without_confirm(self, mock_click, mock_move):
        """Test purchase execution without confirm button."""
        self.automation_engine._is_running = True
        
        self.automation_engine._execute_purchase(
            buy_button_pos=self.buy_button_pos,
            confirm_button_pos=None,
            click_delay=0.05,
            enable_confirm_click=False
        )
        
        # Should only click buy button
        self.assertEqual(mock_move.call_count, 1)
        self.assertEqual(mock_click.call_count, 1)
    
    def test_execute_purchase_when_stopped(self):
        """Test purchase execution when automation is stopped."""
        self.automation_engine._is_running = False
        
        # Should return early without doing anything
        self.automation_engine._execute_purchase(
            buy_button_pos=self.buy_button_pos,
            confirm_button_pos=None,
            click_delay=0.05,
            enable_confirm_click=False
        )
        
        # State should remain idle
        self.assertEqual(self.automation_engine.get_state(), AutomationState.IDLE)
    
    @patch('smart_buyer.core.automation.pyautogui.moveTo')
    def test_execute_purchase_failure(self, mock_move):
        """Test purchase execution failure."""
        mock_move.side_effect = Exception("Click failed")
        self.automation_engine._is_running = True
        
        with self.assertRaises(AutomationError):
            self.automation_engine._execute_purchase(
                buy_button_pos=self.buy_button_pos,
                confirm_button_pos=None,
                click_delay=0.05,
                enable_confirm_click=False
            )
        
        self.assertEqual(self.automation_engine.get_state(), AutomationState.ERROR)


if __name__ == '__main__':
    unittest.main()