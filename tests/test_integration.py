#!/usr/bin/env python3
"""
智能抢购助手的集成测试。

此脚本测试重构后应用程序的基本功能，
确保所有模块正确协作。
"""

import sys
import os
import unittest
import tempfile
import json
from unittest.mock import Mock, patch

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from smart_buyer.config.manager import ConfigManager
from smart_buyer.core.ocr import OCRProcessor
from smart_buyer.core.automation import AutomationEngine, AutomationState
from smart_buyer.ui.cli import CLIInterface
from smart_buyer.ui.gui import GUIInterface
from smart_buyer.core.exceptions import SmartBuyerError, ConfigurationError


class TestConfigurationIntegration(unittest.TestCase):
    """测试配置管理的集成功能。"""
    
    def setUp(self):
        """设置测试环境。"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.config_manager = ConfigManager(self.temp_file.name)
    
    def tearDown(self):
        """清理测试环境。"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_config_persistence(self):
        """测试配置持久化。"""
        # 修改配置
        original_interval = self.config_manager.get('check_interval')
        new_interval = 0.5
        
        success = self.config_manager.set('check_interval', new_interval)
        self.assertTrue(success)
        
        # 保存配置
        success = self.config_manager.save_config()
        self.assertTrue(success)
        
        # 创建新的配置管理器实例
        new_manager = ConfigManager(self.temp_file.name)
        loaded_interval = new_manager.get('check_interval')
        
        self.assertEqual(loaded_interval, new_interval)
        self.assertNotEqual(loaded_interval, original_interval)
    
    def test_config_validation_integration(self):
        """测试配置验证集成。"""
        # 测试有效配置
        valid_updates = {
            'countdown_box': [100, 200, 300, 400],
            'buy_btn_pos': [500, 600],
            'check_interval': 0.2
        }
        
        success = self.config_manager.update(valid_updates)
        self.assertTrue(success)
        
        # 测试无效配置
        invalid_updates = {
            'countdown_box': [300, 200, 100, 400],  # 左 > 右
            'check_interval': -1  # 负值
        }
        
        success = self.config_manager.update(invalid_updates)
        self.assertFalse(success)
        
        # 确保无效配置没有被应用
        self.assertEqual(self.config_manager.get('check_interval'), 0.2)


