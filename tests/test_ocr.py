"""
Unit tests for OCR processing functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from smart_buyer.core.ocr import OCRProcessor
from smart_buyer.core.exceptions import OCRError


class TestOCRProcessor(unittest.TestCase):
    """Test cases for OCRProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ocr_processor = OCRProcessor()
        self.test_region = (100, 200, 300, 400)
        self.countdown_formats = [
            r'(\d{1,2}):(\d{2}):(\d{2})',  # HH:MM:SS
            r'(\d{1,2})分(\d{2})秒',        # MM分SS秒
            r'(\d+)秒'                      # SS秒
        ]
    
    def test_init_with_tesseract_path(self):
        """Test initialization with custom Tesseract path."""
        with patch('smart_buyer.core.ocr.pytesseract') as mock_pytesseract:
            processor = OCRProcessor(tesseract_path="/usr/bin/tesseract")
            mock_pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    
    def test_convert_to_seconds_hms_format(self):
        """Test conversion of HH:MM:SS format to seconds."""
        groups = ("1", "30", "45")
        pattern = r'(\d{1,2}):(\d{2}):(\d{2})'
        result = self.ocr_processor._convert_to_seconds(groups, pattern)
        expected = 1 * 3600 + 30 * 60 + 45  # 5445 seconds
        self.assertEqual(result, expected)
    
    def test_convert_to_seconds_chinese_format(self):
        """Test conversion of MM分SS秒 format to seconds."""
        groups = ("30", "45")
        pattern = r'(\d{1,2})分(\d{2})秒'
        result = self.ocr_processor._convert_to_seconds(groups, pattern)
        expected = 30 * 60 + 45  # 1845 seconds
        self.assertEqual(result, expected)
    
    def test_convert_to_seconds_seconds_only(self):
        """Test conversion of seconds-only format."""
        groups = ("45",)
        pattern = r'(\d+)秒'
        result = self.ocr_processor._convert_to_seconds(groups, pattern)
        self.assertEqual(result, 45)
    
    def test_convert_to_seconds_invalid_groups(self):
        """Test conversion with invalid groups."""
        groups = ("invalid", "data")
        pattern = r'(\d{1,2})分(\d{2})秒'
        result = self.ocr_processor._convert_to_seconds(groups, pattern)
        self.assertIsNone(result)
    
    def test_parse_countdown_hms_format(self):
        """Test parsing countdown in HH:MM:SS format."""
        text = "剩余时间: 01:30:45"
        result = self.ocr_processor._parse_countdown(text, self.countdown_formats)
        expected = 1 * 3600 + 30 * 60 + 45
        self.assertEqual(result, expected)
    
    def test_parse_countdown_chinese_format(self):
        """Test parsing countdown in Chinese format."""
        text = "还有30分45秒"
        result = self.ocr_processor._parse_countdown(text, self.countdown_formats)
        expected = 30 * 60 + 45
        self.assertEqual(result, expected)
    
    def test_parse_countdown_seconds_only(self):
        """Test parsing countdown with seconds only."""
        text = "45秒后开始"
        result = self.ocr_processor._parse_countdown(text, self.countdown_formats)
        self.assertEqual(result, 45)
    
    def test_parse_countdown_no_match(self):
        """Test parsing countdown with no matching pattern."""
        text = "无法识别的文本"
        result = self.ocr_processor._parse_countdown(text, self.countdown_formats)
        self.assertIsNone(result)
    
    def test_parse_countdown_empty_text(self):
        """Test parsing countdown with empty text."""
        text = ""
        result = self.ocr_processor._parse_countdown(text, self.countdown_formats)
        self.assertIsNone(result)
    
    @patch('smart_buyer.core.ocr.ImageGrab.grab')
    def test_capture_region_success(self, mock_grab):
        """Test successful screen region capture."""
        mock_image = Mock(spec=Image.Image)
        mock_grab.return_value = mock_image
        
        result = self.ocr_processor._capture_region(self.test_region)
        
        mock_grab.assert_called_once_with(bbox=self.test_region)
        self.assertEqual(result, mock_image)
    
    @patch('smart_buyer.core.ocr.ImageGrab.grab')
    def test_capture_region_failure(self, mock_grab):
        """Test screen region capture failure."""
        mock_grab.side_effect = Exception("Screen capture failed")
        
        with self.assertRaises(OCRError):
            self.ocr_processor._capture_region(self.test_region)
    
    def test_preprocess_image_success(self):
        """Test successful image preprocessing."""
        # Create a mock image
        mock_image = Mock(spec=Image.Image)
        mock_gray = Mock(spec=Image.Image)
        mock_enhanced = Mock(spec=Image.Image)
        
        mock_image.convert.return_value = mock_gray
        
        with patch('smart_buyer.core.ocr.ImageEnhance.Contrast') as mock_contrast:
            mock_enhancer = Mock()
            mock_enhancer.enhance.return_value = mock_enhanced
            mock_contrast.return_value = mock_enhancer
            
            result = self.ocr_processor._preprocess_image(mock_image, 2.0)
            
            mock_image.convert.assert_called_once_with('L')
            mock_contrast.assert_called_once_with(mock_gray)
            mock_enhancer.enhance.assert_called_once_with(2.0)
            self.assertEqual(result, mock_enhanced)
    
    def test_preprocess_image_failure(self):
        """Test image preprocessing failure fallback."""
        mock_image = Mock(spec=Image.Image)
        mock_image.convert.side_effect = Exception("Conversion failed")
        
        result = self.ocr_processor._preprocess_image(mock_image)
        self.assertEqual(result, mock_image)  # Should return original image
    
    @patch('smart_buyer.core.ocr.pytesseract.image_to_string')
    def test_extract_text_success(self, mock_ocr):
        """Test successful text extraction."""
        mock_image = Mock(spec=Image.Image)
        mock_ocr.return_value = "  01:30:45  "
        
        result = self.ocr_processor._extract_text(mock_image)
        
        mock_ocr.assert_called_once_with(mock_image, config="--psm 8")
        self.assertEqual(result, "01:30:45")
    
    @patch('smart_buyer.core.ocr.pytesseract.image_to_string')
    def test_extract_text_failure(self, mock_ocr):
        """Test text extraction failure."""
        mock_image = Mock(spec=Image.Image)
        mock_ocr.side_effect = Exception("OCR failed")
        
        with self.assertRaises(OCRError):
            self.ocr_processor._extract_text(mock_image)
    
    def test_validate_countdown_formats_valid(self):
        """Test validation of valid countdown formats."""
        formats = [
            r'(\d{1,2}):(\d{2}):(\d{2})',
            r'(\d{1,2})分(\d{2})秒',
            r'(\d+)秒'
        ]
        result = self.ocr_processor.validate_countdown_formats(formats)
        self.assertEqual(result, formats)
    
    def test_validate_countdown_formats_invalid(self):
        """Test validation with invalid regex patterns."""
        formats = [
            r'(\d{1,2}):(\d{2}):(\d{2})',  # Valid
            r'[invalid regex',              # Invalid
            r'(\d+)秒'                      # Valid
        ]
        result = self.ocr_processor.validate_countdown_formats(formats)
        expected = [formats[0], formats[2]]  # Only valid patterns
        self.assertEqual(result, expected)
    
    def test_validate_countdown_formats_empty(self):
        """Test validation with empty format list."""
        result = self.ocr_processor.validate_countdown_formats([])
        self.assertEqual(result, [])
    
    @patch('smart_buyer.core.ocr.OCRProcessor._capture_region')
    @patch('smart_buyer.core.ocr.OCRProcessor._preprocess_image')
    @patch('smart_buyer.core.ocr.OCRProcessor._extract_text')
    def test_test_ocr_region_success(self, mock_extract, mock_preprocess, mock_capture):
        """Test OCR region testing functionality."""
        mock_image = Mock(spec=Image.Image)
        mock_processed = Mock(spec=Image.Image)
        
        mock_capture.return_value = mock_image
        mock_preprocess.return_value = mock_processed
        mock_extract.return_value = "01:30:45"
        
        text, success = self.ocr_processor.test_ocr_region(self.test_region)
        
        self.assertEqual(text, "01:30:45")
        self.assertTrue(success)
        mock_capture.assert_called_once_with(self.test_region)
        mock_preprocess.assert_called_once_with(mock_image)
        mock_extract.assert_called_once_with(mock_processed)
    
    @patch('smart_buyer.core.ocr.OCRProcessor._capture_region')
    def test_test_ocr_region_failure(self, mock_capture):
        """Test OCR region testing failure."""
        mock_capture.side_effect = Exception("Capture failed")
        
        text, success = self.ocr_processor.test_ocr_region(self.test_region)
        
        self.assertIsNone(text)
        self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()