"""
Unit tests for GUI interface functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from smart_buyer.ui.gui import GUIInterface
from smart_buyer.config.manager import ConfigManager
from smart_buyer.core.ocr import OCRProcessor
from smart_buyer.core.automation import AutomationEngine


class TestGUIInterface(unittest.TestCase):
    """Test cases for GUIInterface class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the dependencies to avoid actual GUI creation
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_ocr_processor = Mock(spec=OCRProcessor)
        self.mock_automation_engine = Mock(spec=AutomationEngine)
        
        # Set up default config values
        self.mock_config_manager.get_all.return_value = {
            'countdown_box': [100, 200, 300, 240],
            'buy_btn_pos': [500, 600],
            'confirm_btn_pos': [550, 650],
            'check_interval': 0.1,
            'tesseract_path': '',
            'enable_confirm_click': True,
            'window_title': '智能抢购助手',
            'window_geometry': '600x500',
            'countdown_formats': [r'(\d{1,2}):(\d{2}):(\d{2})'],
            'ocr_config': '--psm 8',
            'click_delay': 0.05,
            'max_retries': 3
        }
        
        self.mock_config_manager.get.side_effect = lambda key, default=None: \
            self.mock_config_manager.get_all.return_value.get(key, default)
    
    @patch('smart_buyer.ui.gui.AutomationEngine')
    @patch('smart_buyer.ui.gui.OCRProcessor')
    @patch('smart_buyer.ui.gui.ConfigManager')
    @patch('smart_buyer.ui.gui.tk.Tk')
    def test_init_gui_interface(self, mock_tk, mock_config, mock_ocr, mock_automation):
        """Test GUI interface initialization."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock root window
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        gui = GUIInterface()
        
        # Verify components were created
        self.assertIsNotNone(gui.config_manager)
        self.assertIsNotNone(gui.ocr_processor)
        self.assertIsNotNone(gui.automation_engine)
        
        # Verify root window setup
        mock_root.title.assert_called()
        mock_root.geometry.assert_called()
    
    def test_parse_coordinate_string_valid(self):
        """Test parsing valid coordinate strings."""
        from smart_buyer.utils.helpers import parse_coordinate_string
        
        # Test bounding box format
        result = parse_coordinate_string("[100, 200, 300, 400]")
        self.assertEqual(result, [100, 200, 300, 400])
        
        # Test point format
        result = parse_coordinate_string("[500, 600]")
        self.assertEqual(result, [500, 600])
        
        # Test without brackets
        result = parse_coordinate_string("100, 200")
        self.assertEqual(result, [100, 200])
    
    def test_parse_coordinate_string_invalid(self):
        """Test parsing invalid coordinate strings."""
        from smart_buyer.utils.helpers import parse_coordinate_string
        from smart_buyer.core.exceptions import ValidationError
        
        with self.assertRaises(ValidationError):
            parse_coordinate_string("invalid")
        
        with self.assertRaises(ValidationError):
            parse_coordinate_string("")
        
        with self.assertRaises(ValidationError):
            parse_coordinate_string("[]")
    
    @patch('smart_buyer.ui.gui.AutomationEngine')
    @patch('smart_buyer.ui.gui.OCRProcessor')
    @patch('smart_buyer.ui.gui.ConfigManager')
    @patch('smart_buyer.ui.gui.tk.Tk')
    def test_save_current_config_success(self, mock_tk, mock_config, mock_ocr, mock_automation):
        """Test successful configuration saving."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock successful update
        self.mock_config_manager.update.return_value = True
        
        # Mock root and create GUI
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        gui = GUIInterface()
        
        # Set up GUI variables with valid values
        gui.countdown_box_var = Mock()
        gui.countdown_box_var.get.return_value = "[100, 200, 300, 400]"
        gui.buy_btn_var = Mock()
        gui.buy_btn_var.get.return_value = "[500, 600]"
        gui.confirm_btn_var = Mock()
        gui.confirm_btn_var.get.return_value = "[550, 650]"
        gui.check_interval_var = Mock()
        gui.check_interval_var.get.return_value = "0.1"
        gui.tesseract_path_var = Mock()
        gui.tesseract_path_var.get.return_value = ""
        gui.enable_confirm_var = Mock()
        gui.enable_confirm_var.get.return_value = True
        
        # Mock status update method
        gui._update_status = Mock()
        
        result = gui._save_current_config()
        
        self.assertTrue(result)
        self.mock_config_manager.update.assert_called_once()
    
    @patch('smart_buyer.ui.gui.AutomationEngine')
    @patch('smart_buyer.ui.gui.OCRProcessor')
    @patch('smart_buyer.ui.gui.ConfigManager')
    @patch('smart_buyer.ui.gui.tk.Tk')
    def test_save_current_config_invalid_values(self, mock_tk, mock_config, mock_ocr, mock_automation):
        """Test configuration saving with invalid values."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock root and create GUI
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        gui = GUIInterface()
        
        # Set up GUI variables with invalid values
        gui.countdown_box_var = Mock()
        gui.countdown_box_var.get.return_value = "invalid"
        gui.buy_btn_var = Mock()
        gui.buy_btn_var.get.return_value = "[500, 600]"
        gui.confirm_btn_var = Mock()
        gui.confirm_btn_var.get.return_value = "[550, 650]"
        gui.check_interval_var = Mock()
        gui.check_interval_var.get.return_value = "0.1"
        gui.tesseract_path_var = Mock()
        gui.tesseract_path_var.get.return_value = ""
        gui.enable_confirm_var = Mock()
        gui.enable_confirm_var.get.return_value = True
        
        # Mock status update method
        gui._update_status = Mock()
        
        result = gui._save_current_config()
        
        self.assertFalse(result)
        gui._update_status.assert_called()
    
    @patch('smart_buyer.ui.gui.get_mouse_position_after_delay')
    @patch('smart_buyer.ui.gui.threading.Thread')
    @patch('smart_buyer.ui.gui.AutomationEngine')
    @patch('smart_buyer.ui.gui.OCRProcessor')
    @patch('smart_buyer.ui.gui.ConfigManager')
    @patch('smart_buyer.ui.gui.tk.Tk')
    def test_get_mouse_position(self, mock_tk, mock_config, mock_ocr, mock_automation, mock_thread, mock_get_pos):
        """Test mouse position retrieval."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock root and create GUI
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        gui = GUIInterface()
        gui._update_status = Mock()
        
        # Mock mouse position
        mock_get_pos.return_value = (100, 200)
        
        gui._get_mouse_position()
        
        # Verify thread was started
        mock_thread.assert_called_once()
        gui._update_status.assert_called_with("请将鼠标移动到目标位置，3秒后获取坐标...")
    
    @patch('smart_buyer.ui.gui.threading.Thread')
    @patch('smart_buyer.ui.gui.AutomationEngine')
    @patch('smart_buyer.ui.gui.OCRProcessor')
    @patch('smart_buyer.ui.gui.ConfigManager')
    @patch('smart_buyer.ui.gui.tk.Tk')
    def test_test_countdown(self, mock_tk, mock_config, mock_ocr, mock_automation, mock_thread):
        """Test countdown recognition testing."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock root and create GUI
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        gui = GUIInterface()
        gui._save_current_config = Mock(return_value=True)
        gui._update_status = Mock()
        
        # Mock OCR result
        self.mock_ocr_processor.read_countdown.return_value = 30
        
        gui._test_countdown()
        
        # Verify thread was started
        mock_thread.assert_called_once()
        gui._save_current_config.assert_called_once()
    
    @patch('smart_buyer.ui.gui.AutomationEngine')
    @patch('smart_buyer.ui.gui.OCRProcessor')
    @patch('smart_buyer.ui.gui.ConfigManager')
    @patch('smart_buyer.ui.gui.tk.Tk')
    def test_test_buy_button(self, mock_tk, mock_config, mock_ocr, mock_automation):
        """Test buy button position testing."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock root and create GUI
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        gui = GUIInterface()
        gui._save_current_config = Mock(return_value=True)
        gui._update_status = Mock()
        
        # Mock successful test
        self.mock_automation_engine.test_click_position.return_value = True
        
        gui._test_buy_button()
        
        gui._save_current_config.assert_called_once()
        self.mock_automation_engine.test_click_position.assert_called_once()
        gui._update_status.assert_called()
    
    @patch('smart_buyer.ui.gui.AutomationEngine')
    @patch('smart_buyer.ui.gui.OCRProcessor')
    @patch('smart_buyer.ui.gui.ConfigManager')
    @patch('smart_buyer.ui.gui.tk.Tk')
    def test_save_config(self, mock_tk, mock_config, mock_ocr, mock_automation):
        """Test configuration file saving."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock root and create GUI
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        gui = GUIInterface()
        gui._save_current_config = Mock(return_value=True)
        gui._update_status = Mock()
        
        # Mock successful save
        self.mock_config_manager.save_config.return_value = True
        
        gui._save_config()
        
        gui._save_current_config.assert_called_once()
        self.mock_config_manager.save_config.assert_called_once()
        gui._update_status.assert_called_with("配置已保存到文件")
    
    @patch('smart_buyer.ui.gui.filedialog.askopenfilename')
    @patch('smart_buyer.ui.gui.AutomationEngine')
    @patch('smart_buyer.ui.gui.OCRProcessor')
    @patch('smart_buyer.ui.gui.ConfigManager')
    @patch('smart_buyer.ui.gui.tk.Tk')
    def test_load_config_file(self, mock_tk, mock_config, mock_ocr, mock_automation, mock_dialog):
        """Test configuration file loading."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock root and create GUI
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        gui = GUIInterface()
        gui._load_configuration = Mock()
        gui._update_status = Mock()
        
        # Mock file dialog and successful load
        mock_dialog.return_value = "test_config.json"
        self.mock_config_manager.load_from_file.return_value = True
        
        gui._load_config_file()
        
        mock_dialog.assert_called_once()
        self.mock_config_manager.load_from_file.assert_called_with("test_config.json")
        gui._load_configuration.assert_called_once()
        gui._update_status.assert_called()
    
    @patch('smart_buyer.ui.gui.AutomationEngine')
    @patch('smart_buyer.ui.gui.OCRProcessor')
    @patch('smart_buyer.ui.gui.ConfigManager')
    @patch('smart_buyer.ui.gui.tk.Tk')
    def test_monitoring_callback(self, mock_tk, mock_config, mock_ocr, mock_automation):
        """Test monitoring status callback."""
        mock_config.return_value = self.mock_config_manager
        mock_ocr.return_value = self.mock_ocr_processor
        mock_automation.return_value = self.mock_automation_engine
        
        # Mock root and create GUI
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        gui = GUIInterface()
        gui._update_status = Mock()
        
        # Test callback
        gui._monitoring_callback("测试消息")
        
        # Verify root.after was called to schedule UI update
        mock_root.after.assert_called()


if __name__ == '__main__':
    unittest.main()