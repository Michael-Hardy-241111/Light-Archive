# -*- coding: utf-8 -*-
"""
用于处理 light archive 文件(.larc)的 Python 免费公开工具 API
@author: Michael-Hardy-241111
@version: 0.2.0
@date: 2025-08-20
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
本工具在代码托管平台开源, 任何人都可以提出问题和建议, 链接如下:
> Github (https://github.com/Michael-Hardy-241111/Light-Archive)
"""

# 导入模块
import os
import warnings
import sys

if sys.version_info < (3, 6):
    raise RuntimeError("需要Python 3.6或更高版本")

# 定义常量
LARC_FILE_HEADER:bytes = b'LARC'		# 文件头
LARC_DEFAULT_FOOTER:bytes = b'\x03'	    # 文件结束标识
LARC_DEFAULT_VERSION:bytearray = bytearray([0, 2, 0])  # 默认版本号 [修订版本号, 次版本号, 主版本号]

class FileStruct:
    """
    管理LARC文件内部文件的结构信息
    """
    def __init__(self):
        """
        初始化文件结构对象
        
        属性:
            index: 序号
            offset: 文件偏移
            length: 文件长度
            name: 文件名
        """
        self.index:int = 0											# 序号
        self.offset:int = 0											# 文件偏移
        self.length:int = 0											# 文件长度
        self.name:str = ''											# 文件名

    def modify(self, data:list[int, int, int, str]) -> None:
        """
        通过列表设置文件结构参数
        
        参数:
            data (list): [序号, 偏移量, 长度, 文件名]格式的列表
        """
        self.index = data[0]
        self.offset = data[1]
        self.length = data[2]
        self.name = data[3]
        return
    
    def modify_bytearray(self, data:bytearray) -> None:
        """
        从字节数组解析文件结构参数
        
        参数:
            data (bytearray): 20字节索引信息 + 变长文件名组成的字节数组
        """
        self.index = int.from_bytes(data[0:4], byteorder='little')
        self.offset = int.from_bytes(data[4:12], byteorder='little')
        self.length = int.from_bytes(data[12:20], byteorder='little')
        self.name = data[20:].decode('utf-8')
        return

    def modify_index(self, index:int) -> None:
        """
        修改序号
        
        参数:
            index (int): 新的序号值
        """
        self.index = index
        return

    def modify_offset(self, offset:int) -> None:
        """
        修改文件偏移
        
        参数:
            offset (int): 新的文件偏移值
        """
        self.offset = offset
        return

    def modify_length(self, length:int) -> None:
        """
        修改文件长度
        
        参数:
            length (int): 新的文件长度值
        """
        self.length = length
        return

    def modify_name(self, name:str) -> None:
        """
        修改文件名
        
        参数:
            name (str): 新的文件名
        """
        self.name = name
        return

    def get(self) -> list[int, int, int, str]:
        """
        获取内部文件结构体
        
        返回:
            list: [序号, 偏移量, 长度, 文件名]格式的列表
        """
        return [self.index, self.offset, self.length, self.name]
    
    def get_bytearray(self) -> bytearray:
        """
        将文件结构转换为字节数组
        
        返回:
            bytearray: 包含4字节序号 + 8字节偏移量 + 8字节长度 + UTF-8编码文件名的字节数组
        """
        byte_data = bytearray()
        byte_data.extend(self.index.to_bytes(4, byteorder='little'))
        byte_data.extend(self.offset.to_bytes(8, byteorder='little'))
        byte_data.extend(self.length.to_bytes(8, byteorder='little'))
        byte_data.extend(self.name.encode('utf-8'))
        byte_data.append(0)  # 添加null终止符
        return byte_data

    def get_index(self) -> int:
        """
        获取序号
        
        返回:
            int: 文件结构的序号
        """
        return self.index
    
    def get_offset(self) -> int:
        """
        获取文件偏移
        
        返回:
            int: 文件的偏移量
        """
        return self.offset
    
    def get_length(self) -> int:
        """
        获取文件长度
        
        返回:
            int: 文件的长度
        """
        return self.length
    
    def get_name(self) -> str:
        """
        获取文件名
        
        返回:
            str: 文件的名称
        """
        return self.name

