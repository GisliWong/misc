# PleaseStopUpdatePCL

一个用于修改 PCL 启动器配置的小工具，通过修改 `setup.ini` 中的 `SystemSystemUpdate` 参数，阻止启动器自动更新。

## 使用方法

1. 拖入 PCL 的 `.exe` 程序或 `.lnk` 快捷方式，也可以点击窗口选择文件。
2. 程序自动定位 `PCL\setup.ini`。
3. 将 `SystemSystemUpdate` 参数设置为 `3`；若参数不存在，则自动新增。
4. 修改前自动创建 `setup.ini.bak` 备份文件。

## 运行环境
- Windows

## 仅限个人使用，禁止违反《中华人民共和国网络安全法》
