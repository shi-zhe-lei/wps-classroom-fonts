# GitHub 发布准备

## 仓库资料

| 项目 | 已准备的内容 |
| --- | --- |
| Repository name | `wps-classroom-fonts` |
| 显示名称 | WPS Classroom Fonts · WPS 课件字体助手 |
| Description | 麒麟 / Linux 上的 WPS 课件字体助手：离线安装、分组撤销、字体校验与隐私友好的日志。 |
| English description | Offline font helper for WPS on Linux: per-user installation, grouped undo, integrity checks, and privacy-conscious logs. |
| Topics | `wps-office` `linux` `kylin` `fonts` `fontconfig` `mathematics` `education` `offline` `bash` |
| Default branch | `main` |
| Code license | MIT |
| Bundled fonts | STIX Two · SIL OFL 1.1 |
| 首版标签 | `v1.0.0` |
| Release title | `v1.0.0 · 离线安装，分组管理` |

项目尚未设置主页地址或远程仓库地址，避免写入不存在的链接。建好 GitHub 仓库后，可把仓库主页填入 About。默认 README 已有导航、横幅、功能表、使用步骤及授权说明。

## 首次发布步骤

1. 在 GitHub 创建名为 `wps-classroom-fonts` 的空仓库，不额外初始化 README 或许可证。
2. 在 GitHub Desktop 中通过 **Add Local Repository** 选择本地项目目录。也可以使用 GitHub 给出的“push an existing repository”命令连接远程仓库并推送 `main`。
3. 在 About 中填入上面的简介和 Topics。
4. 查看 Actions 的 `Validate` 工作流，确认检查通过。
5. 使用已交付的 `wps-classroom-fonts-v1.0.0.zip` 及 `.zip.sha256`，或运行 `python3 tools/build-release.py` 重新生成。构建要求已有提交且已跟踪文件没有未提交修改。
6. 创建 `v1.0.0` Release，复制下面的更新说明，上传这两个生成文件。不要上传整个本地目录的手动压缩包。

GitHub Desktop 的 Publish repository 可直接发布本地仓库；发布范围以 Git 中的文件为准。先完成公开检查，再按需要选择可见性。

## 首版更新说明

WPS Classroom Fonts 的首个公开版本，为麒麟 / Linux 上的课件提供离线字体准备和管理工具。

- 附带 9 个 STIX Two 开源字体文件，可直接一键安装。
- 保留完整 58 文件配置，支持在本地导入有权使用的扩展字体。
- 数学与英语、常用中文、补充字体分别安装与撤销。
- 安装前检查完整性和目标冲突，重复运行自动保留相同文件。
- 撤销文件移入备份，兼容旧版安装目录。
- 日志默认留在账号缓存中，并隐藏账号主目录和项目路径。
- 提供隔离安装测试、桌面入口验证、公开内容检查和可重复打包工具。

公开发布包仅包含 STIX Two 字体及工具；不附带 Windows、MathType、方正等未确认再分发许可的扩展字体。安装完成后请重新打开 WPS，用原课件确认实际显示效果。

## 本地 Git 备注

提交身份使用维护者指定的 Git 用户，并仅写入当前仓库配置，不改变全局 Git 配置。Git 提交会保留作者姓名和邮箱；如需 GitHub 贡献归属，应确保该邮箱已关联相应 GitHub 账号。

## English publication notes

Create an empty GitHub repository named `wps-classroom-fonts`, add the delivered local repository in GitHub Desktop, and publish `main` manually. Set the description and topics from the table above. Wait for the `Validate` workflow to pass, then create release `v1.0.0` and attach the public ZIP and its SHA-256 file. The transfer archive containing `.git` is for moving the repository between computers; it is not a release asset.
