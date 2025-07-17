import time
import pytesseract
from PIL import ImageGrab, Image
import pyautogui
import re
import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime
import os
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('抢购日志.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "countdown_box": [100, 200, 300, 240],
    "buy_btn_pos": [500, 600],
    "confirm_btn_pos": [550, 650],
    "tesseract_path": "",
    "click_delay": 0.05,
    "check_interval": 0.1,
    "max_retries": 3,
    "enable_confirm_click": True,
    "countdown_formats": [
        r'(\d{1,2}):(\d{2}):(\d{2})',
        r'(\d{1,2})分(\d{2})秒',
        r'(\d+)秒'
    ]
}

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("配置已保存")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value

class AutoBuyer:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.is_running = False
        self.setup_tesseract()
        
    def setup_tesseract(self):
        tesseract_path = self.config_manager.get('tesseract_path')
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
    def read_countdown(self):
        try:
            countdown_box = tuple(self.config_manager.get('countdown_box'))
            img = ImageGrab.grab(bbox=countdown_box)
            
            # 图像预处理
            gray = img.convert('L')
            # 增强对比度
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(2.0)
            
            text = pytesseract.image_to_string(enhanced, config='--psm 8')
            logger.debug(f"OCR识别文本: {text}")
            
            # 尝试多种倒计时格式
            formats = self.config_manager.get('countdown_formats')
            
            for fmt in formats:
                m = re.search(fmt, text)
                if m:
                    groups = m.groups()
                    if len(groups) == 3:  # HH:MM:SS格式
                        h, m_, s = map(int, groups)
                        return h * 3600 + m_ * 60 + s
                    elif len(groups) == 2:  # MM分SS秒格式
                        m_, s = map(int, groups)
                        return m_ * 60 + s
                    elif len(groups) == 1:  # SS秒格式
                        return int(groups[0])
            
            return None
            
        except Exception as e:
            logger.error(f"读取倒计时失败: {e}")
            return None

    def wait_and_click(self, callback=None):
        self.is_running = True
        logger.info("开始监控倒计时...")
        
        retry_count = 0
        max_retries = self.config_manager.get('max_retries')
        check_interval = self.config_manager.get('check_interval')
        
        while self.is_running:
            try:
                secs = self.read_countdown()
                
                if callback:
                    callback(f"剩余秒数: {secs if secs is not None else '识别失败'}")
                
                logger.info(f"剩余秒数: {secs}")
                
                if secs is None:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.warning("连续识别失败，可能倒计时已结束或区域设置错误")
                        break
                    time.sleep(check_interval)
                    continue
                
                retry_count = 0  # 重置重试计数
                
                if secs <= 0:
                    break
                    
                time.sleep(min(check_interval, secs))
                
            except Exception as e:
                logger.error(f"监控过程出错: {e}")
                time.sleep(check_interval)
        
        if self.is_running:
            self.execute_purchase(callback)
        
        self.is_running = False
    
    def execute_purchase(self, callback=None):
        try:
            logger.info("倒计时结束，开始执行购买操作")
            if callback:
                callback("正在执行购买操作...")
            
            click_delay = self.config_manager.get('click_delay')
            buy_btn_pos = tuple(self.config_manager.get('buy_btn_pos'))
            
            # 点击购买按钮
            pyautogui.moveTo(*buy_btn_pos, duration=click_delay)
            pyautogui.click()
            logger.info(f"已点击购买按钮: {buy_btn_pos}")
            
            time.sleep(click_delay)
            
            # 点击确认按钮（如果启用）
            if self.config_manager.get('enable_confirm_click'):
                confirm_btn_pos = tuple(self.config_manager.get('confirm_btn_pos'))
                pyautogui.moveTo(*confirm_btn_pos, duration=click_delay)
                pyautogui.click()
                logger.info(f"已点击确认按钮: {confirm_btn_pos}")
            
            logger.info("购买操作完成")
            if callback:
                callback("购买操作完成！")
                
        except Exception as e:
            logger.error(f"执行购买操作失败: {e}")
            if callback:
                callback(f"购买操作失败: {e}")
    
    def stop(self):
        self.is_running = False
        logger.info("停止监控")

