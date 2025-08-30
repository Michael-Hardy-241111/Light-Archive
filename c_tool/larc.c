#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 跨平台目录创建支持
#ifdef _WIN32
    #include <direct.h>
    #define mkdir(dir, mode) _mkdir(dir)
#else
    #include <sys/stat.h>
    #include <sys/types.h>
#endif

// 禁用 CRT 安全警告
#define _CRT_SECURE_NO_WARNINGS

#define LARC_HEADER ((char[4]){'L', 'A', 'R', 'C'})
#define LARC_FOOTER ((char)0x03)
#define LARC_DEFAULT_VERSION ((uint8_t[3]){0, 2, 0})

struct FileStruct
{
    // 文件索引
    uint32_t index;
    // 文件偏移
    uint64_t offset;
    // 文件大小
    uint64_t size;
    // 文件名
    char* name;
};

struct LarcFile
{
    // LARC 文件指针
    FILE* larcFile;
    // LARC 文件版本
    uint8_t version[3];
    // 加密标志
    uint8_t encryptionFlag;
    // 密钥长度
    uint32_t keyLength;
    // 文件列表头偏移
    uint32_t listHeaderOffset;
    // 文件列表长度
    uint32_t listLength;
    // 文件数量
    uint32_t fileCount;
    // 文件总长度
    uint64_t fileTotalLength;
    // 文件列表，一个数组，每一个元素是 FileStruct 结构体指针
    struct FileStruct** fileList;
};

/**
 * 创建新的LARC文件并初始化文件结构
 * @param fileName 要创建的LARC文件路径
 * @return 成功返回LarcFile指针，失败返回NULL
 * @note 文件头包含4字节标识、3字节版本号(修订.次.主)、1字节加密标志
 */
struct LarcFile* larcCreate(const char* fileName)
{
    FILE* fp = fopen(fileName, "wb+");
    if (!fp) {
        perror("无法创建文件");
        return NULL;
    }

    // 初始化32字节头信息（含文件结束符）
    uint8_t header[33] = {
        'L','A','R','C',  // 文件头 (4B)
        LARC_DEFAULT_VERSION[0], LARC_DEFAULT_VERSION[1], LARC_DEFAULT_VERSION[2], // 版本号 (修订.次.主)
        0,                 // 加密标志 (1B)
        0,0,0,0,          // 密钥长度 (4B)
        0,0,0,0,          // 列表头偏移 (4B)
        0,0,0,0,          // 列表长度 (4B)
        0,0,0,0,          // 文件数量 (4B)
        0,0,0,0,0,0,0,0,  // 总长度 (8B)
        (uint8_t)'\x03'    // 文件结束符 (1B)
    };

    struct LarcFile* larc = malloc(sizeof(struct LarcFile));
    if (!larc) {
        perror("内存分配失败");
        fclose(fp);
        return NULL;
    }

    // 一次性写入完整头信息
    if (fwrite(header, 1, sizeof(header), fp) != sizeof(header)) {
        perror("文件头写入失败");
        free(larc);
        fclose(fp);
        return NULL;
    }

    // 初始化结构体
    larc->larcFile = fp;
    memcpy(larc->version, LARC_DEFAULT_VERSION, sizeof(LARC_DEFAULT_VERSION));  // 版本号
    return larc;
}

/**
 * 打开现有LARC文件并验证文件结构
 * @param fileName 要打开的LARC文件路径
 * @return 成功返回初始化好的LarcFile指针，失败返回NULL
 * @warning 必须通过larcClose()释放资源
 */
struct LarcFile* larcOpen(const char* fileName)
{
    FILE* fp = fopen(fileName, "rb+");
    if (!fp) {
        perror("文件打开失败");
        return NULL;
    }

    // 验证文件头
    uint8_t header[32];
    if (fread(header, 1, sizeof(header), fp) != sizeof(header)) {
        perror("文件头读取失败");
        fclose(fp);
        return NULL;
    }

    // 检查文件标识
    if (memcmp(header, "LARC", 4) != 0) {
        fprintf(stderr, "无效的文件格式\n");
        fclose(fp);
        return NULL;
    }

