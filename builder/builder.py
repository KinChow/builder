#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Copyright (c) 2024, Zhou Zijian

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import subprocess
import sys
from abc import ABCMeta, abstractmethod
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional


def run_cmd(args: List[str]) -> None:
    try:
        result = subprocess.run(args, check=True, text=True,
                                encoding='utf-8', errors='replace', capture_output=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {' '.join(args)}")
        print(f"错误输出: {e.stderr}")
        sys.exit(1)


class Builder(metaclass=ABCMeta):
    """
    Abstract base class for a Builder.
    This class defines the interface for building and cleaning operations.
    Subclasses must implement the `build` and `clean` methods.
    Methods
    -------
    build(build_options: Optional[List[str]] = None)
        Abstract method to perform the build operation. 
        Parameters:
            build_options (Optional[List[str]]): A list of build options. Default is None.
    clean()
        Abstract method to perform the clean operation.
    """
    @abstractmethod
    def build(self, build_options: Optional[List[str]] = None):
        pass

    @abstractmethod
    def clean(self):
        pass


class BuilderImpl(Builder):
    def __init__(self, build_dir: str):
        self.build_dir = build_dir

    @abstractmethod
    def build(self, build_options: Optional[List[str]] = None):
        pass

    def clean(self):
        shutil.rmtree(self.build_dir, ignore_errors=True)


class NdkBuilder(BuilderImpl):
    def __init__(self, build_dir: str, compiler_prefix: str = ""):
        super().__init__(build_dir)
        self.build_cmd = self._get_ndk_build_command(compiler_prefix)

    def _get_ndk_build_command(self, compiler_prefix: str) -> List[str]:
        compiler = "ndk-build.cmd" if sys.platform == "win32" else "ndk-build"

        if compiler_prefix:
            compiler_path = Path(compiler_prefix) / compiler
        else:
            android_ndk = os.environ.get("ANDROID_NDK")
            if not android_ndk:
                raise EnvironmentError(
                    "ANDROID_NDK environment variable is not set")
            compiler_path = Path(android_ndk) / compiler

        if not compiler_path.exists():
            raise FileNotFoundError(f"{compiler_path} does not exist")

        return [
            str(compiler_path),
            "V=1",
            f"NDK_OUT={self.build_dir}",
            f"NDK_LIBS_OUT={self.build_dir}",
        ]

    def build(self, build_options: Optional[List[str]] = None):
        cmd = self.build_cmd + (build_options or [])
        run_cmd(cmd)


class CMakeBuilder(BuilderImpl):
    def __init__(self, build_dir: str):
        super().__init__(build_dir)
        self.config_cmd = ["cmake", "-B", self.build_dir]
        self.build_cmd = ["cmake", "--build", self.build_dir]

    def build(self, build_options: Optional[List[str]] = None):
        config_cmd = self.config_cmd + (build_options or [])
        run_cmd(config_cmd)
        run_cmd(self.build_cmd)


class CMakeWindowsVsMsvcBuilder(CMakeBuilder):
    def __init__(self, build_dir: str):
        super().__init__(build_dir)
        self.config_cmd += ["-G", "Visual Studio 17 2022"]


class CMakeWindowsMingwBuilder(CMakeBuilder):
    def __init__(self, build_dir: str, compiler_prefix: str = ""):
        super().__init__(build_dir)
        self.config_cmd += self._get_config_cmd(compiler_prefix)

    def _get_config_cmd(self, compiler_prefix: str) -> List[str]:
        make = "mingw32-make.exe"

        if compiler_prefix:
            make_path = Path(compiler_prefix) / make
        else:
            mingw = os.environ.get("MinGW")
            if not mingw:
                raise EnvironmentError(
                    "MinGW environment variable is not set")
            make_path = Path(mingw) / "bin" / make

        if not make_path.exists():
            raise FileNotFoundError(f"{make_path} does not exist")

        return [
            "-G",
            "MinGW Makefiles",
            f"-DCMAKE_MAKE_PROGRAM={make_path}",
        ]


class CMakeClangBuilder(CMakeBuilder):
    def __init__(self, build_dir: str, compiler_prefix: str = ""):
        super().__init__(build_dir)
        self.config_cmd += self._get_config_cmd(compiler_prefix)

    def _get_config_cmd(self, compiler_prefix: str) -> List[str]:
        compiler_c = "clang.exe" if sys.platform == "win32" else "clang"
        compiler_cpp = "clang++.exe" if sys.platform == "win32" else "clang++"

        if compiler_prefix:
            compiler_c_path = Path(compiler_prefix + compiler_c)
            compiler_cpp_path = Path(compiler_prefix + compiler_cpp)
        else:
            llvm = os.environ.get("LLVM")
            if not llvm:
                raise EnvironmentError(
                    "LLVM environment variable is not set")
            compiler_c_path = Path(llvm) / "bin" / compiler_c
            compiler_cpp_path = Path(llvm) / "bin" / compiler_cpp

        if not compiler_c_path.exists():
            raise FileNotFoundError(f"{compiler_c_path} does not exist")
        if not compiler_cpp_path.exists():
            raise FileNotFoundError(f"{compiler_cpp_path} does not exist")

        return [
            "-G",
            "Ninja",
            f"-DCMAKE_C_COMPILER:FILEPATH={compiler_c_path}",
            f"-DCMAKE_CXX_COMPILER:FILEPATH={compiler_cpp_path}",
        ]


class CMakeGccBuilder(CMakeBuilder):
    def __init__(self, build_dir: str, compiler_prefix: str = ""):
        super().__init__(build_dir)
        self.config_cmd += self._get_config_cmd(compiler_prefix)

    def _get_config_cmd(self, compiler_prefix: str) -> List[str]:
        compiler_c = "gcc"
        compiler_cpp = "g++"

        if compiler_prefix:
            compiler_c_path = Path(compiler_prefix + compiler_c)
            compiler_cpp_path = Path(compiler_prefix + compiler_cpp)
        else:
            gcc = os.environ.get("GCC")
            if not gcc:
                raise EnvironmentError(
                    "GCC environment variable is not set")
            compiler_c_path = Path(gcc) / "bin" / compiler_c
            compiler_cpp_path = Path(gcc) / "bin" / compiler_cpp

        if not compiler_c_path.exists():
            raise FileNotFoundError(f"{compiler_c_path} does not exist")
        if not compiler_cpp_path.exists():
            raise FileNotFoundError(f"{compiler_cpp_path} does not exist")

        return [
            "-G",
            "Ninja",
            f"-DCMAKE_C_COMPILER:FILEPATH={compiler_c_path}",
            f"-DCMAKE_CXX_COMPILER:FILEPATH={compiler_cpp_path}",
        ]


class CMakeAndroidBuilder(CMakeBuilder):
    def __init__(self, build_dir: str, compiler_prefix: str = ""):
        super().__init__(build_dir)
        self.config_cmd += self._get_config_cmd(compiler_prefix)

    def _get_config_cmd(self, compiler_prefix: str) -> List[str]:
        if compiler_prefix:
            cmake_toolchain = Path(compiler_prefix) / "build" / \
                "cmake" / "android.toolchain.cmake"
        else:
            android_ndk = os.environ.get("ANDROID_NDK")
            if not android_ndk:
                raise EnvironmentError(
                    "ANDROID_NDK environment variable is not set")
            cmake_toolchain = Path(android_ndk) / "build" / \
                "cmake" / "android.toolchain.cmake"

        if not cmake_toolchain.exists():
            raise FileNotFoundError(f"{cmake_toolchain} does not exist")

        return [
            "-G",
            "Ninja",
            f"-DCMAKE_TOOLCHAIN_FILE={cmake_toolchain}",
            "-DANDROID_ABI=arm64-v8a",
            "-DANDROID_STL=c++_shared",
            "-DANDROID_PLATFORM=android-31",
        ]


class CMakeOhosBuilder(CMakeBuilder):
    def __init__(self, build_dir: str, compiler_prefix: str = ""):
        super().__init__(build_dir)
        self.config_cmd += self._get_config_cmd(compiler_prefix)

    def _get_config_cmd(self, compiler_prefix: str) -> List[str]:
        if compiler_prefix:
            cmake_toolchain = Path(compiler_prefix) / "build" / \
                "cmake" / "ohos.toolchain.cmake"
        else:
            ohos_sdk = os.environ.get("OHOS_SDK")
            if not ohos_sdk:
                raise EnvironmentError(
                    "OHOS_SDK environment variable is not set")
            cmake_toolchain = Path(ohos_sdk) / "build" / \
                "cmake" / "ohos.toolchain.cmake"

        if not cmake_toolchain.exists():
            raise FileNotFoundError(f"{cmake_toolchain} does not exist")

        return [
            "-G",
            "Ninja",
            f"-DCMAKE_TOOLCHAIN_FILE={cmake_toolchain}",
            "-DANDROID_ABI=arm64-v8a",
            "-DANDROID_STL=c++_shared",
            "-DANDROID_PLATFORM=OHOS",
        ]


class BuilderType(Enum):
    """
    Enum class representing different types of builders.

    Attributes:
        NDK: Represents the NDK builder type.
        CMAKE_WINDOWS_VS_MSVC: Represents the CMake builder type for Windows using Visual Studio MSVC.
        CMAKE_WINDOWS_MINGW: Represents the CMake builder type for Windows using MinGW.
        CMAKE_CLANG: Represents the CMake builder type using Clang.
        CMAKE_GCC: Represents the CMake builder type using GCC.
        CMAKE_ANDROID: Represents the CMake builder type for Android.
        CMAKE_OHOS: Represents the CMake builder type for OpenHarmony OS.
    """
    NDK = auto()
    CMAKE_WINDOWS_VS_MSVC = auto()
    CMAKE_WINDOWS_MINGW = auto()
    CMAKE_CLANG = auto()
    CMAKE_GCC = auto()
    CMAKE_ANDROID = auto()
    CMAKE_OHOS = auto()


class BuilderFactory:
    """
    Factory class to create different types of builders based on the provided builder type.

    Methods
    -------
    create(builder_type: BuilderType, build_dir: str, compiler_prefix: str = "") -> Builder
        Static method to create a builder instance based on the provided builder type.
        Parameters:
            builder_type (BuilderType): The type of builder to create.
            build_dir (str): The directory where the build will take place.
            compiler_prefix (str, optional): The compiler prefix to use. Defaults to an empty string.
        Returns:
            Builder: An instance of the specified builder type.
        Raises:
            ValueError: If an invalid builder type is provided.
    """
    @staticmethod
    def create(builder_type: BuilderType, build_dir: str, compiler_prefix: str = "") -> Builder:
        if builder_type == BuilderType.NDK:
            return NdkBuilder(build_dir, compiler_prefix)
        elif builder_type == BuilderType.CMAKE_WINDOWS_VS_MSVC:
            return CMakeWindowsVsMsvcBuilder(build_dir)
        elif builder_type == BuilderType.CMAKE_WINDOWS_MINGW:
            return CMakeWindowsMingwBuilder(build_dir, compiler_prefix)
        elif builder_type == BuilderType.CMAKE_CLANG:
            return CMakeClangBuilder(build_dir, compiler_prefix)
        elif builder_type == BuilderType.CMAKE_GCC:
            return CMakeGccBuilder(build_dir, compiler_prefix)
        elif builder_type == BuilderType.CMAKE_ANDROID:
            return CMakeAndroidBuilder(build_dir, compiler_prefix)
        elif builder_type == BuilderType.CMAKE_OHOS:
            return CMakeOhosBuilder(build_dir, compiler_prefix)
        else:
            raise ValueError(f"Invalid builder type: {builder_type}")