class AutoBuyerGUI:
    def __init__(self):
        self.auto_buyer = AutoBuyer()
        self.root = tk.Tk()
        self.root.title("智能抢购助手")
        self.root.geometry("600x500")
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="配置设置", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 倒计时区域设置
        ttk.Label(config_frame, text="倒计时区域 (左,上,右,下):").grid(row=0, column=0, sticky=tk.W)
        self.countdown_box_var = tk.StringVar(value=str(self.auto_buyer.config_manager.get('countdown_box')))
        ttk.Entry(config_frame, textvariable=self.countdown_box_var, width=30).grid(row=0, column=1, padx=(10, 0))
        
        # 购买按钮位置
        ttk.Label(config_frame, text="购买按钮位置 (x,y):").grid(row=1, column=0, sticky=tk.W)
        self.buy_btn_var = tk.StringVar(value=str(self.auto_buyer.config_manager.get('buy_btn_pos')))
        ttk.Entry(config_frame, textvariable=self.buy_btn_var, width=30).grid(row=1, column=1, padx=(10, 0))
        
        # 确认按钮位置
        ttk.Label(config_frame, text="确认按钮位置 (x,y):").grid(row=2, column=0, sticky=tk.W)
        self.confirm_btn_var = tk.StringVar(value=str(self.auto_buyer.config_manager.get('confirm_btn_pos')))
        ttk.Entry(config_frame, textvariable=self.confirm_btn_var, width=30).grid(row=2, column=1, padx=(10, 0))
        
        # 检查间隔
        ttk.Label(config_frame, text="检查间隔(秒):").grid(row=3, column=0, sticky=tk.W)
        self.check_interval_var = tk.StringVar(value=str(self.auto_buyer.config_manager.get('check_interval')))
        ttk.Entry(config_frame, textvariable=self.check_interval_var, width=30).grid(row=3, column=1, padx=(10, 0))
        
        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="获取鼠标位置", command=self.get_mouse_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="测试倒计时识别", command=self.test_countdown).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="加载配置", command=self.load_config).pack(side=tk.LEFT, padx=5)
        
        # 控制区域
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="开始监控", command=self.start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="停止监控", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="状态信息", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.status_text = tk.Text(status_frame, height=15, width=70)
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
    def update_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def get_mouse_position(self):
        self.update_status("请将鼠标移动到目标位置，3秒后获取坐标...")
        self.root.after(3000, self._get_position)
        
    def _get_position(self):
        x, y = pyautogui.position()
        self.update_status(f"当前鼠标位置: ({x}, {y})")
        
    def test_countdown(self):
        self.save_current_config()
        secs = self.auto_buyer.read_countdown()
        if secs is not None:
            self.update_status(f"倒计时识别成功: {secs}秒")
        else:
            self.update_status("倒计时识别失败，请检查区域设置")
            
    def save_current_config(self):
        try:
            # 解析并保存当前配置
            countdown_box = eval(self.countdown_box_var.get())
            buy_btn_pos = eval(self.buy_btn_var.get())
            confirm_btn_pos = eval(self.confirm_btn_var.get())
            check_interval = float(self.check_interval_var.get())
            
            self.auto_buyer.config_manager.set('countdown_box', countdown_box)
            self.auto_buyer.config_manager.set('buy_btn_pos', buy_btn_pos)
            self.auto_buyer.config_manager.set('confirm_btn_pos', confirm_btn_pos)
            self.auto_buyer.config_manager.set('check_interval', check_interval)
            
        except Exception as e:
            self.update_status(f"配置格式错误: {e}")
            
    def save_config(self):
        self.save_current_config()
        self.auto_buyer.config_manager.save_config()
        self.update_status("配置已保存")
        
    def load_config(self):
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.auto_buyer.config_manager.config_file = file_path
            self.auto_buyer.config_manager.config = self.auto_buyer.config_manager.load_config()
            self.refresh_ui()
            self.update_status(f"已加载配置文件: {file_path}")
            
    def refresh_ui(self):
        config = self.auto_buyer.config_manager.config
        self.countdown_box_var.set(str(config['countdown_box']))
        self.buy_btn_var.set(str(config['buy_btn_pos']))
        self.confirm_btn_var.set(str(config['confirm_btn_pos']))
        self.check_interval_var.set(str(config['check_interval']))
        
    def start_monitoring(self):
        self.save_current_config()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.update_status("开始监控倒计时...")
        
        # 在新线程中运行监控
        self.monitor_thread = threading.Thread(
            target=self.auto_buyer.wait_and_click,
            args=(self.update_status,)
        )
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        self.auto_buyer.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("已停止监控")
        
    def run(self):
        self.root.mainloop()

def main():
    try:
        # 检查是否有命令行参数
        if len(sys.argv) > 1 and sys.argv[1] == '--console':
            # 控制台模式
            auto_buyer = AutoBuyer()
            print("准备监控倒计时区域...")
            time.sleep(2)
            auto_buyer.wait_and_click()
        else:
            # GUI模式
            app = AutoBuyerGUI()
            app.run()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")

if __name__ == '__main__':
    main()