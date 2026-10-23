# GitHub 发布指南

## 仓库资料

| 项目 | 内容 |
| --- | --- |
| Repository | [shi-zhe-lei/wps-classroom-fonts](https://github.com/shi-zhe-lei/wps-classroom-fonts) |
| 显示名称 | WPS Classroom Fonts · WPS 课件字体助手 |
| Description | 麒麟 / Linux 上的 WPS 课件字体助手：离线安装、分组撤销、字体校验与隐私友好的日志。 |
| English description | Offline font helper for WPS on Linux: per-user installation, grouped undo, integrity checks, and privacy-conscious logs. |
| Topics | `wps-office` `linux` `kylin` `fonts` `fontconfig` `mathematics` `education` `offline` `bash` |
| Default branch | `main` |
| Code license | MIT |
| Bundled fonts | 9 个 STIX Two 字体文件 · SIL OFL 1.1 |
| 当前版本 | `v1.1.0` |
| Release title | `v1.1.0 · 新增课件字体组，支持独立撤销` |

仓库的 `main` 分支和 Release 是分别更新的。推送代码不会自动替换已有下载包；每次更新需要从对应提交重新构建，并发布新版本。

## 发布步骤

1. 更新 `VERSION`、`CHANGELOG.md` 和本页的版本资料，将本次更新说明保存到 `docs/releases/`。检查文档与实际字体清单一致。
2. 按 [测试说明](../tests/README.md) 运行适用的检查。涉及本地完整包时，也要运行完整包与旧版升级测试；这些字体不会交给公开 CI。
3. 暂存准备公开的文件后，运行 `python3 tools/verify-public.py` 检查暂存内容。检查通过后提交并推送 `main`，确认对应提交的 `Validate` 工作流通过。
4. 运行 `python3 tools/build-release.py`。它只从当前 Git 提交生成 `build/wps-classroom-fonts-v<版本>.zip` 和 `.zip.sha256`，要求已跟踪文件没有未提交修改。
5. 创建对应 `v<版本>` 标签的 Release 草稿，目标选用刚才检查通过的提交。填写更新说明，上传 ZIP 和 SHA-256 文件，确认附件完整后再发布，并将稳定版本设为 Latest。
6. 从公开下载地址重新下载两个附件，校验 ZIP 的 SHA-256，确认标签指向正确提交。保留旧版 Release，方便需要时回退。

不要把整个本地目录手动压缩后上传。公开发布包只附带 9 个 OFL 字体；本地扩展字体、个人日志、缓存和仓库转移包不属于发布附件。

## v1.1.0 更新说明

可直接使用 [v1.1.0 发布说明](releases/v1.1.0.md)。该版本增加独立的 `lesson` 课件补充组，完整本地配置从 58 个字体文件扩展到 65 个。NEU-BZ-S92 尚未取得完整字体文件，必须在发布说明中保留待补提示。

## 本地 Git 备注

使用维护者配置的 Git 提交身份。Git 提交会保留作者姓名和邮箱；不要把个人路径、日志或凭据写进文档及发布说明。

## English publication notes

Pushing `main` does not update release downloads. Update the version and changelog, audit the intended public files, commit, push, and wait for `Validate` to pass for that exact commit. Run `python3 tools/build-release.py`, create a draft release targeting the verified commit, and attach the generated ZIP and SHA-256 file. Publish it as the latest stable release after checking the assets, then download the public assets again and verify their checksum. Keep previous releases available.

Public releases contain only the nine OFL-licensed STIX Two fonts and the helper. The 65-file profile supports locally supplied extensions; those binaries and runtime logs must remain outside public releases. NEU-BZ-S92 remains unavailable in v1.1.0.
