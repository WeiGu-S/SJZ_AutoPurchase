"""
智能抢购助手的实用工具函数。

此模块包含在不同组件中使用的通用实用函数。
"""

import time
import pyautogui
from typing import Tuple, List, Union, Optional
from ..core.exceptions import ValidationError


def get_mouse_position_after_delay(delay: float = 3.0) -> Tuple[int, int]:
    """
    在指定延迟后获取鼠标位置。
    
    此函数对于允许用户在捕获坐标之前
    定位鼠标很有用。
    
    参数:
        delay: 捕获位置前的延迟（秒）
        
    返回:
        (x, y)坐标的元组
    """
    time.sleep(delay)
    return pyautogui.position()


def parse_coordinate_string(coord_str: str) -> List[int]:
    """
    将坐标字符串解析为整数列表。
    
    支持的格式如:
    - "[100, 200, 300, 400]" 用于边界框
    - "[500, 600]" 用于点坐标
    
    参数:
        coord_str: 坐标的字符串表示
        
    返回:
        整数坐标列表
        
    异常:
        ValidationError: 如果坐标字符串无效
    """
    try:
        # 移除括号并按逗号分割
        coord_str = coord_str.strip("[]()").replace(" ", "")
        coords = [int(x.strip()) for x in coord_str.split(",") if x.strip()]
        
        if not coords:
            raise ValidationError("空坐标字符串")
            
        return coords
        
    except (ValueError, AttributeError) as e:
        raise ValidationError(f"无效的坐标格式: {coord_str}", details=str(e))


def validate_bounding_box(bbox: List[int]) -> bool:
    """
    验证边界框坐标。
    
    Args:
        bbox: [左, 上, 右, 下] 坐标列表
        
    Returns:
        如果有效返回True
        
    Raises:
        ValidationError: 如果边界框无效
    """
    if len(bbox) != 4:
        raise ValidationError(f"Bounding box must have 4 coordinates, got {len(bbox)}")
    
    left, top, right, bottom = bbox
    
    if left >= right:
        raise ValidationError(f"Left coordinate ({left}) must be less than right ({right})")
    
    if top >= bottom:
        raise ValidationError(f"Top coordinate ({top}) must be less than bottom ({bottom})")
    
    if any(coord < 0 for coord in bbox):
        raise ValidationError("All coordinates must be non-negative")
    
    return True


def validate_point_coordinates(point: List[int]) -> bool:
    """
    验证点坐标。
    
    Args:
        point: [x, y] 坐标列表
        
    Returns:
        如果有效返回True
        
    Raises:
        ValidationError: 如果点坐标无效
    """
    if len(point) != 2:
        raise ValidationError(f"Point must have 2 coordinates, got {len(point)}")
    
    x, y = point
    
    if x < 0 or y < 0:
        raise ValidationError("Point coordinates must be non-negative")
    
    return True


def format_time_remaining(seconds: Optional[int]) -> str:
    """
    将剩余时间格式化为人类可读的格式。
    
    Args:
        seconds: 剩余秒数（如果未知则为None）
        
    Returns:
        格式化的时间字符串
    """
    if seconds is None:
        return "识别失败"
    
    if seconds < 0:
        return "已结束"
    
    if seconds < 60:
        return f"{seconds}秒"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}分{remaining_seconds}秒"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    return f"{hours}时{remaining_minutes}分{remaining_seconds}秒"