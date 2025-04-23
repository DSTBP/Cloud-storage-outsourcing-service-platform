'''
Description: 
Author: DSTBP
Date: 2025-04-22 17:29:18
LastEditTime: 2025-04-23 10:42:01
LastEditors: DSTBP
'''
import PyInstaller.__main__
import os
import sys

# 检查图标文件
if not os.path.exists('favicon.ico'):
    raise FileNotFoundError("找不到 favicon.ico 文件，请确保它在当前目录中")

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义打包参数
params = [
    'system_gui.py',  # 主程序入口
    '--name=SystemCenter',  # 生成的可执行文件名
    '--onefile',  # 打包成单个文件
    '--windowed',  # 不显示控制台窗口
    '--icon=favicon.ico',  # 程序图标
    '--add-data=favicon.ico;.',
    '--add-data=utils;utils',  # 添加utils目录
    '--add-data=services;services',  # 添加services目录
    '--add-data=business;business',  # 添加business目录
    '--add-data=builtin_tools;builtin_tools',  # 添加builtin_tools目录
    '--hidden-import=loguru',  # 添加隐藏导入
    '--clean',  # 清理临时文件
]

# 执行打包
PyInstaller.__main__.run(params)