# 工具 / Tools

`font-actions.sh` 负责安装、检查和撤销；`oneclick.sh` 为桌面入口保留终端输出。运行时只操作当前账号，字体字节必须匹配分组清单。完整预检查成功后才修改字体，重复安装保留相同文件，撤销先校验再移动到备份。

`import-fonts.py` 按校验值导入本地字体，不下载文件；`verify-public.py` 检查暂存区或指定 Git 提交；`build-release.py` 从通过审查的干净提交生成 ZIP 与 SHA-256 文件。公开包只包含清单允许的九个 STIX 文件。

The shell tools install, inspect, and undo fonts for the current user. All source and destination checks precede font changes. Identical files are preserved on repeat installation; undo validates managed files before moving them to backup.

The Python tools import exact local font versions, audit staged or committed public files, and build release archives from an audited clean commit. The archive boundary is Git history, not every file in the local folder. No tool uploads fonts or publishes a repository.
