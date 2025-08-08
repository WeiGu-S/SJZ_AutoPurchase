"""
Unit tests for CLI interface functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import io
from smart_buyer.ui.cli import CLIInterface
from smart_buyer.config.manager import ConfigManager
from smart_buyer.core.ocr import OCRProcessor
from smart_buyer.core.automation import AutomationEngine, AutomationState


class TestCLIInterface(unittest.TestCase):
    """Test cases for CLIInterface class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the dependencies
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_ocr_processor = Mock(spec=OCRProcessor)
        self.mock_automation_engine = Mock(spec=AutomationEngine)
        
        # Set up default config values
        self.default_config = {
            'countdown_box': [100, 200, 300, 240],
            'buy_btn_pos': [500, 600],
            'confirm_btn_pos': [550, 650],
            'check_interval': 0.1,
            'tesseract_path': '',
            'enable_confirm_click': True,
            'log_file': '抢购日志.log',
            'ocr_config': '--psm 8',
            'countdown_formats': [r'(\d{1,2}):(\d{2}):(\d{2})'],
            'click_delay': 0.05,
            'max_retries': 3
        }
        
        self.mock_config_manager.get_all.return_value = self.default_config
        self.mock_config_manager.get.side_effect = lambda key, default=None: \
            self.default_config.get(key, default)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_init_cli_interface(self, mock_config, mock_ocr, mock_automation):
        """Test CLI interface initialization."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        
        # Verify components were created
        self.assertIsNotNone(cli.config_manager)
        self.assertIsNotNone(cli.ocr_processor)
        self.assertIsNotNone(cli.automation_engine)
        self.assertFalse(cli.verbose)
        self.assertFalse(cli.quiet)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_parse_arguments_console_mode(self, mock_config, mock_ocr, mock_automation):
        """Test parsing console mode arguments."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        args = cli._parse_arguments(['--console'])
        
        self.assertTrue(args.console)
        self.assertFalse(args.gui)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_parse_arguments_test_ocr(self, mock_config, mock_ocr, mock_automation):
        """Test parsing OCR test arguments."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        args = cli._parse_arguments(['--test-ocr'])
        
        self.assertTrue(args.test_ocr)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_parse_arguments_config_options(self, mock_config, mock_ocr, mock_automation):
        """Test parsing configuration options."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        args = cli._parse_arguments([
            '--config', 'test.json',
            '--set', 'check_interval', '0.2',
            '--set', 'max_retries', '5',
            '--verbose'
        ])
        
        self.assertEqual(args.config, 'test.json')
        self.assertEqual(args.set, [['check_interval', '0.2'], ['max_retries', '5']])
        self.assertTrue(args.verbose)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_parse_config_value_coordinates(self, mock_config, mock_ocr, mock_automation):
        """Test parsing coordinate configuration values."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        
        # Test bounding box
        result = cli._parse_config_value('countdown_box', '[100,200,300,400]')
        self.assertEqual(result, [100, 200, 300, 400])
        
        # Test point coordinates
        result = cli._parse_config_value('buy_btn_pos', '[500,600]')
        self.assertEqual(result, [500, 600])
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_parse_config_value_boolean(self, mock_config, mock_ocr, mock_automation):
        """Test parsing boolean configuration values."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        
        # Test true values
        for value in ['true', '1', 'yes', 'on']:
            result = cli._parse_config_value('enable_confirm_click', value)
            self.assertTrue(result)
        
        # Test false values
        for value in ['false', '0', 'no', 'off']:
            result = cli._parse_config_value('enable_confirm_click', value)
            self.assertFalse(result)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_parse_config_value_numeric(self, mock_config, mock_ocr, mock_automation):
        """Test parsing numeric configuration values."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        
        # Test float values
        result = cli._parse_config_value('check_interval', '0.5')
        self.assertEqual(result, 0.5)
        
        # Test integer values
        result = cli._parse_config_value('max_retries', '10')
        self.assertEqual(result, 10)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_set_config_value_success(self, mock_config, mock_ocr, mock_automation):
        """Test successful configuration value setting."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock successful set
        self.mock_config_manager.set.return_value = True
        
        cli = CLIInterface()
        cli.quiet = True  # Suppress output for testing
        
        result = cli._set_config_value('check_interval', '0.2')
        
        self.assertTrue(result)
        self.mock_config_manager.set.assert_called_once_with('check_interval', 0.2)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_set_config_value_failure(self, mock_config, mock_ocr, mock_automation):
        """Test configuration value setting failure."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock failed set
        self.mock_config_manager.set.return_value = False
        
        cli = CLIInterface()
        
        with patch('sys.stderr', new_callable=io.StringIO):
            result = cli._set_config_value('check_interval', '0.2')
        
        self.assertFalse(result)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_get_config_value_success(self, mock_config, mock_ocr, mock_automation):
        """Test successful configuration value retrieval."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = cli._get_config_value('check_interval')
        
        self.assertEqual(result, 0)
        self.assertIn('check_interval = 0.1', mock_stdout.getvalue())
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_get_config_value_not_found(self, mock_config, mock_ocr, mock_automation):
        """Test configuration value retrieval for non-existent key."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock get to return None for non-existent key
        self.mock_config_manager.get.return_value = None
        
        cli = CLIInterface()
        
        with patch('sys.stderr', new_callable=io.StringIO):
            result = cli._get_config_value('nonexistent_key')
        
        self.assertEqual(result, 1)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_list_config(self, mock_config, mock_ocr, mock_automation):
        """Test configuration listing."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = cli._list_config()
        
        self.assertEqual(result, 0)
        output = mock_stdout.getvalue()
        self.assertIn('当前配置:', output)
        self.assertIn('check_interval = 0.1', output)
    
    @patch('smart_buyer.ui.cli.time.sleep')
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_test_ocr_success(self, mock_config, mock_ocr, mock_automation, mock_sleep):
        """Test successful OCR testing."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock successful OCR
        self.mock_ocr_processor.read_countdown.return_value = 30
        
        cli = CLIInterface()
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = cli._test_ocr()
        
        self.assertEqual(result, 0)
        output = mock_stdout.getvalue()
        self.assertIn('OCR识别成功', output)
        self.assertIn('30秒', output)
    
    @patch('smart_buyer.ui.cli.time.sleep')
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_test_ocr_failure(self, mock_config, mock_ocr, mock_automation, mock_sleep):
        """Test OCR testing failure."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock failed OCR
        self.mock_ocr_processor.read_countdown.return_value = None
        
        cli = CLIInterface()
        
        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            result = cli._test_ocr()
        
        self.assertEqual(result, 1)
        output = mock_stderr.getvalue()
        self.assertIn('OCR识别失败', output)
    
    @patch('smart_buyer.ui.cli.time.sleep')
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_test_click_success(self, mock_config, mock_ocr, mock_automation, mock_sleep):
        """Test successful click testing."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock successful click tests
        self.mock_automation_engine.test_click_position.return_value = True
        
        cli = CLIInterface()
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = cli._test_click()
        
        self.assertEqual(result, 0)
        output = mock_stdout.getvalue()
        self.assertIn('购买按钮测试成功', output)
        self.assertIn('确认按钮测试成功', output)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_validate_config_success(self, mock_config, mock_ocr, mock_automation):
        """Test successful configuration validation."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock successful validation
        self.mock_automation_engine.validate_configuration.return_value = (True, [])
        
        cli = CLIInterface()
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = cli._validate_config()
        
        self.assertEqual(result, 0)
        output = mock_stdout.getvalue()
        self.assertIn('配置验证通过', output)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_validate_config_failure(self, mock_config, mock_ocr, mock_automation):
        """Test configuration validation failure."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock failed validation
        self.mock_automation_engine.validate_configuration.return_value = (False, ["错误1", "错误2"])
        
        cli = CLIInterface()
        
        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            result = cli._validate_config()
        
        self.assertEqual(result, 1)
        output = mock_stderr.getvalue()
        self.assertIn('配置验证失败', output)
        self.assertIn('错误1', output)
        self.assertIn('错误2', output)
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_print_message_normal_mode(self, mock_config, mock_ocr, mock_automation):
        """Test message printing in normal mode."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        cli.quiet = False
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            cli._print_message("测试消息")
        
        self.assertEqual(mock_stdout.getvalue().strip(), "测试消息")
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_print_message_quiet_mode(self, mock_config, mock_ocr, mock_automation):
        """Test message printing in quiet mode."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        cli.quiet = True
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            cli._print_message("测试消息")
        
        self.assertEqual(mock_stdout.getvalue(), "")
    
    @patch('smart_buyer.ui.cli.AutomationEngine')
    @patch('smart_buyer.ui.cli.OCRProcessor')
    @patch('smart_buyer.ui.cli.ConfigManager')
    def test_print_error(self, mock_config, mock_ocr, mock_automation):
        """Test error message printing."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        cli = CLIInterface()
        
        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            cli._print_error("测试错误")
        
        self.assertEqual(mock_stderr.getvalue().strip(), "错误: 测试错误")


if __name__ == '__main__':
    unittest.main()