"""
智能抢购助手的默认配置值。

此模块包含应用程序中使用的所有默认配置常量，
为默认值提供集中位置。
"""

from typing import Dict, Any, List

# 默认配置字典
DEFAULT_CONFIG: Dict[str, Any] = {
    # 倒计时检测的屏幕区域 (左, 上, 右, 下)
    "countdown_box": [100, 200, 300, 240],
    
    # 自动点击的按钮位置
    "buy_btn_pos": [500, 600],
    "confirm_btn_pos": [550, 650],
    
    # Tesseract OCR配置
    "tesseract_path": "",
    
    # 时间配置
    "click_delay": 0.05,  # 点击之间的延迟（秒）
    "check_interval": 0.1,  # 倒计时检查间隔（秒）
    
    # 重试和错误处理
    "max_retries": 3,  # OCR识别的最大重试次数
    
    # 功能开关
    "enable_confirm_click": True,  # 购买后是否点击确认按钮
    
    # OCR识别的倒计时格式模式
    "countdown_formats": [
        r'(\d{1,2}):(\d{2}):(\d{2})',  # HH:MM:SS 格式
        r'(\d{1,2})分(\d{2})秒',        # MM分SS秒 格式
        r'(\d+)秒'                      # SS秒 格式
    ],
    
    # 日志配置
    "log_level": "INFO",
    "log_file": "抢购日志.log",
    "enable_console_logging": True,
    
    # OCR配置
    "ocr_config": "--psm 8",  # Tesseract页面分割模式
    "image_enhancement": {
        "contrast_factor": 2.0,  # 对比度增强因子
        "enable_grayscale": True,  # 转换为灰度图
    },
    
    # GUI配置
    "window_geometry": "600x500",
    "window_title": "智能抢购助手",
    
    # 验证设置
    "min_countdown_value": 0,
    "max_countdown_value": 86400,  # 24小时（秒）
}

# 用于验证的配置字段类型
CONFIG_FIELD_TYPES: Dict[str, type] = {
    "countdown_box": list,
    "buy_btn_pos": list,
    "confirm_btn_pos": list,
    "tesseract_path": str,
    "click_delay": (int, float),
    "check_interval": (int, float),
    "max_retries": int,
    "enable_confirm_click": bool,
    "countdown_formats": list,
    "log_level": str,
    "log_file": str,
    "enable_console_logging": bool,
    "ocr_config": str,
    "image_enhancement": dict,
    "window_geometry": str,
    "window_title": str,
    "min_countdown_value": int,
    "max_countdown_value": int,
}

# 必须存在的必需配置字段
REQUIRED_CONFIG_FIELDS: List[str] = [
    "countdown_box",
    "buy_btn_pos",
    "confirm_btn_pos",
    "check_interval",
    "max_retries",
]

# 有效的日志级别
VALID_LOG_LEVELS: List[str] = [
    "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
]