    struct LarcFile* larc = malloc(sizeof(struct LarcFile));
    if (!larc) {
        perror("内存分配失败");
        fclose(fp);
        return NULL;
    }

    // 初始化结构体
    larc->larcFile = fp;
    memcpy(larc->version, header+4, 3);
    larc->encryptionFlag = header[7];
    
    // 解析其他头字段
    larc->keyLength = *(uint32_t*)(header+8);
    larc->listHeaderOffset = *(uint32_t*)(header+12);
    larc->listLength = *(uint32_t*)(header+16);
    larc->fileCount = *(uint32_t*)(header+20);
    larc->fileTotalLength = *(uint64_t*)(header+24);

    return larc;
}

/**
 * 关闭LARC文件并释放资源
 * @param larc 要关闭的LarcFile指针
 * @note 必须调用此函数释放文件资源
 */
void larcClose(struct LarcFile* larc)
{
    if (larc) {
        fclose(larc->larcFile);
        // 释放文件列表
        if (larc->fileList) {
            for (int i = 0; i < larc->fileCount; i++) {
                free(larc->fileList[i]);
            }
            free(larc->fileList);
        }
        free(larc);
    }
    return;
}

/**
 * 打包多个文件到LARC文件
 * @param larc 目标LarcFile指针
 * @param fileNames 文件名数组
 * @param fileCount 文件数量
 * @return 成功返回0，失败返回-1
 * @warning 文件名数组必须以NULL结尾
 */

