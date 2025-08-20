#include <iso646.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 禁用 CRT 安全警告
#define _CRT_SECURE_NO_WARNINGS

#define LARC_HEADER ((char[4]){'L', 'A', 'R', 'C'})
#define LARC_FOOTER ((char)0x03)
#define LARC_DEFAULT_VERSION ((uint8_t[3]){0, 2, 0})

struct FileStruct {
    // 文件索引
    uint32_t index;
    // 文件偏移
    uint64_t offset;
    // 文件大小
    uint64_t size;
    // 文件名
    char* name;
};

struct LarcFile {
    // LARC 文件指针
    FILE* larc_file;
    // LARC 文件版本
    uint8_t version[3];
    // 加密标志
    uint8_t encryption_flag;
    // 密钥长度
    uint32_t key_length;
    // 文件列表头偏移
    uint32_t list_header_offset;
    // 文件列表长度
    uint32_t list_length;
    // 文件数量
    uint32_t file_count;
    // 文件总长度
    uint64_t file_total_length;
    // 文件列表，一个数组，每一个元素是 FileStruct 结构体指针
    struct FileStruct** file_list;
};

/**
 * @brief 关闭 LARC 文件
 * 
 * @param larc_file LarcFile 结构体指针
 * @return int 0 成功 1 失败
 */
int larc_close(struct LarcFile* larc_file) {
    // 关闭文件
    fclose(larc_file->larc_file);
    // 释放文件列表内存
    for (uint32_t i = 0; i < larc_file->file_count; ++ i) {
        free(larc_file->file_list[i]);
    }
    free(larc_file->file_list);
    // 释放 LarcFile 结构体内存
    free(larc_file);
    return 0;
}

/**
 * @brief 打开 LARC 文件
 * 
 * @param filename 文件名
 * @return struct LarcFile* LarcFile 结构体指针
 */
struct LarcFile* larc_open(const char* filename) {
    // 打开文件
    FILE* file = fopen(filename, "rb+");
    if (file == NULL) {
        return NULL;
    }
    // 读取文件头
    char header[4];
    fread(header, 1, 4, file);
    // 检查文件头是否正确
    if (memcmp(header, LARC_HEADER, 4) != 0) {
        fclose(file);
        return NULL;
    }
    // 分配 LarcFile 结构体内存
    struct LarcFile* larc_file = malloc(sizeof(struct LarcFile));
    if (larc_file == NULL) {
        fclose(file);
        return NULL;
    }
    // 初始化 LarcFile 结构体
    larc_file->larc_file = file;
    larc_file->version[0] = 0;
    larc_file->version[1] = 0;
    larc_file->version[2] = 0;
    larc_file->encryption_flag = 0;
    larc_file->key_length = 0;
    larc_file->list_header_offset = 0;
    larc_file->list_length = 0;
    larc_file->file_count = 0;
    larc_file->file_total_length = 0;
    larc_file->file_list = NULL;
    // 读取文件版本
    fread(&larc_file->version, 1, 3, file);
    // 读取加密标志
    fread(&larc_file->encryption_flag, 1, 1, file);
    // 读取密钥长度
    fread(&larc_file->key_length, 1, 4, file);
    // 读取文件列表头偏移
    fread(&larc_file->list_header_offset, 1, 4, file);
    // 读取文件列表长度
    fread(&larc_file->list_length, 1, 4, file);
    // 读取文件数量
    fread(&larc_file->file_count, 1, 4, file);
    // 读取文件总长度
    fread(&larc_file->file_total_length, 1, 8, file);
    // 分配文件列表内存
    larc_file->file_list = calloc(larc_file->file_count, sizeof(struct FileStruct*));
    if (larc_file->file_list == NULL) {
        fclose(file);
        free(larc_file);
        return NULL;
    }
    // 读取文件列表
    fseek(file, larc_file->list_header_offset, SEEK_SET);
    for (uint32_t i = 0; i < larc_file->file_count; ++ i) {
        larc_file->file_list[i] = malloc(sizeof(struct FileStruct));
        if (larc_file->file_list[i] == NULL) {
            fclose(file);
            free(larc_file);
            return NULL;
        }
        // 读取文件索引
        fread(&larc_file->file_list[i]->index, 1, 4, file);
        // 读取文件偏移
        fread(&larc_file->file_list[i]->offset, 1, 8, file);
        // 读取文件大小
        fread(&larc_file->file_list[i]->size, 1, 8, file);
        // 循环读取文件名
        uint32_t name_length = 0;
        char* name = NULL;
        name = malloc(1);
        if (name == NULL) {
            fclose(file);
            free(larc_file);
            for (uint32_t j = 0; j < i; ++ j) {
                free(larc_file->file_list[j]);
            }
            free(larc_file->file_list);
            return NULL;
        }
        while (1) {
            char c = 0;
            fread(&c, 1, 1, file);
            if (c == '\0') {
                break;
            }
            name_length ++;
            name = realloc(name, name_length + 1);
            if (name == NULL) {
                fclose(file);
                free(larc_file);
                for (uint32_t j = 0; j < i; ++ j) {
                    free(larc_file->file_list[j]);
                }
                free(larc_file->file_list);
                return NULL;
            }
            name[name_length - 1] = c;
        }
        name[name_length] = '\0';
        larc_file->file_list[i]->name = name;
    }
    // 读取文件列表结束符
    char footer = 0;
    fread(&footer, 1, 1, file);
    if (footer != LARC_FOOTER) {
        fclose(file);
        free(larc_file);
        for (uint32_t j = 0; j < larc_file->file_count; ++ j) {
            free(larc_file->file_list[j]);
        }
        free(larc_file->file_list);
        return NULL;
    }
    return larc_file;
}

