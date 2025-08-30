# -*- coding: utf-8 -*-
"""
测试LARC文件打包和解包功能
"""

import os
from larc import LarcFile

# 初始化LARC文件对象
larc = LarcFile()

# 创建新的LARC文件
try:
    # 打包文件
    larc.open_file("c:\\Users\\micha\\Documents\\Code\\Light Archive\\test_folder\\test_file.larc")
    
    # 获取要打包的文件列表
    packed_files = [
        "c:\\Users\\micha\\Documents\\Code\\Light Archive\\test_folder\\packed_files\\Vim Cheat Sheet.html",
        "c:\\Users\\micha\\Documents\\Code\\Light Archive\\test_folder\\packed_files\\style.css",
        "c:\\Users\\micha\\Documents\\Code\\Light Archive\\test_folder\\packed_files\\warp-logo.svg"
    ]
    
    # 打包文件
    larc.pack_files(packed_files)
    print("文件打包成功！")
    
    # 解包文件
    larc.unpack_files("c:\\Users\\micha\\Documents\\Code\\Light Archive\\test_folder\\unpacked_files")
    print("文件解包成功！")
    
    # 关闭文件
    larc.close_file()
    
except Exception as e:
    print(f"发生错误: {e}")
    if larc.larc_file is not None:
        larc.close_file()
