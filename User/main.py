from business.webview_api import *
import webview
import os

def main():
    # 获取当前文件所在目录的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建HTML文件的绝对路径
    html_path = os.path.join(current_dir, 'UI', 'index.html')

    # 创建webview窗口
    window = webview.create_window(
        '云存储系统',
        html_path,
        width=2400,
        height=1200,
        resizable=True,
        min_size=(800, 600),
        # fullscreen=True,
        js_api=None
    )

    # 注册Python函数供JS调用
    window.expose(generate_keypair, match_keypair, keypair_format_conversion, upload_file, select_file, download_file, save_file, write_file)

    # 启动webview
    webview.start(debug=True)

if __name__ == '__main__':
    main()