int packFiles(struct LarcFile* larc, const char** fileNames, int fileCount)
{
    if (!larc || !fileNames || fileCount <= 0) {
        fprintf(stderr, "无效的参数\n");
        return -1;
    }

    // 获取当前文件位置（文件内容开始位置）
    fseek(larc->larcFile, 0, SEEK_END);
    uint64_t currentOffset = ftell(larc->larcFile);

    // 逐个处理文件
    for (int i = 0; i < fileCount; i++) {
        const char* fileName = fileNames[i];
        FILE* sourceFile = fopen(fileName, "rb");
        if (!sourceFile) {
            perror("无法打开源文件");
            fprintf(stderr, "文件: %s\n", fileName);
            // 清理已分配的内存
            for (int j = 0; j < i; j++) {
                free(larc->fileList[j]->name);
                free(larc->fileList[j]);
            }
            return -1;
        }

        // 获取文件大小
        fseek(sourceFile, 0, SEEK_END);
        uint64_t fileSize = ftell(sourceFile);
        fseek(sourceFile, 0, SEEK_SET);

        // 创建文件结构
        struct FileStruct* fileStruct = malloc(sizeof(struct FileStruct));
        if (!fileStruct) {
            perror("内存分配失败");
            fclose(sourceFile);
            // 清理已分配的内存
            for (int j = 0; j < i; j++) {
                free(larc->fileList[j]->name);
                free(larc->fileList[j]);
            }
            return -1;
        }

        fileStruct->index = i;
        fileStruct->offset = currentOffset;
        fileStruct->size = fileSize;
        fileStruct->name = malloc(strlen(fileName) + 1);
        if (!fileStruct->name) {
            perror("内存分配失败");
            free(fileStruct);
            fclose(sourceFile);
            // 清理已分配的内存
            for (int j = 0; j < i; j++) {
                free(larc->fileList[j]->name);
                free(larc->fileList[j]);
            }
            return -1;
        }
        strcpy(fileStruct->name, fileName);

        larc->fileList[i] = fileStruct;

        // 写入文件内容
        uint8_t buffer[4096];
        size_t bytesRead;
        while ((bytesRead = fread(buffer, 1, sizeof(buffer), sourceFile)) > 0) {
            if (fwrite(buffer, 1, bytesRead, larc->larcFile) != bytesRead) {
                perror("文件写入失败");
                fclose(sourceFile);
                // 清理已分配的内存
                for (int j = 0; j <= i; j++) {
                    free(larc->fileList[j]->name);
                    free(larc->fileList[j]);
                }
                return -1;
            }
        }

        fclose(sourceFile);
        currentOffset += fileSize;
        larc->fileTotalLength += fileSize;
    }

    // 更新文件数量
    larc->fileCount = fileCount;

    // 记录文件列表头位置
    larc->listHeaderOffset = currentOffset;

    // 写入文件列表
    for (int i = 0; i < fileCount; i++) {
        struct FileStruct* file = larc->fileList[i];
        
        // 写入文件索引 (4B)
        if (fwrite(&file->index, sizeof(uint32_t), 1, larc->larcFile) != 1) {
            perror("文件索引写入失败");
            return -1;
        }
        
        // 写入文件偏移 (8B)
        if (fwrite(&file->offset, sizeof(uint64_t), 1, larc->larcFile) != 1) {
            perror("文件偏移写入失败");
            return -1;
        }
        
        // 写入文件大小 (8B)
        if (fwrite(&file->size, sizeof(uint64_t), 1, larc->larcFile) != 1) {
            perror("文件大小写入失败");
            return -1;
        }
        
        // 写入文件名长度 (4B)
        uint32_t nameLength = strlen(file->name);
        if (fwrite(&nameLength, sizeof(uint32_t), 1, larc->larcFile) != 1) {
            perror("文件名长度写入失败");
            return -1;
        }
        
        // 写入文件名
        if (fwrite(file->name, 1, nameLength, larc->larcFile) != nameLength) {
            perror("文件名写入失败");
            return -1;
        }
    }

    // 更新列表长度
    larc->listLength = ftell(larc->larcFile) - larc->listHeaderOffset;

    // 更新文件头信息
    fseek(larc->larcFile, 20, SEEK_SET); // 文件数量位置
    if (fwrite(&larc->fileCount, sizeof(uint32_t), 1, larc->larcFile) != 1) {
        perror("文件头更新失败");
        return -1;
    }
    
    fseek(larc->larcFile, 24, SEEK_SET); // 总长度位置
    if (fwrite(&larc->fileTotalLength, sizeof(uint64_t), 1, larc->larcFile) != 1) {
        perror("文件头更新失败");
        return -1;
    }
    
    fseek(larc->larcFile, 12, SEEK_SET); // 列表头偏移位置
    if (fwrite(&larc->listHeaderOffset, sizeof(uint32_t), 1, larc->larcFile) != 1) {
        perror("文件头更新失败");
        return -1;
    }
    
    fseek(larc->larcFile, 16, SEEK_SET); // 列表长度位置
    if (fwrite(&larc->listLength, sizeof(uint32_t), 1, larc->larcFile) != 1) {
        perror("文件头更新失败");
        return -1;
    }

    return 0;
}

/**
 * 解包LARC文件到指定目录
 * @param larc 要解包的LarcFile指针
 * @param outputDir 输出目录路径
 * @return 成功返回0，失败返回-1
 */
