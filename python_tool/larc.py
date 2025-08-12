# -*- coding: utf-8 -*-
# 这是 .larc 文件格式的 Python tool API

import os
import tempfile

# 工具默认版本，格式为 [修订版本号, 次版本号, 主版本号]：0.1.0
tool_default_version:list[int] = [0, 1, 0]
# .larc 文件格式的文件头 [SOH, 'L', 'A', 'R', 'C', STX]
larc_file_header:bytes = b"\x01\x4c\x41\x52\x43\x02"
# 文件尾部防伪数据的明文
file_footer:bytes = b"Extension of Light-Archive File is .larc, author is Michael-Hardy-241111."

class FileInfo:
	"""
	文件信息类
	"""
	file_num:int = 0
	file_head:int = 0
	file_long:int = 0
	file_name:str = ""

class LarcTool:
	"""
	这是一个 .larc 文件格式的 Python tool API
	"""
	larc_file:object = None
	file_path:str = ""
	file_version:list[int] = [0, 0, 0]
	array_head:int = 0
	array_long:int = 0
	files_count:int = 0
	files_long:int = 0
	files_array:list[FileInfo] = []

	def __init__(self):
		"""
		无参数初始化对象
		"""
		pass
	
	def open_file(self, file_path:str) -> bool:
		"""
		打开一个文件
		:param file_path: 文件路径
		:return: 是否异常
		该函数会调用 :func:`read_files_array` 函数读取文件列表数组
		"""
		boolean:bool = False
		self.file_path = file_path
		try:
			self.larc_file = open(self.file_path, "rb+")
		except:
			print("打开文件失败")
			boolean = True
		if self.larc_file.read(6) != larc_file_header:
			print("文件头错误")
			boolean = True
		self.file_version = self.larc_file.read(3)
		if self.file_version[2] != tool_default_version[2]:
			print("主版本号不一致，无法打开")
			boolean = True
		if self.file_version[1] != tool_default_version[1]:
			print("次版本号不一致，建议更换对应版本的工具")
		self.array_head = int.from_bytes(self.larc_file.read(4), byteorder="little")
		self.array_long = int.from_bytes(self.larc_file.read(4), byteorder="little")
		self.files_count = int.from_bytes(self.larc_file.read(4), byteorder="little")
		self.files_long = int.from_bytes(self.larc_file.read(4), byteorder="little")
		self.larc_file.seek(self.array_head + self.array_long + self.files_long)
		if self.larc_file.read(len(file_footer) + 2) != b"\x03" + file_footer + b"\x04":
			print("文件尾错误")
			boolean = True
		boolean = self.read_files_array()
		return boolean

	def read_files_array(self) -> bool:
		"""
		读取文件列表的数组
		:return: 是否异常
		"""
		readbytes = 0
		self.larc_file.seek(self.array_head)
		for i in range(self.files_count):
			file_info = FileInfo()
			file_info.file_num = int.from_bytes(self.larc_file.read(4), byteorder="little")
			file_info.file_head = int.from_bytes(self.larc_file.read(4), byteorder="little")
			file_info.file_long = int.from_bytes(self.larc_file.read(4), byteorder="little")
			j:int = 0
			while char := self.larc_file.read(1) != b"\0":
				file_info.file_name += char
				j += 1
				if j > 255:
					print("文件名过长")
					return True
			readbytes += (4 + 4 + 4 + j + 1)
			if readbytes > self.array_long:
				print("文件列表数组长度错误")
				return True
			self.files_array.append(file_info)
		if readbytes != self.array_long:
			print("文件列表数组长度错误")
			return True
		return False

	def create_file(self, file_path:str) -> bool:
		"""
		创建一个文件
		:param file_path: 文件路径
		:return: 是否异常
		"""
		try:
			self.larc_file = open(file_path, "wb+")
		except:
			print("创建文件失败")
			return True
		self.larc_file.write(larc_file_header)
		self.larc_file.write(bytes(tool_default_version))
		# 数组头地址偏移文件头（6）、版本号（3）、数组头地址（4）、数组长度（4）、文件数量（4）、文件列表长度（4）
		self.larc_file.write(int.to_bytes(6+3+4+4+4+4, 4, byteorder="little"))
		self.larc_file.write(int.to_bytes(0, 4, byteorder="little"))
		self.larc_file.write(int.to_bytes(0, 4, byteorder="little"))
		self.larc_file.write(int.to_bytes(0, 4, byteorder="little"))
		self.larc_file.write(b"\x03")
		self.larc_file.write(file_footer)
		self.larc_file.write(b"\x04")
		self.larc_file.close()
		return False
		
	def close_file(self) -> bool:
		"""
		关闭文件
		:return: 是否异常
		"""
		boolean:bool = False
		try:
			self.larc_file.close()
		except:
			print("关闭文件失败")
			boolean = True
		return boolean

def test_larc_tool(file_path: str) -> None:
    print("===== 开始测试 LarcTool =====")
    
    # 1. 创建对象
    larc_creator = LarcTool()
    print("1. 对象创建成功")
    
    # 2. 调用新建文件函数
    create_result = larc_creator.create_file(file_path)
    if create_result:
        print("2. 创建文件失败")
        return
    print("2. 创建文件成功")
    
    # 3. 调用关闭文件函数
    close_result = larc_creator.close_file()
    if close_result:
        print("3. 关闭文件失败")
    else:
        print("3. 关闭文件成功")
    
    # 4. 调用打开文件函数
    larc_opener = LarcTool()
    larc_opener.open_file(file_path)
    print("4. 打开文件成功")
    
    # 5. 调用关闭文件函数
    close_result2 = larc_opener.close_file()
    if close_result2:
        print("5. 再次关闭文件失败")
    else:
        print("5. 再次关闭文件成功")
    
    # 6. 删除对象
    del larc_creator
    del larc_opener
    print("6. 对象删除成功")
    
    print("===== 测试结束 =====")

if __name__ == "__main__":
	test_larc_tool("test_temp.larc")
