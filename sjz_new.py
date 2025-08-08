#!/usr/bin/env python3
"""
智能抢购助手的向后兼容入口点。

此文件在使用新的模块化架构的同时，
保持与原始sjz.py的向后兼容性。
"""

import sys
import os

# 将当前目录添加到Python路径以确保可以导入smart_buyer
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from smart_buyer.main import main
    
    if __name__ == '__main__':
        sys.exit(main())
        
except ImportError as e:
    print(f"导入错误: {e}", file=sys.stderr)
    print("请确保smart_buyer包已正确安装或在当前目录中", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"启动失败: {e}", file=sys.stderr)
    sys.exit(1)