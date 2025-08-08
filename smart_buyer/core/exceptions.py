"""
智能抢购助手的自定义异常类。

此模块定义了在整个应用程序中使用的异常层次结构，
以提供清晰的错误处理和调试信息。
"""

from typing import Optional


class SmartBuyerError(Exception):
    """所有智能抢购助手相关错误的基础异常类。"""
    
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ConfigurationError(SmartBuyerError):
    """当出现配置相关错误时抛出。"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[str] = None):
        self.config_key = config_key
        if config_key:
            message = f"Configuration error for '{config_key}': {message}"
        super().__init__(message, details)


class OCRError(SmartBuyerError):
    """当OCR处理失败时抛出。"""
    
    def __init__(self, message: str, image_region: Optional[tuple] = None, details: Optional[str] = None):
        self.image_region = image_region
        if image_region:
            message = f"OCR error in region {image_region}: {message}"
        super().__init__(message, details)


class AutomationError(SmartBuyerError):
    """当自动化操作失败时抛出。"""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[str] = None):
        self.operation = operation
        if operation:
            message = f"Automation error during '{operation}': {message}"
        super().__init__(message, details)


class ValidationError(SmartBuyerError):
    """当数据验证失败时抛出。"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None):
        self.field = field
        self.value = value
        if field:
            message = f"Validation error for field '{field}': {message}"
        super().__init__(message)