# Builder

## 介绍

Builder 是一个用于构建 C++ 程序的强大工具。它提供了一个统一的接口来处理不同的构建系统和编译器,简化了 C++ 项目的构建过程。



## 特性

- 支持多种构建系统（CMake, NDK）
- 兼容多种编译器（MSVC, MinGW, Clang, GCC）
- 支持跨平台构建（Windows, Android, OpenHarmony OS）
- 简单易用的 API



## 安装

安装 Builder 有两种方式:使用安装包或设置环境变量。

### 使用安装包

```bash
cd PATH_TO_BUILDER
pip install .
```



### 设置环境变量

设置builder包的环境变量

```
# Windows
$env:PYTHONPATH="PATH_TO_BUILDER"

# Linux/macOS
export PYTHONPATH=PATH_TO_BUILDER:$PYTHONPATH
```



## 使用说明

基本用法如下:

```
from builder import BuilderFactory, BuilderType

# 创建一个构建器实例
builder = BuilderFactory.create(BuilderType.CMAKE_GCC, "build_directory", "compiler_prefix")

# 执行构建
builder.build()

# 清理构建文件
builder.clean()
```



### 可用的构建器类型

Builder 支持以下构建器类型:

- `BuilderType.NDK`
- `BuilderType.CMAKE_WINDOWS_VS_MSVC`
- `BuilderType.CMAKE_WINDOWS_MINGW`
- `BuilderType.CMAKE_CLANG`
- `BuilderType.CMAKE_GCC`
- `BuilderType.CMAKE_ANDROID`
- `BuilderType.CMAKE_OHOS`



### Builder 接口

所有构建器都实现了以下接口:

- `build()`: 执行构建过程
- `clean()`: 清理构建文件
