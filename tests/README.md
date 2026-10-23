# 测试 / Tests

使用非 root 的 Linux 账号运行 `bash tests/integration.sh`。Ubuntu 测试依赖为 `fontconfig desktop-file-utils python3-gi shellcheck git`，另需 Python 3.9+、Bash 4+、GNU coreutils 和 util-linux。静态检查命令为 `shellcheck -x install.sh check.sh undo.sh tools/*.sh tests/*.sh`。

- `test_runtime.py`：真实 Fontconfig 安装、重复运行、检查、撤销与恢复、文件损坏、路径和并发保护、桌面入口及本地导入。
- `test_public.py`：暂存内容检查、日志与未批准字体拦截、账号路径与凭据格式拦截。
- `test_release.py`：从提交生成公开 ZIP、校验文件、执行权限、重复构建一致性，以及脏工作区、未批准字体、无提交和非法版本的拒绝。

完整 65 文件包测试需设置 `WCF_TEST_FULL_SOURCE` 指向本地已准备好的字体包；未设置时跳过完整包与旧版升级两项测试。升级测试会先安装原有 58 个文件，再补装 7 个，并核对独立撤销后原有字体逐字节不变。测试使用专属临时字体目录和 Fontconfig 配置，不改写 `HOME`，不安装到日常账号的字体目录。

Run `bash tests/integration.sh` as a non-root Linux user with the dependencies listed above. Runtime tests use real Fontconfig with isolated data and cache directories. Publication and release tests create disposable Git repositories and never modify the real project's history.

Set `WCF_TEST_FULL_SOURCE` to an authorized local 65-file package to enable the optional full-package and legacy-upgrade tests. Public CI does not carry these additional fonts and skips those two cases. The upgrade test preserves the original 58 files while adding and independently undoing the seven new files. A passing suite verifies font operations and launcher parsing; actual document appearance must still be checked in the target Kylin/WPS environment.
