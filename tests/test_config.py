"""
Unit tests for configuration management modules.
"""

import unittest
import tempfile
import os
import json
from smart_buyer.config.manager import ConfigManager
from smart_buyer.config.validator import ConfigValidator
from smart_buyer.config.defaults import DEFAULT_CONFIG
from smart_buyer.core.exceptions import ConfigurationError, ValidationError


class TestConfigValidator(unittest.TestCase):
    """Test cases for ConfigValidator class."""
    
    def test_validate_bounding_box_valid(self):
        """Test valid bounding box validation."""
        bbox = [100, 200, 300, 400]
        result = ConfigValidator._validate_bounding_box(bbox)
        self.assertEqual(result, bbox)
    
    def test_validate_bounding_box_invalid_length(self):
        """Test invalid bounding box length."""
        with self.assertRaises(ValidationError):
            ConfigValidator._validate_bounding_box([100, 200, 300])
    
    def test_validate_bounding_box_invalid_order(self):
        """Test invalid bounding box coordinate order."""
        with self.assertRaises(ValidationError):
            ConfigValidator._validate_bounding_box([300, 200, 100, 400])
    
    def test_validate_point_valid(self):
        """Test valid point validation."""
        point = [500, 600]
        result = ConfigValidator._validate_point(point)
        self.assertEqual(result, point)
    
    def test_validate_point_invalid_length(self):
        """Test invalid point length."""
        with self.assertRaises(ValidationError):
            ConfigValidator._validate_point([500])
    
    def test_validate_positive_number_valid(self):
        """Test valid positive number validation."""
        self.assertEqual(ConfigValidator._validate_positive_number(1.5), 1.5)
        self.assertEqual(ConfigValidator._validate_positive_number(10), 10)
    
    def test_validate_positive_number_invalid(self):
        """Test invalid positive number validation."""
        with self.assertRaises(ValidationError):
            ConfigValidator._validate_positive_number(-1)
        with self.assertRaises(ValidationError):
            ConfigValidator._validate_positive_number(0)
    
    def test_validate_log_level_valid(self):
        """Test valid log level validation."""
        self.assertEqual(ConfigValidator._validate_log_level("info"), "INFO")
        self.assertEqual(ConfigValidator._validate_log_level("DEBUG"), "DEBUG")
    
    def test_validate_log_level_invalid(self):
        """Test invalid log level validation."""
        with self.assertRaises(ValidationError):
            ConfigValidator._validate_log_level("INVALID")


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.config_manager = ConfigManager(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        config = self.config_manager.get_all()
        self.assertIsInstance(config, dict)
        self.assertIn('countdown_box', config)
        self.assertIn('buy_btn_pos', config)
    
    def test_get_config_value(self):
        """Test getting configuration values."""
        value = self.config_manager.get('countdown_box')
        self.assertEqual(value, DEFAULT_CONFIG['countdown_box'])
        
        # Test default value
        value = self.config_manager.get('nonexistent_key', 'default')
        self.assertEqual(value, 'default')
    
    def test_set_config_value_valid(self):
        """Test setting valid configuration values."""
        result = self.config_manager.set('click_delay', 0.1)
        self.assertTrue(result)
        self.assertEqual(self.config_manager.get('click_delay'), 0.1)
    
    def test_set_config_value_invalid(self):
        """Test setting invalid configuration values."""
        result = self.config_manager.set('click_delay', -1)
        self.assertFalse(result)
        # Should keep original value
        self.assertEqual(self.config_manager.get('click_delay'), DEFAULT_CONFIG['click_delay'])
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        # Set a value and save
        self.config_manager.set('click_delay', 0.2)
        result = self.config_manager.save_config()
        self.assertTrue(result)
        
        # Create new manager and verify value persisted
        new_manager = ConfigManager(self.temp_file.name)
        self.assertEqual(new_manager.get('click_delay'), 0.2)
    
    def test_update_multiple_values(self):
        """Test updating multiple configuration values."""
        updates = {
            'click_delay': 0.3,
            'check_interval': 0.2,
            'max_retries': 5
        }
        result = self.config_manager.update(updates)
        self.assertTrue(result)
        
        for key, value in updates.items():
            self.assertEqual(self.config_manager.get(key), value)
    
    def test_update_invalid_values(self):
        """Test updating with invalid values."""
        updates = {
            'click_delay': -1,  # Invalid
            'check_interval': 0.2  # Valid
        }
        result = self.config_manager.update(updates)
        self.assertFalse(result)
        
        # Neither value should be updated
        self.assertEqual(self.config_manager.get('click_delay'), DEFAULT_CONFIG['click_delay'])
        self.assertEqual(self.config_manager.get('check_interval'), DEFAULT_CONFIG['check_interval'])
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        # Change some values
        self.config_manager.set('click_delay', 0.5)
        self.config_manager.set('max_retries', 10)
        
        # Reset
        self.config_manager.reset_to_defaults()
        
        # Verify reset
        self.assertEqual(self.config_manager.get('click_delay'), DEFAULT_CONFIG['click_delay'])
        self.assertEqual(self.config_manager.get('max_retries'), DEFAULT_CONFIG['max_retries'])
    
    def test_load_from_invalid_file(self):
        """Test loading from non-existent file."""
        result = self.config_manager.load_from_file('nonexistent.json')
        self.assertFalse(result)
    
    def test_export_to_file(self):
        """Test exporting configuration to file."""
        export_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        export_file.close()
        
        try:
            result = self.config_manager.export_to_file(export_file.name)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(export_file.name))
            
            # Verify content
            with open(export_file.name, 'r', encoding='utf-8') as f:
                exported_config = json.load(f)
            
            self.assertIsInstance(exported_config, dict)
            self.assertIn('countdown_box', exported_config)
            
        finally:
            if os.path.exists(export_file.name):
                os.unlink(export_file.name)


if __name__ == '__main__':
    unittest.main()