/**
 * @brief 创建 LARC 文件
 * 
 * @param filename 文件名
 * @return struct LarcFile* LarcFile 结构体指针
 */
struct LarcFile* larc_create(const char* filename) {
    // 打开文件
    FILE* file = fopen(filename, "wb");
    if (file == NULL) {
        return NULL;
    }
    // 写入文件头
    fwrite(LARC_HEADER, 1, 4, file);
    // 分配 LarcFile 结构体内存
    struct LarcFile* larc_file = malloc(sizeof(struct LarcFile));
    if (larc_file == NULL) {
        fclose(file);
        return NULL;
    }
    // 初始化 LarcFile 结构体
    larc_file->larc_file = file;
    larc_file->version[0] = LARC_DEFAULT_VERSION[0];
    larc_file->version[1] = LARC_DEFAULT_VERSION[1];
    larc_file->version[2] = LARC_DEFAULT_VERSION[2];

    larc_file->encryption_flag = 0;
    larc_file->key_length = 0;
    larc_file->list_header_offset = 0;
    larc_file->list_length = 0;
    larc_file->file_count = 0;
    larc_file->file_total_length = 0;
    larc_file->file_list = NULL;
    // 写入文件版本
    fwrite(&larc_file->version, 1, 3, file);
    // 写入加密标志
    fwrite(&larc_file->encryption_flag, 1, 1, file);
    // 写入密钥长度
    fwrite(&larc_file->key_length, 1, 4, file);
    // 写入文件列表头偏移
    fwrite(&larc_file->list_header_offset, 1, 4, file);
    // 写入文件列表长度
    fwrite(&larc_file->list_length, 1, 4, file);
    // 写入文件数量
    fwrite(&larc_file->file_count, 1, 4, file);
    // 写入文件总长度
    fwrite(&larc_file->file_total_length, 1, 8, file);
    // 写入文件列表结束符
    char footer = LARC_FOOTER;
    fwrite(&footer, 1, 1, file);
    // 刷新文件缓冲区
    fflush(file);
    return larc_file;
}
