# 生成、读取、修改、解包 .larc 文件的工具类

defautl_version = "0.1.0"

class LarcFile:
	file_path:str = ""
	tool_version:str = ""
	larc_file = None

	def __init__(self, file_path:str):
		self.file_path = file_path
		self.tool_version = defautl_version
	
	def open(self) -> None:
		"""
		打开 .larc 文件
		"""
		if self.file_path.endswith(".larc") == False:
			raise ValueError("File path must end with .larc")
		larc_file = open(self.file_path, "rb+")
		if larc_file is None:
			raise IOError("Failed to open file: " + self.file_path)
		self.larc_file = larc_file
		return 
	
	def open_new(self, version:str = defautl_version) -> None:
		"""
		创建一个新的 .larc 文件
		"""
		if self.file_path.endswith(".larc") == False:
			raise ValueError("File path must end with .larc")
		self.larc_file = open(self.file_path, "wb+")
		self.tool_version = version
		if self.larc_file is None:
			raise IOError("Failed to create file: " + self.file_path)
		# 写入文件头等信息
		self.larc_file.write(b"LARC")	 									# 文件头
		self.larc_file.write(version.encode())								# 工具版本
		self.larc_file.write((0).to_bytes(2+2+1+4, byteorder='little'))		# 记录列表的头地址、长度和总文件数、总长度
		# 记录列表的数据
		list_start:int = len(b"LARC") + len(version.encode()) + (2+2+1+4)
		self.larc_file.seek(len(b"LARC") + len(version.encode()))
		self.larc_file.write(list_start.to_bytes(2, byteorder='little'))	# 记录列表的头地址
		# 刷新缓冲区
		self.larc_file.flush()
		return
	
	def close(self):
		"""
		关闭 .larc 文件
		"""
		if self.larc_file is not None:
			self.larc_file.close()
			self.larc_file = None
		else:
			raise IOError("File is not open: " + self.file_path)
		return

if __name__ == "__main__":
	# 测试代码
	larc = LarcFile("test.larc")
	try:
		larc.open_new()
		print("New LARC file created successfully.")
	except Exception as e:
		print("Error:", e)
	finally:
		larc.close()
		print("LARC file closed.")
