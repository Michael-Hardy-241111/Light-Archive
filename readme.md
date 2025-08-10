# Light Archive

### Languages

- [简体中文](#zh-hans-chinese)
- [American English](#en-us-english)

## (zh-hans) Chinese

**轻量容器文件格式**

> 这是一种新型容器文件格式（.larc），拥有与文件夹一样的功能（修改内部文件需要适配对应编辑器）。

它相比其他的打包格式和压缩格式，优点是在修改其内部文件时拥有修改普通文件的速度和效率，无需其他步骤。如果你没有设置加密、压缩，那么无需任何步骤就可以修改内部文件。

它诞生的初衷是为了提高修改打包的程序的效率，为服务器提供一种一次性传输多个文件的高效方案。

### 该格式现有功能

**目前的版本：0.1.0**

1. 加入、移除文件
2. 打包、解包

### 接下来的更新计划

提供Python、C/C++编程语言的免费API。

### 其余内容

所有正式版的更新版本记录都在[这里](instructions/version_instructions_zh_hans.html)。

## (en-us) English

**Lightweight Archive Container Format**

> This is a novel container file format (.larc) that provides folder-like functionality. Modifying internal files requires compatible editor support.

Compared to other archive and compression formats, its key advantage is enabling direct modification of internal files with the same speed and efficiency as regular files - no additional steps required. When encryption or compression aren't enabled, internal files can be modified without any intermediate processes.

The format was created to improve efficiency when working with packaged applications and to provide servers with a high-performance solution for transferring multiple files in a single operation.

### Current Features

**Current version: 0.1.0**

1. Add/remove files  
2. Pack/unpack archives  

### Planned Updates

Free APIs for Python and C/C++ programming languages.

### Additional Information

All release version histories are documented [here](instructions/version_instructions_en_us.html).  
