# import os
# import shutil


# def clear_keys_subdirs(root_dir: str):
#     """
#     清空指定目录下所有名为 'keys' 的子目录中的所有内容。

#     :param root_dir: 根目录路径
#     """
#     for dirpath, dirnames, filenames in os.walk(root_dir):
#         for dirname in dirnames:
#             if dirname == "keys":
#                 keys_dir = os.path.join(dirpath, dirname)
#                 print(f"清空目录: {keys_dir}")
#                 for item in os.listdir(keys_dir):
#                     item_path = os.path.join(keys_dir, item)
#                     try:
#                         if os.path.isfile(item_path) or os.path.islink(item_path):
#                             os.unlink(item_path)  # 删除文件或符号链接
#                         elif os.path.isdir(item_path):
#                             shutil.rmtree(item_path)  # 删除子目录
#                     except Exception as e:
#                         print(f"删除 {item_path} 失败: {e}")

# # 示例用法
# clear_keys_subdirs(r"D:\Data\PythonProjects\GraduationDesign\Beta0.8")


import os
import shutil

def delete_dev_dirs(root_dir):
    # 要删除的目录名称列表
    target_dirs = {'.vscode', '.idea', '__pycache__'}

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # 过滤出目标目录
        for dirname in list(dirnames):
            if dirname in target_dirs:
                full_path = os.path.join(dirpath, dirname)
                print(f"删除目录: {full_path}")
                shutil.rmtree(full_path)
                # 从遍历中移除，避免访问已删除目录
                dirnames.remove(dirname)

# 用法：传入你要清理的路径
delete_dev_dirs(r'D:\Data\PythonProjects\GraduationDesign\Gamma0.7')