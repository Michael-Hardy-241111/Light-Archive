# -*- coding: utf-8 -*-
"""
用于处理 light archive 文件(.larc)的 Python 免费公开工具 API
@author: Michael-Hardy-241111
@version: 0.1.0
@date: 2025-08-10
@license: MIT

技术说明
文件内的数据顺序为:
1. 文件头(4Bytes);
2. 版本号(3Bytes), [修订版本号, 次版本号, 主版本号];
3. 加密/压缩标志(1Byte);
4. 密钥长度(4Bytes), 对应密钥长度在 0 ~ 4,294,967,295(2^32-1) 之间;
5. 列表头偏移(4Bytes);
6. 列表长度(4Bytes);
7. 内部文件数量(4Bytes);
8. 内部文件的总长度(8Bytes);
# 上面共计 32 Bytes, 固定长度部分
9. 列表, 标记每个内部文件的存储信息
    9.1. 序号(4Bytes);
    9.2. 文件偏移(8Bytes);
    9.3. 文件长度(8Bytes);
    9.4. 文件名(变长), 到第一个'\0'结束;
10. 内部文件数据, 每个内部文件的偏移和位置已在列表定义, 修改此部分时需要同时修改列表&'7. 内部文件数量(4Bytes)'&'8. 内部文件的总长度(8Bytes)';
11. 额外指定的防伪数据(变长), 以'\x03'(ETX)结尾, 也表示文件结束

使用说明
任何人都可以免费使用本工具, 也可以修改代码, 使工具符合自己的需求.
本工具不限制任何人下载, 传播时禁止收费, 请保证 Light Archive 社区的纯净.
如果要在任何平台(包括线上和线下)公开本工具, 请声明原作者, 保留原作者的信息, 维护原作者的权益.
本工具目前在 Github 上开源, 任何人都可以提出问题和建议, 链接如下:
> https://github.com/Michael-Hardy-241111/Light-Archive
"""

# 导入模块
import os

# 定义常量
LARC_FILE_HEADER:bytes = b'LARC'		# 文件头
LARC_DEFAULT_FOOTER:bytes = b'\x03'	    # 文件结束标识

class FileStruct:
    """
    内部文件结构体
    """
    def __init__(self):
        """
        初始化内部文件结构体
        """
        self.index:int = 0											# 序号
        self.offset:int = 0											# 文件偏移
        self.length:int = 0											# 文件长度
        self.name:str = ''											# 文件名

    def modify(self, data:list[int, int, int, str]) -> None:
        """
        修改内部文件结构体
        """
        self.index = data[0]
        self.offset = data[1]
        self.length = data[2]
        self.name = data[3]
        return
    
    def modify_bytearray(self, data:bytearray) -> None:
        """
        修改内部文件结构体
        """
        self.index = int.from_bytes(data[0:4], byteorder='little')
        self.offset = int.from_bytes(data[4:12], byteorder='little')
        self.length = int.from_bytes(data[12:20], byteorder='little')
        self.name = data[20:].decode('utf-8')
        return
    
    def get(self) -> list[int, int, int, str]:
        """
        获取内部文件结构体
        """
        return [self.index, self.offset, self.length, self.name]
    
    def get_bytearray(self) -> bytearray:
        byte_data = bytearray()
        byte_data.extend(self.index.to_bytes(4, byteorder='little'))
        byte_data.extend(self.offset.to_bytes(8, byteorder='little'))
        byte_data.extend(self.length.to_bytes(8, byteorder='little'))
        byte_data.extend(self.name.encode('utf-8'))
        byte_data.append(0)  # 添加null终止符
        return byte_data

class LarcFile:
    """
    Light Archive 文件类
    """
    def __init__(self):
        """
        初始化 Light Archive 文件类
        没有参数的构造函数, 所有参数都需要在后续的函数中设置.
        """
        self.file_path:str = ''										# 文件路径
        self.file_header:bytes = LARC_FILE_HEADER					# 文件头
        self.version:bytearray = bytearray(3)						# 版本号
        self.encryption_flag:bytearray = bytearray(1)				# 加密/压缩标志
        self.key_length:bytearray = bytearray(4)					# 密钥长度
        self.list_header_offset:bytearray = bytearray(4)			# 列表头偏移
        self.list_length:bytearray = bytearray(4)					# 列表长度
        self.file_count:bytearray = bytearray(4)					# 内部文件数量
        self.file_total_length:bytearray = bytearray(8)				# 内部文件的总长度
        self.larc_file = None
        self.file_list:list[FileStruct] = []

    def close_file(self) -> None:
        """
        关闭 Light Archive 文件
        """
        if self.larc_file is not None:
            self.larc_file.close()
            self.larc_file = None
        return
    
    def create_file(self, file_path:str) -> None:
        """
        创建 Light Archive 文件
        """
        self.file_path = file_path
        self.larc_file = open(file_path, 'wb+')
        self.version = bytearray([0, 1, 0])							# 版本号
        self.encryption_flag = bytearray([0])						# 加密/压缩标志
        self.key_length = bytearray([0, 0, 0, 0])					# 密钥长度
        self.list_header_offset = bytearray([0, 0, 0, 0])			# 列表头偏移
        self.list_length = bytearray([0, 0, 0, 0])					# 列表长度
        self.file_count = bytearray([0, 0, 0, 0])					# 内部文件数量
        self.file_total_length = bytearray([0, 0, 0, 0, 0, 0, 0, 0])# 内部文件的总长度
        self.larc_file.write(self.file_header)
        self.larc_file.write(self.version)
        self.larc_file.write(self.encryption_flag)
        self.larc_file.write(self.key_length)
        self.larc_file.write(self.list_header_offset)
        self.larc_file.write(self.list_length)
        self.larc_file.write(self.file_count)
        self.larc_file.write(self.file_total_length)
        self.larc_file.write(LARC_DEFAULT_FOOTER)
        return
    
    def open_file(self, file_path:str) -> None:
        """
        打开 Light Archive 文件
        """
        self.file_path = file_path
        self.larc_file = open(file_path, 'rb+')
        self.file_header = self.larc_file.read(4)
        if self.file_header != LARC_FILE_HEADER:
            raise Exception('文件头错误')
        self.version = bytearray(self.larc_file.read(3))
        self.encryption_flag = bytearray(self.larc_file.read(1))
        self.key_length = bytearray(self.larc_file.read(4))
        self.list_header_offset = bytearray(self.larc_file.read(4))
        self.list_length = bytearray(self.larc_file.read(4))
        self.file_count = bytearray(self.larc_file.read(4))
        self.file_total_length = bytearray(self.larc_file.read(8))
        self.file_list = []
        for i in range(int.from_bytes(self.file_count, byteorder='little')):
            list = bytearray(self.larc_file.read(20))
            while True:
                char = self.larc_file.read(1)
                if char == b'\x00':
                    break
                list.extend(char)  # Fixed: use extend() instead of append()
            self.file_list.append(FileStruct())
            self.file_list[i].modify_bytearray(list)
        return
