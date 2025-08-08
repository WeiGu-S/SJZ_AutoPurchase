"""
智能抢购助手的OCR处理模块。

此模块处理倒计时检测的光学字符识别，
包括图像预处理和支持多种格式的文本解析。
"""

import re
import pytesseract
from PIL import Image, ImageGrab, ImageEnhance
from typing import Optional, List, Tuple
from ..core.exceptions import OCRError
from ..utils.logging import get_logger


class OCRProcessor:
    """处理倒计时识别的OCR处理器。"""
    
    def __init__(self, tesseract_path: str = "", ocr_config: str = "--psm 8"):
        """
        初始化OCR处理器。
        
        参数:
            tesseract_path: Tesseract可执行文件路径（空字符串表示使用系统PATH）
            ocr_config: Tesseract配置参数
        """
        self.logger = get_logger(__name__)
        self.tesseract_path = tesseract_path
        self.ocr_config = ocr_config
        
        # 如果提供了路径则设置Tesseract路径
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            self.logger.info(f"Tesseract路径设置为: {tesseract_path}")
    
    def read_countdown(
        self,
        region: Tuple[int, int, int, int],
        countdown_formats: List[str],
        enable_preprocessing: bool = True,
        contrast_factor: float = 2.0
    ) -> Optional[int]:
        """
        从屏幕区域读取倒计时值。
        
        参数:
            region: 屏幕区域，格式为(左, 上, 右, 下)
            countdown_formats: 倒计时格式的正则表达式模式列表
            enable_preprocessing: 是否应用图像预处理
            contrast_factor: 对比度增强因子
            
        返回:
            倒计时值（秒），如果识别失败则返回None
            
        异常:
            OCRError: 如果OCR处理失败
        """
        try:
            # 捕获屏幕区域
            image = self._capture_region(region)
            
            # 如果启用则应用预处理
            if enable_preprocessing:
                image = self._preprocess_image(image, contrast_factor)
            
            # 使用OCR提取文本
            text = self._extract_text(image)
            self.logger.debug(f"OCR提取的文本: '{text}'")
            
            # 从文本中解析倒计时
            countdown_seconds = self._parse_countdown(text, countdown_formats)
            
            if countdown_seconds is not None:
                self.logger.debug(f"解析的倒计时: {countdown_seconds}秒")
            else:
                self.logger.debug("从文本中解析倒计时失败")
            
            return countdown_seconds
            
        except Exception as e:
            raise OCRError(f"OCR处理失败: {str(e)}", region)
    
    def _capture_region(self, region: Tuple[int, int, int, int]) -> Image.Image:
        """
        将屏幕区域捕获为图像。
        
        参数:
            region: 屏幕区域，格式为(左, 上, 右, 下)
            
        返回:
            捕获的图像
            
        异常:
            OCRError: 如果屏幕捕获失败
        """
        try:
            image = ImageGrab.grab(bbox=region)
            self.logger.debug(f"捕获屏幕区域: {region}")
            return image
        except Exception as e:
            raise OCRError(f"捕获屏幕区域失败: {str(e)}", region)
    
    def _preprocess_image(self, image: Image.Image, contrast_factor: float = 2.0) -> Image.Image:
        """
        应用图像预处理以提高OCR准确性。
        
        参数:
            image: 输入图像
            contrast_factor: 对比度增强因子
            
        返回:
            预处理后的图像
        """
        try:
            # 转换为灰度图
            gray_image = image.convert('L')
            self.logger.debug("图像已转换为灰度图")
            
            # 增强对比度
            enhancer = ImageEnhance.Contrast(gray_image)
            enhanced_image = enhancer.enhance(contrast_factor)
            self.logger.debug(f"对比度增强因子: {contrast_factor}")
            
            return enhanced_image
            
        except Exception as e:
            self.logger.warning(f"图像预处理失败: {e}，使用原始图像")
            return image
    
    def _extract_text(self, image: Image.Image) -> str:
        """
        使用OCR从图像中提取文本。
        
        参数:
            image: 输入图像
            
        返回:
            提取的文本
            
        异常:
            OCRError: 如果文本提取失败
        """
        try:
            text = pytesseract.image_to_string(image, config=self.ocr_config)
            return text.strip()
        except Exception as e:
            raise OCRError(f"文本提取失败: {str(e)}")
    
    def _parse_countdown(self, text: str, countdown_formats: List[str]) -> Optional[int]:
        """
        使用多种格式模式从文本中解析倒计时值。
        
        参数:
            text: 要解析的文本
            countdown_formats: 倒计时格式的正则表达式模式列表
            
        返回:
            倒计时值（秒），如果解析失败则返回None
        """
        for pattern in countdown_formats:
            try:
                match = re.search(pattern, text)
                if match:
                    groups = match.groups()
                    seconds = self._convert_to_seconds(groups, pattern)
                    if seconds is not None:
                        return seconds
            except re.error as e:
                self.logger.warning(f"无效的正则表达式模式 '{pattern}': {e}")
            except Exception as e:
                self.logger.debug(f"使用模式 '{pattern}' 解析失败: {e}")
        
        return None
    
    def _convert_to_seconds(self, groups: Tuple[str, ...], pattern: str) -> Optional[int]:
        """
        根据模式将匹配的组转换为秒数。
        
        参数:
            groups: 正则表达式匹配组
            pattern: 原始正则表达式模式（用于上下文）
            
        返回:
            总秒数，如果转换失败则返回None
        """
        try:
            if len(groups) == 3:
                # HH:MM:SS 格式
                hours, minutes, seconds = map(int, groups)
                return hours * 3600 + minutes * 60 + seconds
                
            elif len(groups) == 2:
                # MM分SS秒 格式或 MM:SS 格式
                if '分' in pattern and '秒' in pattern:
                    minutes, seconds = map(int, groups)
                    return minutes * 60 + seconds
                else:
                    # 假设为 MM:SS 格式
                    minutes, seconds = map(int, groups)
                    return minutes * 60 + seconds
                    
            elif len(groups) == 1:
                # SS秒 格式或纯秒数
                return int(groups[0])
            
            return None
            
        except (ValueError, TypeError) as e:
            self.logger.debug(f"将组 {groups} 转换为秒数失败: {e}")
            return None
    
    def test_ocr_region(
        self,
        region: Tuple[int, int, int, int],
        save_debug_image: bool = False,
        debug_image_path: str = "debug_ocr.png"
    ) -> Tuple[Optional[str], bool]:
        """
        在特定区域测试OCR以进行调试。
        
        参数:
            region: 要测试的屏幕区域
            save_debug_image: 是否保存捕获的图像用于调试
            debug_image_path: 保存调试图像的路径
            
        返回:
            (提取的文本, 是否成功)的元组
        """
        try:
            # 捕获并预处理图像
            image = self._capture_region(region)
            processed_image = self._preprocess_image(image)
            
            # 如果请求则保存调试图像
            if save_debug_image:
                try:
                    processed_image.save(debug_image_path)
                    self.logger.info(f"调试图像已保存到: {debug_image_path}")
                except Exception as e:
                    self.logger.warning(f"保存调试图像失败: {e}")
            
            # 提取文本
            text = self._extract_text(processed_image)
            self.logger.info(f"OCR测试结果: '{text}'")
            
            return text, True
            
        except Exception as e:
            self.logger.error(f"OCR测试失败: {e}")
            return None, False
    
    def validate_countdown_formats(self, formats: List[str]) -> List[str]:
        """
        验证倒计时格式模式。
        
        参数:
            formats: 要验证的正则表达式模式列表
            
        返回:
            有效模式列表
        """
        valid_formats = []
        
        for pattern in formats:
            try:
                re.compile(pattern)
                valid_formats.append(pattern)
                self.logger.debug(f"有效的倒计时格式: {pattern}")
            except re.error as e:
                self.logger.warning(f"无效的倒计时格式 '{pattern}': {e}")
        
        if not valid_formats:
            self.logger.warning("未找到有效的倒计时格式")
        
        return valid_formats