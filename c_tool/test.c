#include <stdio.h>
#include "larc.h"

int main() {
    printf("Testing Light Archive library...\n");
    
    // 测试创建LARC文件
    struct LarcFile* larc = larcCreate("test.larc");
    if (!larc) {
        printf("Failed to create LARC file\n");
        return 1;
    }
    
    printf("LARC file created successfully\n");
    
    // 测试关闭LARC文件
    larcClose(larc);
    printf("LARC file closed successfully\n");
    
    // 测试打开LARC文件
    larc = larcOpen("test.larc");
    if (!larc) {
        printf("Failed to open LARC file\n");
        return 1;
    }
    
    printf("LARC file opened successfully\n");
    
    // 测试关闭LARC文件
    larcClose(larc);
    printf("LARC file closed successfully\n");
    
    printf("All tests passed!\n");
    return 0;
}
