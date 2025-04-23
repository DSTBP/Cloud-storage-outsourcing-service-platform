import json
import sys
import time
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import queue
import os
from tkinter import messagebox
from loguru import logger
from business.core import CloudServer
from business.config import CloudServerConfig

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        # PyInstaller创建临时文件夹,将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class CloudServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("云服务器集群控制面板")
        self.root.geometry("1000x800")
        self.root.iconbitmap(get_resource_path("favicon.ico"))

        # 创建日志队列
        self.log_queue = queue.Queue()

        # 创建服务器列表
        self.servers = []
        self.server_threads = []

        # 获取默认配置
        self.default_config = CloudServerConfig()

        # 定义配置属性
        self.system_center_url = None  # 系统中心地址输入框
        self.mongo_uri = None         # MongoDB URI输入框
        self.db_name = None           # 数据库名称输入框
        self.enc_shares_collection = None  # 加密份额集合输入框
        self.base_port = None         # 服务器基础端口输入框
        self.storage_path = None      # 密钥存储路径输入框
        self.server_count = None      # 服务器数量输入框
        self.log_path = None          # 日志路径输入框

        # 创建主框架
        self.create_widgets()

        # 配置日志处理器
        self.setup_logger()

    def create_widgets(self):
        # 创建输入框架
        input_frame = ttk.LabelFrame(self.root, text="服务器配置", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 配置列权重，使输入框可以自动拉伸
        input_frame.columnconfigure(1, weight=1)
        
        # 创建输入字段
        # 端口号
        ttk.Label(input_frame, text="服务器基础端口:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.base_port = ttk.Entry(input_frame)
        self.base_port.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.base_port.insert(0, str(self.default_config.port))
        
        # 服务器数量
        ttk.Label(input_frame, text="服务器数量:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.server_count = ttk.Entry(input_frame, validate="key", validatecommand=(self.root.register(self.validate_number), '%P'))
        self.server_count.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.server_count.insert(0, "5")
        
        # 系统中心配置
        system_frame = ttk.LabelFrame(self.root, text="系统中心配置", padding=10)
        system_frame.pack(fill=tk.X, padx=5, pady=5)
        system_frame.columnconfigure(1, weight=1)
        
        # 系统中心地址
        ttk.Label(system_frame, text="系统中心地址:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.system_center_url = ttk.Entry(system_frame)
        self.system_center_url.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.system_center_url.insert(0, self.default_config.system_center_url)
        
        # MongoDB配置
        mongo_frame = ttk.LabelFrame(self.root, text="MongoDB配置", padding=10)
        mongo_frame.pack(fill=tk.X, padx=5, pady=5)
        mongo_frame.columnconfigure(1, weight=1)
        
        # MongoDB URI
        ttk.Label(mongo_frame, text="MongoDB URI:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.mongo_uri = ttk.Entry(mongo_frame)
        self.mongo_uri.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.mongo_uri.insert(0, self.default_config.mongo_uri)
        
        # 数据库名称
        ttk.Label(mongo_frame, text="数据库名称:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.db_name = ttk.Entry(mongo_frame)
        self.db_name.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.db_name.insert(0, self.default_config.db_name)
        
        # 加密份额集合
        ttk.Label(mongo_frame, text="加密份额集合:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.enc_shares_collection = ttk.Entry(mongo_frame)
        self.enc_shares_collection.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.enc_shares_collection.insert(0, self.default_config.enc_shares_collection)
        
        # 存储路径配置
        storage_frame = ttk.LabelFrame(self.root, text="存储路径配置", padding=10)
        storage_frame.pack(fill=tk.X, padx=5, pady=5)
        storage_frame.columnconfigure(1, weight=1)
        
        # 密钥存储路径
        ttk.Label(storage_frame, text="密钥存储路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.storage_path = ttk.Entry(storage_frame)
        self.storage_path.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        ttk.Button(storage_frame, text="浏览", command=lambda: self.browse_path(self.storage_path)).grid(row=0, column=2, padx=5)
        
        # 日志配置
        log_frame = ttk.LabelFrame(self.root, text="日志配置", padding=10)
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        log_frame.columnconfigure(1, weight=1)
        
        # 日志路径
        ttk.Label(log_frame, text="日志路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.log_path = ttk.Entry(log_frame)
        self.log_path.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.log_path.insert(0, os.path.join(os.getcwd(), "log"))
        ttk.Button(log_frame, text="浏览", command=lambda: self.browse_path(self.log_path)).grid(row=0, column=2, padx=5)
        
        # 按钮框架
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_button = ttk.Button(button_frame, text="启动服务器集群", command=self.start_servers)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="停止服务器集群", command=self.stop_servers, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 日志输出框
        log_display_frame = ttk.LabelFrame(self.root, text="日志输出", padding=10)
        log_display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_display_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 设置日志文本标签
        self.log_text.tag_configure("DEBUG", foreground="light blue")
        self.log_text.tag_configure("INFO", foreground="grey")
        self.log_text.tag_configure("SUCCESS", foreground="green")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red", font=("Courier", 10, "bold"))
        
    def create_input_field(self, parent, label_text, field_name, row, default_value=""):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=5)
        setattr(self, field_name, ttk.Entry(parent))
        getattr(self, field_name).grid(row=row, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        if default_value:
            getattr(self, field_name).insert(0, default_value)
        
    def validate_number(self, value):
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
            
    def browse_path(self, entry_widget):
        path = filedialog.askdirectory()
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)
            
    def setup_logger(self):
        # 配置日志处理器
        logger.remove()  # 移除默认处理器
        
        # 添加GUI日志处理器
        logger.add(self.log_queue.put, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
        
        # 确保日志目录存在
        log_path = self.log_path.get()
        if not os.path.exists(log_path):
            os.makedirs(log_path)
            
        # 添加文件处理器
        logger.add(os.path.join(log_path, "server.log"), rotation="1 day", retention="7 days")
            
    def update_log_display(self):
        while not self.log_queue.empty():
            log_entry = self.log_queue.get()
            level = log_entry.split(" | ")[1]
            self.log_text.insert(tk.END, log_entry + "\n", level)
            self.log_text.see(tk.END)
        self.root.after(200, self.update_log_display)

    @staticmethod
    def list_subdirectories(storage_path):
        result = []

        # 判断目录是否存在
        if not os.path.isdir(storage_path):
            os.makedirs(storage_path, exist_ok=True)
            return result

        # 遍历 base_dir 下的所有子目录
        for subdir in os.listdir(storage_path):
            subdir_path = os.path.join(storage_path, subdir)
            info_path = os.path.join(subdir_path, "info.json")

            if os.path.isdir(subdir_path) and os.path.isfile(info_path):
                try:
                    with open(info_path, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                        server_id = info.get("id")
                        port = info.get("port")
                        if server_id and port:
                            result.append({"id": server_id, "port": port})
                except Exception as e:
                    logger.error(f"读取 {info_path} 失败: {e}")
        return result

    def start_servers(self):
        try:
            # 验证密钥存储路径
            storage_path = self.storage_path.get()
            if not storage_path:
                logger.error("密钥存储路径不能为空！")
                return
            
            # 验证系统中心地址
            system_center_url = self.system_center_url.get()
            if not system_center_url:
                logger.error("系统中心地址不能为空！")
                return

            # 获取配置
            base_port = int(self.base_port.get())
            server_count = int(self.server_count.get())
            
            # 清空现有服务器
            self.stop_servers()
            
            # 检查是否刚刚停止服务
            if hasattr(self, 'last_stop_time'):
                elapsed = time.time() - self.last_stop_time
                if elapsed < 2:  # 如果距离上次停止不到2秒
                    messagebox.showwarning("提示", "请稍等片刻再启动服务，以确保资源正确释放。")
                    return

            # 添加分隔符
            separator = "=" * 50
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.log_text.tag_config("separator", foreground="purple")
            self.log_text.insert(tk.END, f"\n{separator}\n", "separator")
            self.log_text.insert(tk.END, f"系统启动时间: {current_time}\n", "separator")
            self.log_text.insert(tk.END, f"{separator}\n\n", "separator")
            self.log_text.see(tk.END)
            
            # 创建并启动服务器
            ids = CloudServerGUI.list_subdirectories(storage_path)
            for i in range(server_count):
                config = CloudServerConfig(
                    storage_path=storage_path,
                    port=base_port + i,
                    system_center_url=self.system_center_url.get(),
                    mongo_uri=self.mongo_uri.get(),
                    db_name=self.db_name.get(),
                    enc_shares_collection=self.enc_shares_collection.get(),
                    id=ids[i]['id'] if ids else ''
                )
                
                server = CloudServer(config)
                self.servers.append(server)
                
                # 创建并启动服务器线程
                thread = threading.Thread(target=self.run_server, args=(server,), name=f"ServerThread-{i}")
                thread.daemon = True
                self.server_threads.append(thread)
                thread.start()
                
            logger.info(f"云服务器集群启动准备 (端口:{base_port}-{base_port + server_count - 1})")
            
            # 更新按钮状态
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
        except Exception as e:
            logger.error(f"启动服务器失败: {str(e)}")
            
    def run_server(self, server):
        try:
            server.initialize()
            server.run_server()
        except Exception as e:
            logger.error(f"服务器运行错误: {str(e)}")
            
    def stop_servers(self):
        if self.servers:
            logger.info("服务器集群已停止")

            for server in self.servers:
                try:
                    server.stop_server()
                except:
                    pass
                    
            self.servers.clear()
            self.server_threads.clear()

            # 添加停止分隔符
            separator = "-" * 50
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.log_text.tag_config("separator", foreground="purple")
            self.log_text.insert(tk.END, f"\n{separator}\n", "separator")
            self.log_text.insert(tk.END, f"系统停止时间: {current_time}\n", "separator")
            self.log_text.insert(tk.END, f"{separator}\n\n", "separator")
            self.log_text.see(tk.END)
            self.last_stop_time = time.time()

        # 更新按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = CloudServerGUI(root)
    
    # 启动日志更新
    app.update_log_display()
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    main() 