import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
from loguru import logger
from business.core import SystemCenter
from business.config import SystemCenterConfig
import json
import os
import sys
import time
import queue

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        # PyInstaller创建临时文件夹,将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SystemCenterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("系统中心控制面板")
        self.root.geometry("1000x800")
        self.root.iconbitmap(get_resource_path("favicon.ico"))

        # 系统参数
        self.system_config = {
            'p': 6277101735386680763835789423207666416083908700390324961279,
            'a': -3,
            'b': 2455155546008943817740293915197451784769108058161191238065,
            'Gx': 602046282375688656758213480587526111916698976636884684818,
            'Gy': 174050332293622031404857552280219410364023488927386650641,
            'N': 6277101735386680763835789423176059013767194773182842284081,
        }

        # 默认配置
        self.default_config = SystemCenterConfig()
        
        self.system_center = None
        self.server_thread = None
        self.is_running = False
        
        # 创建日志队列
        self.log_queue = queue.Queue()
        
        self.create_widgets()
        self.setup_logger()
        
    def create_widgets(self):
        # 创建输入框架
        input_frame = ttk.LabelFrame(self.root, text="系统配置", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 配置列权重，使输入框可以自动拉伸
        input_frame.columnconfigure(1, weight=1)
        
        # 创建输入字段
        # 端口号
        ttk.Label(input_frame, text="端口号:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.port_entry = ttk.Entry(input_frame)
        self.port_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.port_entry.insert(0, str(self.default_config.port))
        
        # 系统参数
        ttk.Label(input_frame, text="系统参数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.sys_param_entry = ttk.Entry(input_frame)
        self.sys_param_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.sys_param_entry.insert(0, json.dumps(self.system_config))
        
        # 云服务器总数
        ttk.Label(input_frame, text="云服务器总数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.n_entry = ttk.Entry(input_frame)
        self.n_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.n_entry.insert(0, "5")
        
        # 门限值
        ttk.Label(input_frame, text="门限值:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.t_entry = ttk.Entry(input_frame)
        self.t_entry.grid(row=3, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.t_entry.insert(0, "3")
        
        # MongoDB配置
        mongo_frame = ttk.LabelFrame(self.root, text="MongoDB配置", padding=10)
        mongo_frame.pack(fill=tk.X, padx=5, pady=5)
        mongo_frame.columnconfigure(1, weight=1)
        
        # MongoDB URI
        ttk.Label(mongo_frame, text="MongoDB URI:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.mongo_uri_entry = ttk.Entry(mongo_frame)
        self.mongo_uri_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.mongo_uri_entry.insert(0, self.default_config.mongo_uri)
        
        # 数据库名称
        ttk.Label(mongo_frame, text="数据库名称:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.db_name_entry = ttk.Entry(mongo_frame)
        self.db_name_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.db_name_entry.insert(0, self.default_config.db_name)
        
        # 文件信息表
        ttk.Label(mongo_frame, text="文件信息表:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.files_collection_entry = ttk.Entry(mongo_frame)
        self.files_collection_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.files_collection_entry.insert(0, self.default_config.files_collection)
        
        # 服务器信息表
        ttk.Label(mongo_frame, text="服务器信息表:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.servers_collection_entry = ttk.Entry(mongo_frame)
        self.servers_collection_entry.grid(row=3, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.servers_collection_entry.insert(0, self.default_config.servers_collection)
        
        # 用户信息表
        ttk.Label(mongo_frame, text="用户信息表:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.users_collection_entry = ttk.Entry(mongo_frame)
        self.users_collection_entry.grid(row=4, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.users_collection_entry.insert(0, self.default_config.users_collection)
        
        # 系统参数表
        ttk.Label(mongo_frame, text="系统参数表:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.sys_params_collection_entry = ttk.Entry(mongo_frame)
        self.sys_params_collection_entry.grid(row=5, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.sys_params_collection_entry.insert(0, self.default_config.sys_params_collection)
        
        # 存储路径配置
        storage_frame = ttk.LabelFrame(self.root, text="存储路径配置", padding=10)
        storage_frame.pack(fill=tk.X, padx=5, pady=5)
        storage_frame.columnconfigure(1, weight=1)
        
        # 存储路径
        ttk.Label(storage_frame, text="存储路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.storage_path_entry = ttk.Entry(storage_frame)
        self.storage_path_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        ttk.Button(storage_frame, text="浏览", command=self.browse_storage_path).grid(row=0, column=2, padx=5)
        
        # 日志配置
        log_frame = ttk.LabelFrame(self.root, text="日志配置", padding=10)
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        log_frame.columnconfigure(1, weight=1)
        
        # 日志路径
        ttk.Label(log_frame, text="日志路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.log_path_entry = ttk.Entry(log_frame)
        self.log_path_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(5,5))
        self.log_path_entry.insert(0, os.path.join(os.getcwd(), "logs"))
        ttk.Button(log_frame, text="浏览", command=self.browse_log_path).grid(row=0, column=2, padx=5)
        
        # 按钮框架
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_button = ttk.Button(button_frame, text="启动系统中心服务", command=self.start_service)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="停止系统中心服务", command=self.stop_service, state=tk.DISABLED)
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
        
    def setup_logger(self):
        # 配置日志处理器
        logger.remove()  # 移除默认处理器
        
        # 添加GUI日志处理器
        logger.add(self.log_queue.put, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
        
        # 确保日志目录存在
        log_path = self.log_path_entry.get()
        if not os.path.exists(log_path):
            os.makedirs(log_path)
            
        # 添加文件处理器
        logger.add(os.path.join(log_path, "system.log"), rotation="1 day", retention="7 days")
        
        # 启动日志更新定时器
        self.root.after(200, self.update_log_display)
        
    def update_log_display(self):
        while not self.log_queue.empty():
            log_entry = self.log_queue.get()
            level = log_entry.split(" | ")[1]
            self.log_text.insert(tk.END, log_entry + "\n", level)
            self.log_text.see(tk.END)
        self.root.after(200, self.update_log_display)
        
    def browse_log_path(self):
        path = filedialog.askdirectory()
        if path:
            self.log_path_entry.delete(0, tk.END)
            self.log_path_entry.insert(0, path)
            self.setup_logger()
            
    def browse_storage_path(self):
        path = filedialog.askdirectory()
        if path:
            self.storage_path_entry.delete(0, tk.END)
            self.storage_path_entry.insert(0, path)
            
    def start_service(self):
        try:
            # 验证存储路径
            storage_path = self.storage_path_entry.get()
            if not storage_path:
                logger.error("存储路径不能为空！")
                return
                
            # 获取配置
            port = int(self.port_entry.get())
            n = int(self.n_entry.get())
            t = int(self.t_entry.get())
            
            # 添加分隔符
            separator = "=" * 50
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.log_text.tag_config("separator", foreground="purple")
            self.log_text.insert(tk.END, f"\n{separator}\n", "separator")
            self.log_text.insert(tk.END, f"系统启动时间: {current_time}\n", "separator")
            self.log_text.insert(tk.END, f"{separator}\n\n", "separator")
            self.log_text.see(tk.END)
            
            # 检查是否刚刚停止服务
            if hasattr(self, 'last_stop_time'):
                elapsed = time.time() - self.last_stop_time
                if elapsed < 2:  # 如果距离上次停止不到2秒
                    messagebox.showwarning("提示", "请稍等片刻再启动服务，以确保资源正确释放。")
                    return
            
            # 创建并启动系统中心
            config = SystemCenterConfig(
                port=port,
                mongo_uri=self.mongo_uri_entry.get(),
                db_name=self.db_name_entry.get(),
                files_collection=self.files_collection_entry.get(),
                servers_collection=self.servers_collection_entry.get(),
                users_collection=self.users_collection_entry.get(),
                sys_params_collection=self.sys_params_collection_entry.get(),
                storage_path=storage_path
            )
            
            self.system_center = SystemCenter(config)
            
            # 创建并启动服务器线程
            self.server_thread = threading.Thread(target=self.run_service, name="SystemCenterThread")
            self.server_thread.daemon = True
            self.server_thread.start()
            
            logger.info(f"系统中心服务启动中... (端口:{port})")
            
            # 更新按钮状态
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
        except Exception as e:
            logger.error(f"启动系统中心服务失败: {str(e)}")
            
    def run_service(self):
        try:
            n = int(self.n_entry.get())
            t = int(self.t_entry.get())
            self.system_center.initialize({**self.system_config, 'n': n, 't': t})
            self.system_center.run_server()
        except Exception as e:
            logger.error(f"系统中心服务运行错误: {str(e)}")
            
    def stop_service(self):
        try:
            if self.system_center:
                self.system_center.stop_server()
                self.system_center = None
                
            if self.server_thread:
                self.server_thread.join(timeout=2)
                self.server_thread = None
                
            # 添加停止分隔符
            separator = "-" * 50
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.log_text.tag_config("separator", foreground="purple")
            self.log_text.insert(tk.END, f"\n{separator}\n", "separator")
            self.log_text.insert(tk.END, f"系统停止时间: {current_time}\n", "separator")
            self.log_text.insert(tk.END, f"{separator}\n\n", "separator")
            self.log_text.see(tk.END)
            
            # 更新按钮状态
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            # 记录停止时间
            self.last_stop_time = time.time()
            
        except Exception as e:
            logger.error(f"停止系统中心服务失败: {str(e)}")
            
if __name__ == "__main__":
    root = tk.Tk()
    app = SystemCenterGUI(root)
    root.mainloop()