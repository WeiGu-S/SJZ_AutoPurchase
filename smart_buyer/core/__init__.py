"""
智能抢购助手的核心功能模块。

此包包含核心业务逻辑，包括:
- 用于倒计时识别的OCR处理
- 用于购买执行的自动化引擎
- 异常处理
"""

from .exceptions import SmartBuyerError, ConfigurationError, OCRError, AutomationError, ValidationError
from .ocr import OCRProcessor
from .automation import AutomationEngine, AutomationState

__all__ = [
    "SmartBuyerError",
    "ConfigurationError", 
    "OCRError",
    "AutomationError",
    "ValidationError",
    "OCRProcessor",
    "AutomationEngine",
    "AutomationState"
]