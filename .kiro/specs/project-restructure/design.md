# Design Document

## Overview

This design document outlines the restructuring of the smart purchasing assistant from a monolithic single-file application into a well-organized, modular Python package. The restructuring will improve maintainability, testability, and extensibility while preserving all existing functionality.

The current application (`sjz.py`) contains approximately 370 lines of code with three main classes (`ConfigManager`, `AutoBuyer`, `AutoBuyerGUI`) and handles GUI, CLI, configuration management, OCR processing, and automation logic all in one file.

## Architecture

### High-Level Architecture

The restructured application will follow a layered architecture pattern:

```
┌─────────────────────────────────────┐
│           Presentation Layer        │
│  ┌─────────────┐  ┌─────────────────┐│
│  │     GUI     │  │      CLI        ││
│  │   Module    │  │    Module       ││
│  └─────────────┘  └─────────────────┘│
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│           Business Layer            │
│  ┌─────────────┐  ┌─────────────────┐│
│  │ Automation  │  │      OCR        ││
│  │   Engine    │  │   Processor     ││
│  └─────────────┘  └─────────────────┘│
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│           Infrastructure Layer      │
│  ┌─────────────┐  ┌─────────────────┐│
│  │Configuration│  │    Logging      ││
│  │   Manager   │  │    System       ││
│  └─────────────┘  └─────────────────┘│
└─────────────────────────────────────┘
```

### Package Structure

```
smart_buyer/
├── __init__.py
├── main.py                    # Entry point
├── core/
│   ├── __init__.py
│   ├── automation.py          # AutoBuyer logic
│   ├── ocr.py                 # OCR processing
│   └── exceptions.py          # Custom exceptions
├── config/
│   ├── __init__.py
│   ├── manager.py             # Configuration management
│   ├── validator.py           # Configuration validation
│   └── defaults.py            # Default configuration
├── ui/
│   ├── __init__.py
│   ├── gui.py                 # GUI interface
│   └── cli.py                 # CLI interface
├── utils/
│   ├── __init__.py
│   ├── logging.py             # Logging configuration
│   └── helpers.py             # Utility functions
└── tests/
    ├── __init__.py
    ├── test_automation.py
    ├── test_config.py
    ├── test_ocr.py
    ├── test_gui.py
    └── test_cli.py
```

## Components and Interfaces

### 1. Core Module (`smart_buyer.core`)

#### AutomationEngine (`automation.py`)
Handles the main automation logic, countdown monitoring, and purchase execution.

```python
class AutomationEngine:
    def __init__(self, config_manager: ConfigManager, ocr_processor: OCRProcessor)
    def start_monitoring(self, callback: Optional[Callable] = None) -> None
    def stop_monitoring(self) -> None
    def execute_purchase(self, callback: Optional[Callable] = None) -> bool
    def is_running(self) -> bool
```

#### OCRProcessor (`ocr.py`)
Handles all OCR-related functionality including image processing and text recognition.

```python
class OCRProcessor:
    def __init__(self, tesseract_path: Optional[str] = None)
    def read_countdown(self, bbox: Tuple[int, int, int, int]) -> Optional[int]
    def preprocess_image(self, image: Image) -> Image
    def parse_countdown_text(self, text: str) -> Optional[int]
```

#### Custom Exceptions (`exceptions.py`)
Defines application-specific exceptions for better error handling.

```python
class SmartBuyerException(Exception): pass
class ConfigurationError(SmartBuyerException): pass
class OCRError(SmartBuyerException): pass
class AutomationError(SmartBuyerException): pass
```

### 2. Configuration Module (`smart_buyer.config`)

#### ConfigManager (`manager.py`)
Manages configuration loading, saving, and access with validation.

```python
class ConfigManager:
    def __init__(self, config_file: str = 'config.json')
    def load_config(self) -> Dict[str, Any]
    def save_config(self) -> None
    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any) -> None
    def validate(self) -> bool
```

#### ConfigValidator (`validator.py`)
Validates configuration values and provides error messages.

```python
class ConfigValidator:
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]
    @staticmethod
    def validate_coordinates(coords: List[int]) -> bool
    @staticmethod
    def validate_timing(value: float) -> bool
```

### 3. UI Module (`smart_buyer.ui`)

#### GUIInterface (`gui.py`)
Handles the graphical user interface using tkinter.

```python
class GUIInterface:
    def __init__(self, automation_engine: AutomationEngine, config_manager: ConfigManager)
    def setup_ui(self) -> None
    def run(self) -> None
    def update_status(self, message: str) -> None
```

#### CLIInterface (`cli.py`)
Handles command-line interface and argument parsing.

```python
class CLIInterface:
    def __init__(self, automation_engine: AutomationEngine)
    def run(self, args: List[str]) -> int
    def parse_arguments(self, args: List[str]) -> argparse.Namespace
```

### 4. Utils Module (`smart_buyer.utils`)

