#!/bin/bash
# 跨平台编译脚本 for Linux/macOS

echo "Building Light Archive library for Linux/macOS..."

# 编译为动态链接库
gcc -shared -fPIC -DLARC_EXPORTS -o liblarc.so larc.c

# 编译为静态库
# gcc -c -DLARC_EXPORTS larc.c
# ar rcs liblarc.a larc.o

echo "Build completed. Library: liblarc.so"

# 测试编译
if [ -f "liblarc.so" ]; then
    echo "Testing library..."
    gcc -o test test.c -L. -llarc
    echo "Test executable: test"
else
    echo "Build failed!"
    exit 1
fi
