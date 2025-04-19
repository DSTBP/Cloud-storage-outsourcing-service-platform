# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : utils/network.py
# @Description : python打包程序
import time
from loguru import logger
from User.core.user import User
from User.model.config import UserConfig

# --------------- 初始化服务 ---------------
sc_url = "http://localhost:6666"


# --------------- 用户注册 ---------------
# if __name__ == '__main__':
#     alice = User(UserConfig(sc_url))
#     username =
#     password =
#     status =
#     alice.initialize(username, password, status)
#     # alice.initialize("alice2114", '123123', 'login')
#
#     # # --------------- 文件上传 ---------------
#     # file_content = b"Secret Data: 2025 Conference Plan"
#     # logger.success("文件上传成功，等待服务器处理...")
#     # alice.upload_file(r"D:\Data\PythonProjects\GraduationDesign\Beta0.7\User\files\source\2025级-硕士研究生信息表-王思羽.xlsx")
#     # time.sleep(3)  # 等待TC处理
#
#     # # --------------- 文件下载 ---------------
#     # files_infos = alice.get_files_info()
#     # logger.debug("files_infos: {}".format(files_infos))
#     # logger.info("尝试下载文件...")
#     # alice.download_file(files_infos[0]._id, r"D:\Data\PythonProjects\GraduationDesign\Beta0.7\User\files\recover")