#### Logging Configuration (`logging.py`)
Centralized logging setup and configuration.

```python
def setup_logging(level: str = 'INFO', log_file: str = '抢购日志.log') -> logging.Logger
def get_logger(name: str) -> logging.Logger
```

#### Helper Functions (`helpers.py`)
Utility functions used across the application.

```python
def get_mouse_position_after_delay(delay: int = 3) -> Tuple[int, int]
def format_countdown(seconds: int) -> str
def validate_screen_coordinates(x: int, y: int) -> bool
```

## Data Models

### Configuration Schema

```python
@dataclass
class AppConfig:
    countdown_box: List[int]
    buy_btn_pos: List[int]
    confirm_btn_pos: List[int]
    tesseract_path: str
    click_delay: float
    check_interval: float
    max_retries: int
    enable_confirm_click: bool
    countdown_formats: List[str]
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
```

### Automation State

```python
@dataclass
class AutomationState:
    is_running: bool
    current_countdown: Optional[int]
    retry_count: int
    last_error: Optional[str]
    start_time: Optional[datetime]
```

## Error Handling

### Exception Hierarchy

```python
SmartBuyerException
├── ConfigurationError
│   ├── InvalidConfigError
│   └── ConfigFileError
├── OCRError
│   ├── TesseractNotFoundError
│   ├── ImageProcessingError
│   └── CountdownParsingError
└── AutomationError
    ├── ClickExecutionError
    └── MonitoringError
```

### Error Handling Strategy

1. **Configuration Errors**: Validate configuration on load and provide clear error messages
2. **OCR Errors**: Implement retry logic with exponential backoff
3. **Automation Errors**: Log errors and provide user feedback through callbacks
4. **GUI Errors**: Show error dialogs and update status display
5. **CLI Errors**: Print error messages and exit with appropriate codes

### Logging Strategy

- **DEBUG**: Detailed execution flow, OCR text recognition results
- **INFO**: Normal operation events, configuration changes, monitoring status
- **WARNING**: Recoverable errors, retry attempts, configuration issues
- **ERROR**: Unrecoverable errors, exceptions, critical failures

## Testing Strategy

### Unit Testing

Each module will have comprehensive unit tests covering:

1. **Core Module Tests**:
   - AutomationEngine state management
   - OCRProcessor image processing and text parsing
   - Exception handling scenarios

2. **Configuration Tests**:
   - Configuration loading/saving
   - Validation logic
   - Default value handling

3. **UI Tests**:
   - GUI component initialization
   - CLI argument parsing
   - User interaction handling

### Integration Testing

- Test interaction between AutomationEngine and OCRProcessor
- Test configuration management across modules
- Test GUI and CLI interfaces with core functionality

### Test Structure

```python
# Example test structure
class TestAutomationEngine(unittest.TestCase):
    def setUp(self):
        self.config_manager = Mock()
        self.ocr_processor = Mock()
        self.engine = AutomationEngine(self.config_manager, self.ocr_processor)
    
    def test_start_monitoring_success(self):
        # Test successful monitoring start
    
    def test_stop_monitoring(self):
        # Test monitoring stop
    
    def test_execute_purchase_success(self):
        # Test successful purchase execution
```

### Mocking Strategy

- Mock external dependencies (pyautogui, pytesseract, PIL)
- Mock file system operations for configuration tests
- Mock GUI components for UI tests
- Use dependency injection to facilitate testing

## Migration Strategy

### Phase 1: Extract Core Logic
1. Create package structure
2. Extract AutomationEngine from AutoBuyer class
3. Extract OCRProcessor functionality
4. Implement basic error handling

### Phase 2: Configuration Management
1. Extract and enhance ConfigManager
2. Add configuration validation
3. Implement proper error handling for config operations

### Phase 3: UI Separation
1. Extract GUI logic into separate module
2. Extract CLI logic into separate module
3. Implement proper interfaces between UI and core

### Phase 4: Testing and Documentation
1. Add comprehensive unit tests
2. Add integration tests
3. Update documentation and README
4. Add type hints throughout codebase

### Backward Compatibility

- Maintain existing configuration file format
- Preserve all existing command-line arguments
- Ensure identical GUI behavior and appearance
- Keep the same entry point (`python sjz.py` should still work)

## Performance Considerations

### Optimization Areas

1. **Image Processing**: Cache processed images when possible
2. **Configuration**: Load configuration once and cache in memory
3. **Logging**: Use appropriate logging levels to avoid performance impact
4. **Threading**: Maintain current threading model for GUI responsiveness

### Memory Management

- Properly dispose of PIL Image objects
- Avoid memory leaks in long-running monitoring sessions
- Use context managers for file operations

## Security Considerations

1. **Configuration Files**: Validate all configuration inputs
2. **File Paths**: Sanitize file paths to prevent directory traversal
3. **External Commands**: Validate tesseract path before execution
4. **Error Messages**: Avoid exposing sensitive information in error messages