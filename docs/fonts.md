# 字体清单与分发范围

安装清单共 65 个完整字体文件，没有裁剪字形，也没有专门加入拼音教学字体。

| 分组 | 数量 | 代表字体 | 公开仓库中的文件 |
| --- | ---: | --- | --- |
| open | 9 | STIX Two Math、STIX Two Text 的常规、斜体和不同字重 | 包含全部 9 个，OFL 1.1 |
| math | 48 | STIX Two、Symbol、MT Extra、Cambria Math、Euclid、Fences、Wingdings、Webdings、Arial、Times New Roman、Calibri、Cambria | 仅包含其中的 9 个 STIX Two |
| chinese | 5 | 宋体/新宋体、黑体、楷体、仿宋、微软雅黑/UI | 不附带，按本地授权准备 |
| extra | 5 | Courier New、Tahoma、Calibri Light、EU-BZ、方正书宋_GBK | 不附带，按本地授权准备 |
| lesson | 7 | 等线、方正兰亭中粗黑_GBK、方正兰亭黑_GBK、方正楷体_GBK、方正黑体_GBK、方正仿宋_GBK、方正准圆_GBK | 不附带，按本地授权准备 |

`open` 与 `math` 重叠；全部安装是 48 + 5 + 5 + 7 = 65。中文 TTC 文件含多个字体家族，因此检查中文组会显示 7 个家族。

## 课件补充（lesson）

本组针对课件点名要求的字体，各保留一个完整常规字体文件；未裁剪字符，未批量增加粗体、斜体或拼音字体。7 个文件共 78,020,798 字节（约 74.4 MiB）。原有数学、英语和中文组的文件与校验值保持不变。

| 字体家族 | 原文件名 | 字形数量 |
| --- | --- | ---: |
| 方正兰亭中粗黑_GBK | FZLTZCHK.ttf | 22,026 |
| 方正兰亭黑_GBK | FZLTHK.ttf | 22,026 |
| 方正楷体_GBK | FZKTK.TTF | 22,026 |
| 方正黑体_GBK | FZHTK.TTF | 22,026 |
| 方正仿宋_GBK | FZFSK.TTF | 22,026 |
| 方正准圆_GBK | FZY3K.TTF | 22,024 |
| 等线 / DengXian | Deng.ttf | 29,624 |

**NEU-BZ-S92 仍待补充**：当前没有取得并验证完整字体文件。旧组的 `EU-BZ` 与它不是同名字体，不会修改名称来冒充。待补项记录在 [`pending.tsv`](../manifests/pending.tsv)，不计入可安装文件数量。

```bash
bash install.sh lesson  # 安装已准备好的 7 个文件
bash check.sh lesson    # 同时检查待补项；仍缺失时退出码为 2
bash undo.sh lesson     # 只撤销本组 7 个文件
```

安装成功表示已提供的 7 个字体安装并被系统识别；不表示待补项已经解决。检查时如果当前账号通过其他方式已装有 NEU-BZ-S92，会如实报告已识别；本工具不会撤销该外部字体。

## 为什么没有公开全部字体

拥有电脑上的字体文件，与拥有公开再分发该文件的权利，是两回事。

- STIX Two 随项目分发时保留了字体原始字节及 [完整 OFL 许可证](../licenses/STIX-OFL.txt)。来源为 [STIX Fonts 项目](https://github.com/stipub/stixfonts) 的 [CTAN 分发包](https://ctan.org/pkg/stix2-otf)。
- Windows / Office 常见字体的分发限制见 [Microsoft 字体分发 FAQ](https://learn.microsoft.com/en-us/typography/fonts/font-faq)。本仓库不随附这些字体二进制文件。
- MathType 字体可从 [WIRIS 官方说明](https://docs.wiris.com/en_US/create-and-edit-equations/mathtype-7-ui-basic-usage) 查阅相关来源。可下载不等于可重新打包公开分发；本仓库仅保留安装目标的名称及校验值。
- 方正书宋可查阅 [方正字库字体页](https://www.foundertype.com/index.php/FontInfo/index/id/151)。EU-BZ 等未确认公开再分发许可的文件也不进入 Git。

项目的 MIT 许可证仅覆盖本项目脚本和文档，不改变任何第三方字体的许可证，也不自动授予跨系统使用权。

## 如何导入

使用你有权在目标电脑上使用的文件：

```bash
python3 tools/import-fonts.py /path/to/your-fonts --group math
bash install.sh math
```

也可把原来的完整离线字体包作为来源目录。工具会递归查找字体，按 SHA-256 识别，不依赖原文件名。文件名、分组、预期校验值及保存位置详见 [`catalog.tsv`](../manifests/catalog.tsv)。

发现同名字体但版本不同、内容不同的文件时，不会自动修改清单或替换。更新支持版本应同时审查字体来源、授权、家族名称、文件校验值和回归测试。

导入后的扩展文件被 `.gitignore` 忽略。公开 ZIP 必须用 `tools/build-release.py` 生成，避免把本地完整目录直接压缩后公开上传。
