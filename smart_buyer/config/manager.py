"""
智能抢购助手的配置管理模块。

此模块提供增强的配置管理功能，包括验证、
文件I/O和运行时配置更新。
"""

import json
import os
from typing import Dict, Any, Optional
from ..core.exceptions import ConfigurationError
from ..utils.logging import get_logger
from .defaults import DEFAULT_CONFIG
from .validator import ConfigValidator


class ConfigManager:
    """具有验证和持久化功能的增强配置管理器。"""
    
    def __init__(self, config_file: str = 'config.json'):
        """
        初始化配置管理器。
        
        参数:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.logger = get_logger(__name__)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file with fallback to defaults.
        
        Returns:
            Loaded and validated configuration dictionary
        """
        config = DEFAULT_CONFIG.copy()
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # Merge with defaults (file config takes precedence)
                config.update(file_config)
                self.logger.info(f"Configuration loaded from {self.config_file}")
                
            except (json.JSONDecodeError, IOError) as e:
                self.logger.error(f"Failed to load config file {self.config_file}: {e}")
                self.logger.info("Using default configuration")
        else:
            self.logger.info(f"Config file {self.config_file} not found, using defaults")
        
        # Validate configuration
        try:
            config = ConfigValidator.validate_config(config)
        except ConfigurationError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            self.logger.info("Falling back to default configuration")
            config = ConfigValidator.validate_config(DEFAULT_CONFIG.copy())
        
        return config
    
    def save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate before saving
            ConfigValidator.validate_config(self._config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except (ConfigurationError, IOError, json.JSONEncodeError) as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value with validation.
        
        Args:
            key: Configuration key
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create temporary config for validation
            temp_config = self._config.copy()
            temp_config[key] = value
            
            # Validate the change
            validated_config = ConfigValidator.validate_config(temp_config)
            
            # Apply the change
            self._config = validated_config
            self.logger.debug(f"Configuration updated: {key} = {value}")
            return True
            
        except ConfigurationError as e:
            self.logger.error(f"Failed to set configuration {key}: {e}")
            return False
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """
        Update multiple configuration values.
        
        Args:
            updates: Dictionary of key-value pairs to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create temporary config for validation
            temp_config = self._config.copy()
            temp_config.update(updates)
            
            # Validate all changes
            validated_config = ConfigValidator.validate_config(temp_config)
            
            # Apply all changes
            self._config = validated_config
            self.logger.info(f"Configuration updated with {len(updates)} changes")
            return True
            
        except ConfigurationError as e:
            self.logger.error(f"Failed to update configuration: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """将配置重置为默认值。"""
        self._config = ConfigValidator.validate_config(DEFAULT_CONFIG.copy())
        self.logger.info("配置已重置为默认值")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Copy of entire configuration dictionary
        """
        return self._config.copy()
    
    def load_from_file(self, file_path: str) -> bool:
        """
        Load configuration from a specific file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Configuration file not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # Merge with current config
            temp_config = self._config.copy()
            temp_config.update(file_config)
            
            # Validate
            validated_config = ConfigValidator.validate_config(temp_config)
            
            # Apply
            self._config = validated_config
            self.config_file = file_path
            self.logger.info(f"Configuration loaded from {file_path}")
            return True
            
        except (json.JSONDecodeError, IOError, ConfigurationError) as e:
            self.logger.error(f"Failed to load configuration from {file_path}: {e}")
            return False
    
    def export_to_file(self, file_path: str) -> bool:
        """
        Export current configuration to a file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Configuration exported to {file_path}")
            return True
            
        except (IOError, json.JSONEncodeError) as e:
            self.logger.error(f"Failed to export configuration to {file_path}: {e}")
            return False
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取配置的只读访问权限。"""
        return self._config.copy()