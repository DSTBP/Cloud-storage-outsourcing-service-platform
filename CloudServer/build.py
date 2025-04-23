import PyInstaller.__main__
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义需要包含的数据文件
datas = [
    ('favicon.ico', '.'),
    ('utils', 'utils'),
    ('services', 'services'),
    ('business', 'business'),
    ('builtin_tools', 'builtin_tools'),
]

# 构建PyInstaller命令
pyinstaller_args = [
    'server_gui.py',  # 主程序文件
    '--name=CloudServer',  # 可执行文件名
    '--onefile',  # 打包成单个文件
    '--windowed',  # 不显示控制台窗口
    '--icon=favicon.ico',  # 程序图标
    '--add-data=favicon.ico;.',  # 添加图标文件
    '--add-data=utils;utils',  # 添加utils目录
    '--add-data=services;services',  # 添加services目录
    '--add-data=business;business',  # 添加business目录
    '--add-data=builtin_tools;builtin_tools',  # 添加builtin_tools目录
    '--clean',  # 清理临时文件
]

# 添加所有数据文件
for src, dst in datas:
    pyinstaller_args.append(f'--add-data={src};{dst}')

# 执行打包命令
PyInstaller.__main__.run(pyinstaller_args)
