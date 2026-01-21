#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频合并工具 - Nuitka打包脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def build_with_nuitka():
    """使用Nuitka打包为单文件exe"""
    
    # 获取当前目录
    current_dir = Path(__file__).parent
    script_path = current_dir / "bili_patch.py"
    
    if not script_path.exists():
        print(f"错误: 找不到脚本文件 {script_path}")
        return False
    
    # 构建输出目录
    build_dir = current_dir / "build"
    build_dir.mkdir(exist_ok=True)
    
    # Nuitka构建命令参数
    nuitka_args = [
        sys.executable, "-m", "nuitka",
        "--standalone",           # 创建独立可执行文件
        "--onefile",              # 单文件模式
        "--windows-disable-console",  # 隐藏控制台窗口
        "--output-dir=" + str(build_dir),  # 输出目录
        "--include-package=ttkbootstrap",  # 包含ttkbootstrap
        "--include-package=pathlib",       # 包含pathlib
        "--include-package=json",          # 包含json
        "--include-package=subprocess",    # 包含subprocess
        "--include-package=threading",    # 包含threading
        "--nofollow-imports",             # 不自动包含所有导入
        "--plugin-enable=tk-inter",        # 启用tkinter插件
        "--remove-output",                 # 清理临时文件
        "--assume-yes-for-downloads",     # 自动下载依赖
        "--lto=yes",                       # 启用链接时优化
        str(script_path)                   # 要打包的脚本
    ]
    
    print("开始使用Nuitka打包...")
    print("命令:", " ".join(nuitka_args))
    print("-" * 60)
    
    try:
        # 运行Nuitka构建
        result = subprocess.run(nuitka_args, check=True, capture_output=True, text=True)
        print("构建成功完成!")
        
        # 查找生成的exe文件
        exe_files = list(build_dir.glob("*.exe"))
        if exe_files:
            exe_path = exe_files[0]
            print(f"\n生成的可执行文件: {exe_path}")
            print(f"文件大小: {exe_path.stat().st_size / (1024*1024):.2f} MB")
            
            # 复制到当前目录
            final_exe = current_dir / "B站视频合并工具.exe"
            if final_exe.exists():
                final_exe.unlink()
            
            import shutil
            shutil.copy2(exe_path, final_exe)
            print(f"已复制到: {final_exe}")
            
            return True
        else:
            print("错误: 未找到生成的exe文件")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"构建失败!")
        print(f"错误输出: {e.stderr}")
        print(f"标准输出: {e.stdout}")
        return False
    except Exception as e:
        print(f"构建过程中出现错误: {e}")
        return False

def build_simple():
    """简化版构建命令"""
    
    current_dir = Path(__file__).parent
    script_path = current_dir / "bili_patch.py"
    
    if not script_path.exists():
        print(f"错误: 找不到脚本文件 {script_path}")
        return False
    
    # 简化的Nuitka命令
    nuitka_args = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--windows-disable-console",
        "--output-dir=build",
        "--plugin-enable=tk-inter",
        str(script_path)
    ]
    
    print("使用简化命令构建...")
    print("命令:", " ".join(nuitka_args))
    
    try:
        result = subprocess.run(nuitka_args, check=True)
        print("构建成功!")
        
        # 查找并复制exe文件
        build_dir = current_dir / "build"
        exe_files = list(build_dir.glob("*.exe"))
        if exe_files:
            exe_path = exe_files[0]
            final_exe = current_dir / "B站视频合并工具.exe"
            
            import shutil
            shutil.copy2(exe_path, final_exe)
            print(f"生成的可执行文件: {final_exe}")
            return True
        
        return False
        
    except Exception as e:
        print(f"构建失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("B站视频合并工具 - Nuitka打包脚本")
    print("=" * 60)
    
    # 检查Nuitka是否可用
    try:
        import nuitka
        print("✓ Nuitka已安装")
    except ImportError:
        print("✗ Nuitka未安装，请先安装: pip install nuitka")
        sys.exit(1)
    
    # 选择构建方式
    print("\n选择构建方式:")
    print("1. 完整构建（推荐）")
    print("2. 简化构建")
    
    choice = input("请输入选择 (1/2, 默认1): ").strip()
    
    if choice == "2":
        success = build_simple()
    else:
        success = build_with_nuitka()
    
    if success:
        print("\n" + "=" * 60)
        print("打包完成!")
        print("生成的可执行文件: B站视频合并工具.exe")
        print("=" * 60)
    else:
        print("\n打包失败，请检查错误信息")
        sys.exit(1)