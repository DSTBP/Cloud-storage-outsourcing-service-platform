'''
Description: 
Author: DSTBP
Date: 2025-04-22 15:14:04
LastEditTime: 2025-04-22 15:14:13
LastEditors: DSTBP
'''
import PyInstaller.__main__
import os
import sys

def build():
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定义 PyInstaller 参数
    params = [
        'main.py',  # 主程序入口
        '--name=云存储系统',  # 生成的可执行文件名
        '--windowed',  # 不显示控制台窗口
        '--onefile',  # 打包成单个文件
        '--icon=UI/static/images/favicon.ico',  # 程序图标
        '--add-data=UI;UI',  # 添加 UI 目录
        '--hidden-import=webview.platforms.cef',  # 添加必要的隐藏导入
        '--hidden-import=webview.platforms.win32',
        '--hidden-import=webview.platforms.edgechromium',
        '--clean',  # 清理临时文件
        '--noconfirm',  # 覆盖输出目录
    ]
    
    # 执行打包
    PyInstaller.__main__.run(params)

if __name__ == '__main__':
    build() 