class LarcFile:
    """
    LARC文件操作, 用于创建、打开和管理LARC格式的压缩文件
    """
    def __init__(self):
        """
        初始化LarcFile对象
        
        属性:
            file_path: 文件路径
            file_header: 文件头
            version: 版本号
            encryption_flag: 加密/压缩标志
            key_length: 密钥长度
            list_header_offset: 列表头偏移
            list_length: 列表长度
            file_count: 内部文件数量
            file_total_length: 内部文件的总长度
            larc_file: 文件对象
            file_list: 文件结构列表
        """
        self.file_path:str = ''										# 文件路径
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
        关闭LARC文件
        
        返回:
            None
        """
        if self.larc_file is not None:
            self.larc_file.close()
            self.larc_file = None
        return
    
    def create_file(self, file_path:str) -> None:
        """
        创建一个新的LARC文件
        
        参数:
            file_path (str): 要创建的LARC文件路径
        
        返回:
            None
        """
        self.file_path = file_path
        self.larc_file = open(file_path, 'wb+')
        self.version = LARC_DEFAULT_VERSION						    # 版本号
        self.encryption_flag = bytearray([0])						# 加密/压缩标志
        self.key_length = bytearray([0, 0, 0, 0])					# 密钥长度
        self.list_header_offset = bytearray([0, 0, 0, 0])		    # 列表头偏移
        self.list_length = bytearray([0, 0, 0, 0])				    # 列表长度
        self.file_count = bytearray([0, 0, 0, 0])				    # 内部文件数量
        self.file_total_length = bytearray([0, 0, 0, 0, 0, 0, 0, 0])# 内部文件的总长度
        self.larc_file.write(LARC_FILE_HEADER)
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
        打开一个已存在的LARC文件
        
        参数:
            file_path (str): 要打开的LARC文件路径
        
        返回:
            None
        
        raises:
            Exception: 如果文件头不正确
        """
        self.file_path = file_path
        self.larc_file = open(file_path, 'rb+')
        self.file_header = self.larc_file.read(4)
        if self.file_header != LARC_FILE_HEADER:
            raise Exception('文件头错误')
        self.version = bytearray(self.larc_file.read(3))
        # 检查版本
        tool_version = LARC_DEFAULT_VERSION  # 当前工具版本 [修订版本号, 次版本号, 主版本号]
        file_major = self.version[2]
        tool_major = tool_version[2]
        file_minor = self.version[1]
        tool_minor = tool_version[1]
        
        if file_major != tool_major:
            raise Exception(f'主版本号不匹配，文件主版本号为 {file_major}，工具主版本号为 {tool_major}，无法继续处理')
        if file_minor != tool_minor:
            warnings.warn(f'次版本号不匹配，文件次版本号为 {file_minor}，工具次版本号为 {tool_minor}，可能存在兼容性问题，继续执行')
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

    def pack_files(self, file_list:list[str]) -> None:
        """
        将指定的文件列表打包到LARC文件中
        
        参数:
            file_list (list[str]): 要打包的文件路径列表
        
        返回:
            None
        """
        # 检查文件是否已打开
        if self.larc_file is None:
            raise Exception('文件未打开')
        
        # 清空文件列表
        self.file_list = []
        
        # 计算文件列表头偏移 - 固定为32字节（文件头部分的长度）
        list_header_offset = 32
        self.list_header_offset = list_header_offset.to_bytes(4, byteorder='little')
        
        # 计算文件数量
        file_count = len(file_list)
        self.file_count = file_count.to_bytes(4, byteorder='little')
        
        # 计算每个文件的信息并添加到文件列表
        total_length = 0  # 内部文件的总长度
        list_length = 0  # 列表部分的总长度
        
        # 第一遍遍历：收集文件信息，计算列表长度和总长度
        for i in range(file_count):
            file_path = file_list[i]
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise Exception(f'文件不存在: {file_path}')
            
            # 创建文件结构对象
            file_struct = FileStruct()
            file_struct.modify_index(i)
            file_struct.modify_name(os.path.basename(file_path))
            
            # 获取文件长度
            file_size = os.path.getsize(file_path)
            file_struct.modify_length(file_size)
            
            # 添加到文件列表
            self.file_list.append(file_struct)
            
            # 累计总长度
            total_length += file_size
            
            # 计算列表项的长度（20字节固定部分 + 文件名长度 + 1字节null终止符）
            list_item_length = 20 + len(file_struct.get_name()) + 1
            list_length += list_item_length
        
        # 更新总长度信息
        self.file_total_length = total_length.to_bytes(8, byteorder='little')
        self.list_length = list_length.to_bytes(4, byteorder='little')
        
        # 第二遍遍历：计算文件偏移
        current_offset = list_header_offset + list_length  # 文件数据开始的偏移量
        for file_struct in self.file_list:
            file_struct.modify_offset(current_offset)
            current_offset += file_struct.get_length()
        
        # 重新写入文件头信息
        self.larc_file.seek(0)
        self.larc_file.write(self.file_header)
        self.larc_file.write(self.version)
        self.larc_file.write(self.encryption_flag)
        self.larc_file.write(self.key_length)
        self.larc_file.write(self.list_header_offset)
        self.larc_file.write(self.list_length)
        self.larc_file.write(self.file_count)
        self.larc_file.write(self.file_total_length)
        
        # 写入文件列表
        for file_struct in self.file_list:
            self.larc_file.write(file_struct.get_bytearray())
        
        # 写入文件数据
        for i in range(file_count):
            file_path = file_list[i]
            file_struct = self.file_list[i]
            
            # 移动到文件数据的偏移位置
            self.larc_file.seek(file_struct.get_offset())
            
            # 读取并写入文件内容
            with open(file_path, 'rb') as f:
                self.larc_file.write(f.read())
        
        # 写入文件结束标志
        self.larc_file.seek(0, 2)  # 移动到文件末尾
        self.larc_file.write(LARC_DEFAULT_FOOTER)
        
        return
    
    def unpack_files(self, output_dir:str) -> None:
        """
        将LARC文件解包到指定目录
        
        参数:
            output_dir (str): 解包输出目录
        
        返回:
            None
        """
        # 检查文件是否已打开
        if self.larc_file is None:
            raise Exception('文件未打开')
        
        # 检查输出目录是否存在，不存在则创建
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 遍历文件列表
        for file_struct in self.file_list:
            # 获取文件名和输出路径
            file_name = file_struct.get_name()
            output_path = os.path.join(output_dir, file_name)
            
            # 读取文件数据
            self.larc_file.seek(file_struct.get_offset())
            file_data = self.larc_file.read(file_struct.get_length())
            
            # 将文件数据写入输出文件
            with open(output_path, 'wb') as f:
                f.write(file_data)
        
        return
