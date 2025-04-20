# -*- coding: utf-8 -*-
# @Time    : 2025/04/19 12:33
# @Author  : DSTBP
# @File    : CloudServer/server_main.py
# @Description : 云服务器集群主函数
import os
import json
from loguru import logger
from business.core import CloudServer
from business.config import CloudServerConfig


def list_subdirectories(base_dir = r"D:\Data\PythonProjects\GraduationDesign\Gamma0.4\CloudServer\business\keys"):
    result = []
    # 遍历 base_dir 下的所有子目录
    for subdir in os.listdir(base_dir):
        subdir_path = os.path.join(base_dir, subdir)
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
                print(f"读取 {info_path} 失败: {e}")
    return result


if __name__ == "__main__":
    ids = list_subdirectories()
    print(ids)
    # 启动云服务器集群（7777端口）
    servers = [
        CloudServer(
            CloudServerConfig(
                system_center_url="http://localhost:8085",
                host='127.0.0.1',
                port= ids[i]['port'] if ids else 7777 + i,
                id= ids[i]['id'] if ids else ''
            )
        ) for i in range(5)
    ]

    # 初始化所有云服务器
    for server in servers:
        server.initialize()
        server.run_server()
    logger.success(f"云服务器集群已启动 (端口:7777-{7777 + len(servers) - 1})")

    # 保持主线程运行
    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("系统关闭")