class TestOCRAutomationIntegration(unittest.TestCase):
    """测试OCR和自动化引擎的集成。"""
    
    def setUp(self):
        """设置测试环境。"""
        self.config_manager = ConfigManager()
        self.ocr_processor = OCRProcessor()
        self.automation_engine = AutomationEngine(self.ocr_processor)
    
    def test_ocr_format_validation(self):
        """测试OCR格式验证。"""
        formats = self.config_manager.get('countdown_formats')
        valid_formats = self.ocr_processor.validate_countdown_formats(formats)
        
        self.assertGreater(len(valid_formats), 0)
        self.assertEqual(len(valid_formats), len(formats))
    
    def test_automation_configuration_validation(self):
        """测试自动化引擎配置验证。"""
        countdown_region = tuple(self.config_manager.get('countdown_box'))
        buy_button_pos = tuple(self.config_manager.get('buy_btn_pos'))
        confirm_button_pos = tuple(self.config_manager.get('confirm_btn_pos'))
        
        is_valid, errors = self.automation_engine.validate_configuration(
            countdown_region=countdown_region,
            buy_button_pos=buy_button_pos,
            confirm_button_pos=confirm_button_pos
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_automation_state_management(self):
        """测试自动化引擎状态管理。"""
        # 初始状态
        self.assertEqual(self.automation_engine.get_state(), AutomationState.IDLE)
        self.assertFalse(self.automation_engine.is_running())
        
        # 测试停止（当未运行时）
        self.automation_engine.stop_monitoring()
        self.assertEqual(self.automation_engine.get_state(), AutomationState.IDLE)


class TestCLIIntegration(unittest.TestCase):
    """测试CLI界面集成。"""
    
    def setUp(self):
        """设置测试环境。"""
        self.cli = CLIInterface()
    
    def test_cli_initialization(self):
        """测试CLI初始化。"""
        self.assertIsNotNone(self.cli.config_manager)
        self.assertIsNotNone(self.cli.ocr_processor)
        self.assertIsNotNone(self.cli.automation_engine)
    
    def test_argument_parsing(self):
        """测试参数解析。"""
        # 测试基本参数
        args = self.cli._parse_arguments(['--console', '--verbose'])
        self.assertTrue(args.console)
        self.assertTrue(args.verbose)
        
        # 测试配置参数
        args = self.cli._parse_arguments([
            '--set', 'check_interval', '0.3',
            '--config', 'test.json'
        ])
        self.assertEqual(args.set, [['check_interval', '0.3']])
        self.assertEqual(args.config, 'test.json')
    
    def test_config_value_parsing(self):
        """测试配置值解析。"""
        # 测试坐标解析
        result = self.cli._parse_config_value('countdown_box', '[100,200,300,400]')
        self.assertEqual(result, [100, 200, 300, 400])
        
        # 测试布尔值解析
        result = self.cli._parse_config_value('enable_confirm_click', 'true')
        self.assertTrue(result)
        
        result = self.cli._parse_config_value('enable_confirm_click', 'false')
        self.assertFalse(result)
        
        # 测试数值解析
        result = self.cli._parse_config_value('check_interval', '0.5')
        self.assertEqual(result, 0.5)
        
        result = self.cli._parse_config_value('max_retries', '10')
        self.assertEqual(result, 10)


class TestGUIIntegration(unittest.TestCase):
    """测试GUI界面集成。"""
    
    def test_gui_components_exist(self):
        """测试GUI组件存在性。"""
        # 由于GUI需要显示环境，我们只测试类的存在性
        from smart_buyer.ui.gui import GUIInterface
        
        # 确保类可以导入
        self.assertTrue(hasattr(GUIInterface, '__init__'))
        self.assertTrue(hasattr(GUIInterface, 'run'))
        self.assertTrue(hasattr(GUIInterface, '_setup_gui'))


class TestErrorHandling(unittest.TestCase):
    """测试错误处理集成。"""
    
    def test_configuration_error_handling(self):
        """测试配置错误处理。"""
        config_manager = ConfigManager()
        
        # 测试无效配置不会崩溃应用
        success = config_manager.set('countdown_box', 'invalid')
        self.assertFalse(success)
        
        # 确保配置保持有效状态
        countdown_box = config_manager.get('countdown_box')
        self.assertIsInstance(countdown_box, list)
        self.assertEqual(len(countdown_box), 4)
    
    def test_ocr_error_handling(self):
        """测试OCR错误处理。"""
        ocr_processor = OCRProcessor()
        
        # 测试无效格式处理
        invalid_formats = ['[invalid regex']
        valid_formats = ocr_processor.validate_countdown_formats(invalid_formats)
        self.assertEqual(len(valid_formats), 0)
    
    def test_automation_error_handling(self):
        """测试自动化错误处理。"""
        ocr_processor = OCRProcessor()
        automation_engine = AutomationEngine(ocr_processor)
        
        # 测试无效配置处理
        is_valid, errors = automation_engine.validate_configuration(
            countdown_region=(300, 200, 100, 400),  # 无效区域
            buy_button_pos=(500, 600),
            confirm_button_pos=(550, 650)
        )
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestBackwardCompatibility(unittest.TestCase):
    """测试向后兼容性。"""
    
    def test_main_entry_points(self):
        """测试主入口点。"""
        from smart_buyer import main, gui_main, cli_main, console_main
        
        # 确保所有入口点都可调用
        self.assertTrue(callable(main))
        self.assertTrue(callable(gui_main))
        self.assertTrue(callable(cli_main))
        self.assertTrue(callable(console_main))
    
    def test_package_imports(self):
        """测试包导入。"""
        # 测试主包导入
        import smart_buyer
        self.assertEqual(smart_buyer.__version__, "2.0.0")
        
        # 测试子包导入
        from smart_buyer.core import OCRProcessor, AutomationEngine
        from smart_buyer.config import ConfigManager
        from smart_buyer.ui import GUIInterface, CLIInterface
        
        # 确保所有类都可实例化
        config_manager = ConfigManager()
        ocr_processor = OCRProcessor()
        automation_engine = AutomationEngine(ocr_processor)
        cli_interface = CLIInterface()
        
        self.assertIsNotNone(config_manager)
        self.assertIsNotNone(ocr_processor)
        self.assertIsNotNone(automation_engine)
        self.assertIsNotNone(cli_interface)


def run_integration_tests():
    """运行所有集成测试。"""
    print("智能抢购助手集成测试")
    print("=" * 50)
    
    # 创建测试套件
    test_classes = [
        TestConfigurationIntegration,
        TestOCRAutomationIntegration,
        TestCLIIntegration,
        TestGUIIntegration,
        TestErrorHandling,
        TestBackwardCompatibility
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回结果
    if result.wasSuccessful():
        print("\\n" + "=" * 50)
        print("✓ 所有集成测试通过！")
        return 0
    else:
        print("\\n" + "=" * 50)
        print("✗ 部分测试失败")
        print(f"失败: {len(result.failures)}, 错误: {len(result.errors)}")
        return 1


if __name__ == '__main__':
    sys.exit(run_integration_tests())