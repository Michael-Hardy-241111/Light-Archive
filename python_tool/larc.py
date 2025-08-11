# -*- coding: utf-8 -*-
# 这是 .larc 文件格式的 Python tool API

# 工具默认版本，格式为 [修订版本号, 次版本号, 主版本号]：0.1.0
tool_default_version:list[int] = [0, 1, 0]
# .larc 文件格式的文件头
larc_file_header:bytearray = bytearray([0x01, 0x4c, 0x41, 0x52, 0x43, 0x02])

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

	def __init__():
		"""
		无参数初始化对象
		"""
		pass

	def __init__(self, file_path:str):
		"""
		用文件路径初始化对象
		:param file_path: 文件路径
		该函数会调用 :func:`open_file` 函数打开文件
		"""
		self.open_file(file_path)
	
	def open_file(self, file_path:str) -> bool:
		"""
		打开一个文件
		:param file_path: 文件路径
		:return: 是否异常
		该函数会调用 :func:`read_files_array` 函数读取文件列表数组
		"""
		self.file_path = file_path
		try:
			self.larc_file = open(self.file_path, "rb+")
		except:
			print("打开文件失败")
			return True
		if self.larc_file.read(6) != larc_file_header:
			print("文件头错误")
			return True
		self.file_version = self.larc_file.read(3)
		if self.file_version[2] != tool_default_version[2]:
			print("主版本号不一致，无法打开")
			return True
		if self.file_version[1] != tool_default_version[1]:
			print("次版本号不一致，建议更换对应版本的工具")
		self.array_head = int.from_bytes(self.larc_file.read(4), byteorder="little")
		self.array_long = int.from_bytes(self.larc_file.read(4), byteorder="little")
		self.files_count = int.from_bytes(self.larc_file.read(4), byteorder="little")
		self.files_long = int.from_bytes(self.larc_file.read(4), byteorder="little")
		return self.read_files_array()

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
		try:
			del self.larc_file
			del self.file_path
			del self.file_version
			del self.array_head
			del self.array_long
			del self.files_count
			del self.files_long
			del self.files_array
		except:
			print("删除文件对象失败")
			boolean = True
		return boolean