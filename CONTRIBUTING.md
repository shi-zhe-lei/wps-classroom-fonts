# 贡献指南

欢迎提交问题、改进脚本或补充文档。描述问题时请写明操作命令、系统版本、期望与实际结果；去掉账号名、个人路径、课件内容和无关日志。问题模板已包含这些提示。

## 修改前约定

- 所有文件名使用英文；面向用户的说明可以使用中文。
- Shell 文件使用 UTF-8 / LF，安装运行时只依赖基础 Linux 工具。
- 安装和撤销仅作用于当前账号，保留旧版安装目录兼容性。
- 字体版本由 SHA-256 固定；改清单时必须核对家族名称及分组。
- 添加可分发字体时必须保留上游许可证，明确数量、体积和必要性。
- 不添加个人日志、凭据、截图或无法确认分发许可的字体。

## 本地验证

```bash
bash tests/integration.sh
git add .
python3 tools/verify-public.py
git diff --cached --check
```

测试需要 Linux 的 Fontconfig、desktop-file-utils、Python 3.9+ 与 Python GObject（用于桌面入口解析）。Ubuntu 可用 `fontconfig desktop-file-utils python3-gi` 软件包。测试通过专用 `XDG_DATA_HOME` 和 Fontconfig 配置隔离真实用户字体，不修改 `HOME`。

若测试机器上有准备好的完整 58 文件包，设置 `WCF_TEST_FULL_SOURCE` 为该包目录，测试会额外验证完整安装、每组撤销及恢复；CI 默认只测试随仓库分发的开源字体。

使用 `git update-index --chmod=+x <file>` 保留脚本与 `.desktop` 的执行权限。提交前概述改动原因和验证结果，避免只描述改了哪些文件。
