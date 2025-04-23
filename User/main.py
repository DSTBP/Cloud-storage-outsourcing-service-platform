from business.webview_api import *
import webview
import os
import sys
from loguru import logger
import traceback
from screeninfo import get_monitors  # 用于获取屏幕信息


# 配置日志记录
def setup_logging():
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'error.log')
    logger.add(log_path, rotation="500 MB", level="DEBUG")


def get_screen_resolution():
    # 获取主显示器的分辨率
    for m in get_monitors():
        if m.is_primary:
            return m.width, m.height
    return 1200, 800  # 默认值


def on_loaded():
    """在 webview 加载后自动调整窗口大小"""
    try:
        width, height = get_screen_resolution()
        window = webview.windows[0]
        window.resize(width, height)
        window.restore()  # 保证窗口是正常状态
        logger.info(f"窗口已调整为最大化：{width}x{height}")
    except Exception as e:
        logger.error(f"调整窗口大小时发生错误: {e}")


def main():
    try:
        setup_logging()
        logger.info("应用程序启动")

        # 获取当前文件所在目录
        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable)
            html_path = 'UI/index.html'
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            html_path = os.path.join(current_dir, 'UI', 'index.html')

        logger.info(f"当前目录: {current_dir}")
        logger.info(f"HTML路径: {html_path}")

        # 创建 webview 窗口（初始大小可以设置一个默认）
        window = webview.create_window(
            '云存储系统',
            html_path,
            width=1200,
            height=800,
            resizable=True,
            min_size=(800, 600),
            fullscreen=False,
            js_api=None
        )

        # 注册 Python 函数供 JS 调用
        window.expose(generate_keypair, match_keypair, keypair_format_conversion,
                      upload_file, select_file, download_file, save_file, write_file)

        # 启动 webview 并自动最大化窗口
        webview.start(on_loaded, debug=False)

    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        input("按回车键退出...")


if __name__ == '__main__':
    main()
