"""
智能抢购助手的GUI界面模块。

此模块为自动化购买系统的配置、监控和控制
提供基于tkinter的图形用户界面。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime
from typing import Optional, Callable
from ..config.manager import ConfigManager
from ..core.ocr import OCRProcessor
from ..core.automation import AutomationEngine, AutomationState
from ..core.exceptions import SmartBuyerError, ConfigurationError
from ..utils.logging import get_logger, setup_logging
from ..utils.helpers import get_mouse_position_after_delay, parse_coordinate_string


class GUIInterface:
    """智能抢购助手的主GUI界面。"""
    
    def __init__(self):
        """初始化GUI界面。"""
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.ocr_processor = OCRProcessor(
            tesseract_path=self.config_manager.get('tesseract_path', ''),
            ocr_config=self.config_manager.get('ocr_config', '--psm 8')
        )
        self.automation_engine = AutomationEngine(self.ocr_processor)
        
        # GUI components
        self.root = None
        self.status_text = None
        self.start_btn = None
        self.stop_btn = None
        
        # Configuration variables
        self.countdown_box_var = None
        self.buy_btn_var = None
        self.confirm_btn_var = None
        self.check_interval_var = None
        self.tesseract_path_var = None
        self.enable_confirm_var = None
        
        # Threading
        self.monitor_thread = None
        
        self._setup_gui()
        self._load_configuration()
    
    def _setup_gui(self) -> None:
        """设置主GUI窗口和组件。"""
        self.root = tk.Tk()
        window_title = self.config_manager.get('window_title', '智能抢购助手')
        window_geometry = self.config_manager.get('window_geometry', '600x500')
        
        self.root.title(window_title)
        self.root.geometry(window_geometry)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Setup different sections
        self._setup_config_section(main_frame)
        self._setup_button_section(main_frame)
        self._setup_control_section(main_frame)
        self._setup_status_section(main_frame)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_config_section(self, parent: ttk.Frame) -> None:
        """设置配置部分。"""
        config_frame = ttk.LabelFrame(parent, text="配置设置", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Countdown region
        ttk.Label(config_frame, text="倒计时区域 (左,上,右,下):").grid(row=0, column=0, sticky=tk.W)
        self.countdown_box_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.countdown_box_var, width=30).grid(
            row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E)
        )
        
        # Buy button position
        ttk.Label(config_frame, text="购买按钮位置 (x,y):").grid(row=1, column=0, sticky=tk.W)
        self.buy_btn_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.buy_btn_var, width=30).grid(
            row=1, column=1, padx=(10, 0), sticky=(tk.W, tk.E)
        )
        
        # Confirm button position
        ttk.Label(config_frame, text="确认按钮位置 (x,y):").grid(row=2, column=0, sticky=tk.W)
        self.confirm_btn_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.confirm_btn_var, width=30).grid(
            row=2, column=1, padx=(10, 0), sticky=(tk.W, tk.E)
        )
        
        # Check interval
        ttk.Label(config_frame, text="检查间隔(秒):").grid(row=3, column=0, sticky=tk.W)
        self.check_interval_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.check_interval_var, width=30).grid(
            row=3, column=1, padx=(10, 0), sticky=(tk.W, tk.E)
        )
        
        # Tesseract path
        ttk.Label(config_frame, text="Tesseract路径:").grid(row=4, column=0, sticky=tk.W)
        self.tesseract_path_var = tk.StringVar()
        path_frame = ttk.Frame(config_frame)
        path_frame.grid(row=4, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        ttk.Entry(path_frame, textvariable=self.tesseract_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="浏览", command=self._browse_tesseract_path).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Enable confirm click
        self.enable_confirm_var = tk.BooleanVar()
        ttk.Checkbutton(
            config_frame, 
            text="启用确认按钮点击", 
            variable=self.enable_confirm_var
        ).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Configure column weight
        config_frame.columnconfigure(1, weight=1)
    
    def _setup_button_section(self, parent: ttk.Frame) -> None:
        """设置按钮部分。"""
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="获取鼠标位置", command=self._get_mouse_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="测试倒计时识别", command=self._test_countdown).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="测试购买按钮", command=self._test_buy_button).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="保存配置", command=self._save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="加载配置", command=self._load_config_file).pack(side=tk.LEFT, padx=5)
    
    def _setup_control_section(self, parent: ttk.Frame) -> None:
        """设置控制部分。"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="开始监控", command=self._start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            control_frame, 
            text="停止监控", 
            command=self._stop_monitoring, 
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status indicator
        self.status_label = ttk.Label(control_frame, text="状态: 就绪")
        self.status_label.pack(side=tk.RIGHT, padx=5)
    
    def _setup_status_section(self, parent: ttk.Frame) -> None:
        """设置状态显示部分。"""
        status_frame = ttk.LabelFrame(parent, text="状态信息", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(status_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(text_frame, height=15, width=70, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Clear button
        ttk.Button(status_frame, text="清空日志", command=self._clear_status).pack(pady=(10, 0))
    
    def _load_configuration(self) -> None:
        """将配置值加载到GUI组件中。"""
        try:
            config = self.config_manager.get_all()
            
            self.countdown_box_var.set(str(config.get('countdown_box', [100, 200, 300, 240])))
            self.buy_btn_var.set(str(config.get('buy_btn_pos', [500, 600])))
            self.confirm_btn_var.set(str(config.get('confirm_btn_pos', [550, 650])))
            self.check_interval_var.set(str(config.get('check_interval', 0.1)))
            self.tesseract_path_var.set(config.get('tesseract_path', ''))
            self.enable_confirm_var.set(config.get('enable_confirm_click', True))
            
            self._update_status("配置已加载")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self._update_status(f"配置加载失败: {e}")
    
    def _save_current_config(self) -> bool:
        """将当前GUI值保存到配置中。"""
        try:
            # Parse and validate configuration values
            countdown_box = parse_coordinate_string(self.countdown_box_var.get())
            buy_btn_pos = parse_coordinate_string(self.buy_btn_var.get())
            confirm_btn_pos = parse_coordinate_string(self.confirm_btn_var.get())
            check_interval = float(self.check_interval_var.get())
            tesseract_path = self.tesseract_path_var.get().strip()
            enable_confirm = self.enable_confirm_var.get()
            
            # Update configuration
            updates = {
                'countdown_box': countdown_box,
                'buy_btn_pos': buy_btn_pos,
                'confirm_btn_pos': confirm_btn_pos,
                'check_interval': check_interval,
                'tesseract_path': tesseract_path,
                'enable_confirm_click': enable_confirm
            }
            
            success = self.config_manager.update(updates)
            if success:
                # Update OCR processor with new tesseract path
                current_tesseract_path = getattr(self.ocr_processor, 'tesseract_path', '')
                if tesseract_path != current_tesseract_path:
                    self.ocr_processor = OCRProcessor(
                        tesseract_path=tesseract_path,
                        ocr_config=self.config_manager.get('ocr_config', '--psm 8')
                    )
                    self.automation_engine = AutomationEngine(self.ocr_processor)
                
                return True
            else:
                self._update_status("配置验证失败，请检查输入值")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            self._update_status(f"配置保存失败: {e}")
            return False
    
    def _get_mouse_position(self) -> None:
        """延迟后获取鼠标位置。"""
        self._update_status("请将鼠标移动到目标位置，3秒后获取坐标...")
        
        def get_position():
            try:
                x, y = get_mouse_position_after_delay(3.0)
                self.root.after(0, lambda: self._update_status(f"当前鼠标位置: ({x}, {y})"))
            except Exception as e:
                self.root.after(0, lambda: self._update_status(f"获取鼠标位置失败: {e}"))
        
        threading.Thread(target=get_position, daemon=True).start()
    
    def _test_countdown(self) -> None:
        """测试倒计时识别。"""
        if not self._save_current_config():
            return
        
        def test_ocr():
            try:
                countdown_box = tuple(self.config_manager.get('countdown_box'))
                countdown_formats = self.config_manager.get('countdown_formats')
                
                seconds = self.ocr_processor.read_countdown(
                    region=countdown_box,
                    countdown_formats=countdown_formats
                )
                
                if seconds is not None:
                    message = f"倒计时识别成功: {seconds}秒"
                else:
                    message = "倒计时识别失败，请检查区域设置和倒计时显示"
                
                self.root.after(0, lambda: self._update_status(message))
                
            except Exception as e:
                self.root.after(0, lambda: self._update_status(f"倒计时测试失败: {e}"))
        
        threading.Thread(target=test_ocr, daemon=True).start()
    
    def _test_buy_button(self) -> None:
        """测试购买按钮点击位置。"""
        if not self._save_current_config():
            return
        
        try:
            buy_btn_pos = tuple(self.config_manager.get('buy_btn_pos'))
            success = self.automation_engine.test_click_position(buy_btn_pos)
            
            if success:
                self._update_status(f"购买按钮测试成功: {buy_btn_pos}")
            else:
                self._update_status(f"购买按钮测试失败: {buy_btn_pos}")
                
        except Exception as e:
            self._update_status(f"购买按钮测试出错: {e}")
    
    def _save_config(self) -> None:
        """将配置保存到文件。"""
        if self._save_current_config():
            success = self.config_manager.save_config()
            if success:
                self._update_status("配置已保存到文件")
            else:
                self._update_status("配置文件保存失败")
    
    def _load_config_file(self) -> None:
        """从文件加载配置。"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            success = self.config_manager.load_from_file(file_path)
            if success:
                self._load_configuration()
                self._update_status(f"已加载配置文件: {file_path}")
            else:
                self._update_status(f"配置文件加载失败: {file_path}")
    
    def _browse_tesseract_path(self) -> None:
        """浏览Tesseract可执行文件路径。"""
        file_path = filedialog.askopenfilename(
            title="选择Tesseract可执行文件",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        
        if file_path:
            self.tesseract_path_var.set(file_path)
    
    def _start_monitoring(self) -> None:
        """开始倒计时监控。"""
        if not self._save_current_config():
            return
        
        if self.automation_engine.is_running():
            messagebox.showwarning("警告", "监控已在运行中")
            return
        
        try:
            # Validate configuration
            countdown_region = tuple(self.config_manager.get('countdown_box'))
            buy_button_pos = tuple(self.config_manager.get('buy_btn_pos'))
            confirm_button_pos = tuple(self.config_manager.get('confirm_btn_pos'))
            
            is_valid, errors = self.automation_engine.validate_configuration(
                countdown_region=countdown_region,
                buy_button_pos=buy_button_pos,
                confirm_button_pos=confirm_button_pos
            )
            
            if not is_valid:
                error_msg = "\\n".join(errors)
                messagebox.showerror("配置错误", f"配置验证失败:\\n{error_msg}")
                return
            
            # Update UI state
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="状态: 监控中")
            self._update_status("开始监控倒计时...")
            
            # Start monitoring in separate thread
            self.monitor_thread = threading.Thread(
                target=self._run_monitoring,
                daemon=True
            )
            self.monitor_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            self._update_status(f"启动监控失败: {e}")
            self._reset_ui_state()
    
    def _run_monitoring(self) -> None:
        """在单独线程中运行监控。"""
        try:
            config = self.config_manager.get_all()
            
            self.automation_engine.start_monitoring(
                countdown_region=tuple(config['countdown_box']),
                countdown_formats=config['countdown_formats'],
                buy_button_pos=tuple(config['buy_btn_pos']),
                confirm_button_pos=tuple(config['confirm_btn_pos']) if config['enable_confirm_click'] else None,
                check_interval=config['check_interval'],
                click_delay=config['click_delay'],
                max_retries=config['max_retries'],
                enable_confirm_click=config['enable_confirm_click'],
                callback=self._monitoring_callback
            )
            
        except Exception as e:
            self.logger.error(f"Monitoring failed: {e}")
            self.root.after(0, lambda: self._update_status(f"监控执行失败: {e}"))
        
        finally:
            self.root.after(0, self._reset_ui_state)
    
    def _monitoring_callback(self, message: str) -> None:
        """监控状态更新的回调函数。"""
        self.root.after(0, lambda: self._update_status(message))
    
    def _stop_monitoring(self) -> None:
        """停止倒计时监控。"""
        if self.automation_engine.is_running():
            self.automation_engine.stop_monitoring()
            self._update_status("正在停止监控...")
        else:
            self._reset_ui_state()
    
    def _reset_ui_state(self) -> None:
        """将UI重置为初始状态。"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        state = self.automation_engine.get_state()
        if state == AutomationState.COMPLETED:
            self.status_label.config(text="状态: 完成")
        elif state == AutomationState.ERROR:
            self.status_label.config(text="状态: 错误")
        elif state == AutomationState.STOPPED:
            self.status_label.config(text="状态: 已停止")
        else:
            self.status_label.config(text="状态: 就绪")
    
    def _update_status(self, message: str) -> None:
        """更新状态显示。"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\\n"
        
        self.status_text.insert(tk.END, formatted_message)
        self.status_text.see(tk.END)
        self.root.update_idletasks()
    
    def _clear_status(self) -> None:
        """清空状态显示。"""
        self.status_text.delete(1.0, tk.END)
    
    def _on_closing(self) -> None:
        """处理窗口关闭。"""
        if self.automation_engine.is_running():
            if messagebox.askokcancel("退出", "监控正在运行，确定要退出吗？"):
                self.automation_engine.stop_monitoring()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self) -> None:
        """运行GUI应用程序。"""
        try:
            self.logger.info("Starting GUI application")
            self._update_status("智能抢购助手已启动")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"GUI application error: {e}")
            messagebox.showerror("错误", f"应用程序错误: {e}")
        finally:
            self.logger.info("GUI application closed")