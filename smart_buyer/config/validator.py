"""
智能抢购助手的配置验证模块。

此模块为所有配置值提供全面验证，
以确保它们满足应用程序的要求。
"""

import os
from typing import Dict, Any, List, Union
from ..core.exceptions import ConfigurationError, ValidationError
from .defaults import CONFIG_FIELD_TYPES, REQUIRED_CONFIG_FIELDS, VALID_LOG_LEVELS


class ConfigValidator:
    """验证配置值并确保它们满足应用程序要求。"""
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate entire configuration dictionary.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ConfigurationError: If validation fails
        """
        # Check required fields
        ConfigValidator._check_required_fields(config)
        
        # Validate each field
        validated_config = {}
        for key, value in config.items():
            try:
                validated_config[key] = ConfigValidator._validate_field(key, value)
            except ValidationError as e:
                raise ConfigurationError(f"Invalid value for {key}", key, str(e))
        
        return validated_config
    
    @staticmethod
    def _check_required_fields(config: Dict[str, Any]) -> None:
        """Check that all required fields are present."""
        missing_fields = [field for field in REQUIRED_CONFIG_FIELDS if field not in config]
        if missing_fields:
            raise ConfigurationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    @staticmethod
    def _validate_field(key: str, value: Any) -> Any:
        """
        Validate a single configuration field.
        
        Args:
            key: Configuration field name
            value: Field value to validate
            
        Returns:
            Validated value
            
        Raises:
            ValidationError: If validation fails
        """
        # Check type
        if key in CONFIG_FIELD_TYPES:
            expected_type = CONFIG_FIELD_TYPES[key]
            if not isinstance(value, expected_type):
                raise ValidationError(f"Expected {expected_type}, got {type(value)}")
        
        # Field-specific validation
        if key == "countdown_box":
            return ConfigValidator._validate_bounding_box(value)
        elif key in ["buy_btn_pos", "confirm_btn_pos"]:
            return ConfigValidator._validate_point(value)
        elif key == "tesseract_path":
            return ConfigValidator._validate_tesseract_path(value)
        elif key in ["click_delay", "check_interval"]:
            return ConfigValidator._validate_positive_number(value)
        elif key == "max_retries":
            return ConfigValidator._validate_positive_integer(value)
        elif key == "countdown_formats":
            return ConfigValidator._validate_regex_patterns(value)
        elif key == "log_level":
            return ConfigValidator._validate_log_level(value)
        elif key == "log_file":
            return ConfigValidator._validate_file_path(value)
        elif key == "image_enhancement":
            return ConfigValidator._validate_image_enhancement(value)
        elif key == "window_geometry":
            return ConfigValidator._validate_window_geometry(value)
        
        return value
    
    @staticmethod
    def _validate_bounding_box(bbox: List[int]) -> List[int]:
        """Validate bounding box coordinates."""
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise ValidationError("Bounding box must be a list of 4 integers")
        
        if not all(isinstance(coord, int) for coord in bbox):
            raise ValidationError("All bounding box coordinates must be integers")
        
        left, top, right, bottom = bbox
        
        if left >= right:
            raise ValidationError(f"Left ({left}) must be less than right ({right})")
        
        if top >= bottom:
            raise ValidationError(f"Top ({top}) must be less than bottom ({bottom})")
        
        if any(coord < 0 for coord in bbox):
            raise ValidationError("All coordinates must be non-negative")
        
        return bbox
    
    @staticmethod
    def _validate_point(point: List[int]) -> List[int]:
        """Validate point coordinates."""
        if not isinstance(point, list) or len(point) != 2:
            raise ValidationError("Point must be a list of 2 integers")
        
        if not all(isinstance(coord, int) for coord in point):
            raise ValidationError("All point coordinates must be integers")
        
        if any(coord < 0 for coord in point):
            raise ValidationError("Point coordinates must be non-negative")
        
        return point
    
    @staticmethod
    def _validate_tesseract_path(path: str) -> str:
        """Validate Tesseract executable path."""
        if not isinstance(path, str):
            raise ValidationError("Tesseract path must be a string")
        
        # Empty path is allowed (uses system PATH)
        if not path:
            return path
        
        if not os.path.exists(path):
            raise ValidationError(f"Tesseract path does not exist: {path}")
        
        if not os.path.isfile(path):
            raise ValidationError(f"Tesseract path is not a file: {path}")
        
        return path
    
    @staticmethod
    def _validate_positive_number(value: Union[int, float]) -> Union[int, float]:
        """Validate positive number."""
        if not isinstance(value, (int, float)):
            raise ValidationError("Value must be a number")
        
        if value <= 0:
            raise ValidationError("Value must be positive")
        
        return value
    
    @staticmethod
    def _validate_positive_integer(value: int) -> int:
        """Validate positive integer."""
        if not isinstance(value, int):
            raise ValidationError("Value must be an integer")
        
        if value <= 0:
            raise ValidationError("Value must be positive")
        
        return value
    
    @staticmethod
    def _validate_regex_patterns(patterns: List[str]) -> List[str]:
        """Validate regex patterns."""
        if not isinstance(patterns, list):
            raise ValidationError("Patterns must be a list")
        
        if not patterns:
            raise ValidationError("At least one pattern is required")
        
        import re
        for pattern in patterns:
            if not isinstance(pattern, str):
                raise ValidationError("All patterns must be strings")
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValidationError(f"Invalid regex pattern '{pattern}': {e}")
        
        return patterns
    
    @staticmethod
    def _validate_log_level(level: str) -> str:
        """Validate log level."""
        if not isinstance(level, str):
            raise ValidationError("Log level must be a string")
        
        level = level.upper()
        if level not in VALID_LOG_LEVELS:
            raise ValidationError(f"Invalid log level. Must be one of: {', '.join(VALID_LOG_LEVELS)}")
        
        return level
    
    @staticmethod
    def _validate_file_path(path: str) -> str:
        """Validate file path for writing."""
        if not isinstance(path, str):
            raise ValidationError("File path must be a string")
        
        if not path:
            raise ValidationError("File path cannot be empty")
        
        # Check if directory exists or can be created
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except OSError as e:
                raise ValidationError(f"Cannot create directory for log file: {e}")
        
        return path
    
    @staticmethod
    def _validate_image_enhancement(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate image enhancement configuration."""
        if not isinstance(config, dict):
            raise ValidationError("Image enhancement config must be a dictionary")
        
        if "contrast_factor" in config:
            factor = config["contrast_factor"]
            if not isinstance(factor, (int, float)) or factor <= 0:
                raise ValidationError("Contrast factor must be a positive number")
        
        if "enable_grayscale" in config:
            if not isinstance(config["enable_grayscale"], bool):
                raise ValidationError("Enable grayscale must be a boolean")
        
        return config
    
    @staticmethod
    def _validate_window_geometry(geometry: str) -> str:
        """Validate window geometry string."""
        if not isinstance(geometry, str):
            raise ValidationError("Window geometry must be a string")
        
        import re
        if not re.match(r'^\d+x\d+$', geometry):
            raise ValidationError("Window geometry must be in format 'WIDTHxHEIGHT'")
        
        return geometry