int unPackFiles(struct LarcFile* larc, const char* outputDir)
{
    if (!larc || !outputDir) {
        fprintf(stderr, "无效的参数\n");
        return -1;
    }

    // 检查文件列表是否已加载
    if (!larc->fileList) {
        // 读取文件列表
        fseek(larc->larcFile, larc->listHeaderOffset, SEEK_SET);
        
        larc->fileList = malloc(sizeof(struct FileStruct*) * larc->fileCount);
        if (!larc->fileList) {
            perror("内存分配失败");
            return -1;
        }

        for (uint32_t i = 0; i < larc->fileCount; i++) {
            struct FileStruct* fileStruct = malloc(sizeof(struct FileStruct));
            if (!fileStruct) {
                perror("内存分配失败");
                // 清理已分配的内存
                for (uint32_t j = 0; j < i; j++) {
                    free(larc->fileList[j]->name);
                    free(larc->fileList[j]);
                }
                free(larc->fileList);
                larc->fileList = NULL;
                return -1;
            }

            // 读取文件索引
            if (fread(&fileStruct->index, sizeof(uint32_t), 1, larc->larcFile) != 1) {
                perror("文件索引读取失败");
                free(fileStruct);
                for (uint32_t j = 0; j < i; j++) {
                    free(larc->fileList[j]->name);
                    free(larc->fileList[j]);
                }
                free(larc->fileList);
                larc->fileList = NULL;
                return -1;
            }

            // 读取文件偏移
            if (fread(&fileStruct->offset, sizeof(uint64_t), 1, larc->larcFile) != 1) {
                perror("文件偏移读取失败");
                free(fileStruct);
                for (uint32_t j = 0; j < i; j++) {
                    free(larc->fileList[j]->name);
                    free(larc->fileList[j]);
                }
                free(larc->fileList);
                larc->fileList = NULL;
                return -1;
            }

            // 读取文件大小
            if (fread(&fileStruct->size, sizeof(uint64_t), 1, larc->larcFile) != 1) {
                perror("文件大小读取失败");
                free(fileStruct);
                for (uint32_t j = 0; j < i; j++) {
                    free(larc->fileList[j]->name);
                    free(larc->fileList[j]);
                }
                free(larc->fileList);
                larc->fileList = NULL;
                return -1;
            }

            // 读取文件名长度
            uint32_t nameLength;
            if (fread(&nameLength, sizeof(uint32_t), 1, larc->larcFile) != 1) {
                perror("文件名长度读取失败");
                free(fileStruct);
                for (uint32_t j = 0; j < i; j++) {
                    free(larc->fileList[j]->name);
                    free(larc->fileList[j]);
                }
                free(larc->fileList);
                larc->fileList = NULL;
                return -1;
            }

            // 读取文件名
            fileStruct->name = malloc(nameLength + 1);
            if (!fileStruct->name) {
                perror("内存分配失败");
                free(fileStruct);
                for (uint32_t j = 0; j < i; j++) {
                    free(larc->fileList[j]->name);
                    free(larc->fileList[j]);
                }
                free(larc->fileList);
                larc->fileList = NULL;
                return -1;
            }

            if (fread(fileStruct->name, 1, nameLength, larc->larcFile) != nameLength) {
                perror("文件名读取失败");
                free(fileStruct->name);
                free(fileStruct);
                for (uint32_t j = 0; j < i; j++) {
                    free(larc->fileList[j]->name);
                    free(larc->fileList[j]);
                }
                free(larc->fileList);
                larc->fileList = NULL;
                return -1;
            }
            fileStruct->name[nameLength] = '\0';

            larc->fileList[i] = fileStruct;
        }
    }

    // 创建输出目录（跨平台兼容）
    mkdir(outputDir, 0755);

    // 逐个提取文件
    for (uint32_t i = 0; i < larc->fileCount; i++) {
        struct FileStruct* file = larc->fileList[i];
        
        // 构建输出文件路径（跨平台路径分隔符）
        char outputPath[512];
        #ifdef _WIN32
            snprintf(outputPath, sizeof(outputPath), "%s\\%s", outputDir, file->name);
        #else
            snprintf(outputPath, sizeof(outputPath), "%s/%s", outputDir, file->name);
        #endif

        // 创建输出文件
        FILE* outputFile = fopen(outputPath, "wb");
        if (!outputFile) {
            perror("无法创建输出文件");
            fprintf(stderr, "文件: %s\n", outputPath);
            return -1;
        }

        // 定位到文件数据位置
        fseek(larc->larcFile, file->offset, SEEK_SET);

        // 读取并写入文件数据
        uint8_t buffer[4096];
        uint64_t remaining = file->size;
        
        while (remaining > 0) {
            size_t toRead = remaining > sizeof(buffer) ? sizeof(buffer) : remaining;
            size_t bytesRead = fread(buffer, 1, toRead, larc->larcFile);
            
            if (bytesRead == 0) {
                perror("文件读取失败");
                fclose(outputFile);
                return -1;
            }

            if (fwrite(buffer, 1, bytesRead, outputFile) != bytesRead) {
                perror("文件写入失败");
                fclose(outputFile);
                return -1;
            }

            remaining -= bytesRead;
        }

        fclose(outputFile);
        printf("已提取文件: %s\n", outputPath);
    }

    return 0;
}
