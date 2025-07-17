#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能抢购助手 - 演示版本
不依赖外部库的功能演示
"""

import time
import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
import os
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('抢购日志_演示.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "countdown_box": [100, 200, 300, 240],
    "buy_btn_pos": [500, 600],
    "confirm_btn_pos": [550, 650],
    "click_delay": 0.05,
    "check_interval": 0.1,
    "max_retries": 3,
    "enable_confirm_click": True,
    "demo_countdown": 10  # 演示用倒计时
}

class ConfigManager:
    def __init__(self, config_file='demo_config.json'):
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

class DemoAutoBuyer:
    """演示版自动购买器，模拟真实功能"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.is_running = False
        self.demo_countdown = self.config_manager.get('demo_countdown', 10)
        
    def read_countdown(self):
        """模拟倒计时读取"""
        try:
            if self.demo_countdown > 0:
                return self.demo_countdown
            return 0
        except Exception as e:
            logger.error(f"读取倒计时失败: {e}")
            return None
    
    def wait_and_click(self, callback=None):
        """模拟监控和点击过程"""
        self.is_running = True
        logger.info("开始监控倒计时...")
        
        retry_count = 0
        max_retries = self.config_manager.get('max_retries')
        check_interval = self.config_manager.get('check_interval')
        
        # 重置演示倒计时
        self.demo_countdown = self.config_manager.get('demo_countdown', 10)
        
        while self.is_running and self.demo_countdown > 0:
            try:
                secs = self.read_countdown()
                
                if callback:
                    callback(f"剩余秒数: {secs if secs is not None else '识别失败'}")
                
                logger.info(f"剩余秒数: {secs}")
                
                if secs is None:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.warning("连续识别失败，可能倒计时已结束")
                        break
                    time.sleep(check_interval)
                    continue
                
                retry_count = 0
                
                if secs <= 0:
                    break
                
                # 模拟倒计时递减
                self.demo_countdown -= 1
                time.sleep(1)  # 演示用，每秒递减
                
            except Exception as e:
                logger.error(f"监控过程出错: {e}")
                time.sleep(check_interval)
        
        if self.is_running:
            self.execute_purchase(callback)
        
        self.is_running = False
    
    def execute_purchase(self, callback=None):
        """模拟购买操作"""
        try:
            logger.info("倒计时结束，开始执行购买操作")
            if callback:
                callback("正在执行购买操作...")
            
            click_delay = self.config_manager.get('click_delay')
            buy_btn_pos = self.config_manager.get('buy_btn_pos')
            
            # 模拟点击购买按钮
            time.sleep(click_delay)
            logger.info(f"已点击购买按钮: {buy_btn_pos}")
            
            # 模拟点击确认按钮
            if self.config_manager.get('enable_confirm_click'):
                confirm_btn_pos = self.config_manager.get('confirm_btn_pos')
                time.sleep(click_delay)
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

class DemoGUI:
    """演示版图形界面"""
    
    def __init__(self):
        self.auto_buyer = DemoAutoBuyer()
        self.root = tk.Tk()
        self.root.title("智能抢购助手 - 演示版")
        self.root.geometry("700x600")
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="智能抢购助手 - 演示版", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 说明文字
        info_text = """这是演示版本，展示了优化后的功能结构：
• 配置管理系统
• 日志记录功能
• 图形用户界面
• 错误处理机制
• 多线程支持

实际版本需要安装 pytesseract, Pillow, pyautogui 等依赖包。"""
        
        info_label = ttk.Label(main_frame, text=info_text, justify=tk.LEFT, foreground='blue')
        info_label.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="配置设置", padding="10")
        config_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 演示倒计时设置
        ttk.Label(config_frame, text="演示倒计时(秒):").grid(row=0, column=0, sticky=tk.W)
        self.demo_countdown_var = tk.StringVar(value=str(self.auto_buyer.config_manager.get('demo_countdown')))
        ttk.Entry(config_frame, textvariable=self.demo_countdown_var, width=20).grid(row=0, column=1, padx=(10, 0))
        
        # 检查间隔
        ttk.Label(config_frame, text="检查间隔(秒):").grid(row=1, column=0, sticky=tk.W)
        self.check_interval_var = tk.StringVar(value=str(self.auto_buyer.config_manager.get('check_interval')))
        ttk.Entry(config_frame, textvariable=self.check_interval_var, width=20).grid(row=1, column=1, padx=(10, 0))
        
        # 购买按钮位置（演示用）
        ttk.Label(config_frame, text="购买按钮位置:").grid(row=2, column=0, sticky=tk.W)
        self.buy_btn_var = tk.StringVar(value=str(self.auto_buyer.config_manager.get('buy_btn_pos')))
        ttk.Entry(config_frame, textvariable=self.buy_btn_var, width=20).grid(row=2, column=1, padx=(10, 0))
        
        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="重置配置", command=self.reset_config).pack(side=tk.LEFT, padx=5)
        
        # 控制区域
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="开始演示", command=self.start_demo)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="停止演示", command=self.stop_demo, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="状态信息", padding="10")
        status_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.status_text = tk.Text(status_frame, height=12, width=80)
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # 初始化状态
        self.update_status("演示程序已启动，可以开始测试功能")
        
    def update_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def save_config(self):
        try:
            demo_countdown = int(self.demo_countdown_var.get())
            check_interval = float(self.check_interval_var.get())
            buy_btn_pos = eval(self.buy_btn_var.get())
            
            self.auto_buyer.config_manager.set('demo_countdown', demo_countdown)
            self.auto_buyer.config_manager.set('check_interval', check_interval)
            self.auto_buyer.config_manager.set('buy_btn_pos', buy_btn_pos)
            
            self.auto_buyer.config_manager.save_config()
            self.update_status("配置已保存")
            
        except Exception as e:
            self.update_status(f"配置保存失败: {e}")
            
    def reset_config(self):
        self.auto_buyer.config_manager.config = DEFAULT_CONFIG.copy()
        self.refresh_ui()
        self.update_status("配置已重置为默认值")
        
    def refresh_ui(self):
        config = self.auto_buyer.config_manager.config
        self.demo_countdown_var.set(str(config['demo_countdown']))
        self.check_interval_var.set(str(config['check_interval']))
        self.buy_btn_var.set(str(config['buy_btn_pos']))
        
    def start_demo(self):
        self.save_config()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.update_status("开始演示监控过程...")
        
        # 在新线程中运行演示
        self.demo_thread = threading.Thread(
            target=self.auto_buyer.wait_and_click,
            args=(self.update_status,)
        )
        self.demo_thread.daemon = True
        self.demo_thread.start()
        
    def stop_demo(self):
        self.auto_buyer.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("演示已停止")
        
    def run(self):
        self.root.mainloop()

def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1] == '--console':
            # 控制台演示模式
            auto_buyer = DemoAutoBuyer()
            print("演示模式：准备监控倒计时...")
            time.sleep(2)
            auto_buyer.wait_and_click()
        else:
            # GUI演示模式
            app = DemoGUI()
            app.run()
    except KeyboardInterrupt:
        logger.info("演示程序被用户中断")
    except Exception as e:
        logger.error(f"演示程序运行出错: {e}")

if __name__ == '__main__':
    main()