@echo off
echo Building Light Archive library for Windows...

REM 编译为动态链接库
cl /LD /DLARC_EXPORTS larc.c /link /OUT:larc.dll

REM 编译为静态库
REM cl /c /DLARC_EXPORTS larc.c
REM lib larc.obj /OUT:larc.lib

echo Build completed. Library: larc.dll

REM 测试编译
if exist "larc.dll" (
    echo Testing library...
    cl test.c larc.lib /Fetest.exe
    echo Test executable: test.exe
) else (
    echo Build failed!
    exit /b 1
)
