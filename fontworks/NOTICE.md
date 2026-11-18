# FontWorks — 来源与许可声明

FontWorks 是一个中文优先的字体生成 Skill，基于 Punchcutter 二次开发。

## 来源

- **上游项目**：Punchcutter，作者 Rishi Shah (https://github.com/byrishi/punchcutter)
- **上游代码许可**：MIT，见 `LICENSE-MIT`
- **上游版权声明**：Copyright (c) 2026 Rishi Shah（原样保留，未修改）

## 本项目的修改

1. **品牌与命名**：项目名、CLI 命令、SKILL/README 描述、agent 显示名、UI 文案、配色与站点图标全部替换为 FontWorks；不再随包分发上游 logo 文件。
2. **遥测移除**：上游默认向美国 PostHog 上报匿名使用数据。本版本彻底移除所有网络上报，`telemetry.py` 改为 no-op，**无任何数据离开用户设备**。
3. **网络访问移除**：上游 remix 路线会从境外 GitHub 下载字体、MCP server 接受任意远程 URL。本版本改为仅支持本地/内置字体，MCP 只接受本地路径。
4. **版本与元数据**：version 改为 1.0.0，plugin/package 配置更新。

## 字体资产的许可

- 随包字体（Burin Grotesk、Pomelo Round 等 TTF）版权归 Punchcutter，采用 **SIL Open Font License 1.1**，全文见 `OFL.txt`。这些字体**没有声明 Reserved Font Name**（经字体元数据实测：name ID 0 = `Copyright 2026 Punchcutter.`，无 `with Reserved Font Name` 字样）。
- 使用 OFL 字体作为 base 衍生的字体，**必须继续以 OFL 发布**、保留版权声明、不得单独售卖字体本身。用字体排版的作品（图片、文档、Logo）不受 OFL 约束。
- **内置中文字体：Noto Sans CJK SC 的 3000 常用字子集**（文件 `bases/NotoSansSC-VF.ttf`，name ID 1/4 = `Noto Sans CJK SC Subset`）。版权归 Adobe，`© 2014-2021 Adobe`，SIL OFL 1.1，其版权声明含 **Reserved Font Name 'Source'**（经字体元数据实测 name ID 0）。
  - **子集化即 OFL 意义上的修改**。OFL 定义："Modified Version" 指通过增加、删除或替换原版任何组成部分（部分或全部）产生的衍生品。删除字形、cmap 与部分 name 记录属于"删除"，因此本子集是 Modified Version，按 OFL §5 整体继续以 OFL 分发。
  - **保留字体名**：RFN 只有 `'Source'`；子集把 name ID 1/4 改成 `Noto Sans CJK SC Subset`，不含 `Source`，符合 OFL §3。同时避免与用户机器上完整安装的 Noto Sans CJK SC 重名。
  - **声明与许可全文随字体保留**：子集逐字保留 name ID 0（Adobe 版权与 RFN 声明）、name ID 7（Source 商标说明）、name ID 13/14（OFL 声明与地址），并在 `bases/OFL.txt` 放置 OFL 全文，随包分发。
  - 用户以此子集为 base 衍生新字体时，**同样不得在字体名中使用 'Source'**，并须保留 Adobe 版权声明、继续以 OFL 发布；`remix` 已内置该校验（命中保留名直接报错）。

## 第三方素材

- `mockups/*.jpg`（8 张场景照片）随上游 Punchcutter 仓库以 MIT 发布，上游未对这些照片单独标注版权或署名。本项目**无法独立验证**其原始来源与授权范围；它们仅用于把字体投影到场景里的预览图，不影响字体文件本身。为控制包体积，本项目将这批照片统一缩放到 720px 宽并重新编码（有损压缩），内容与署名状态未变。若后续能替换为自有或生成素材，应替换并删除本条说明。
- 包内其余图像（`assets/fontworks.png`、`assets/fontworks-small.svg`）由本项目用自身品牌图形生成。

## 双重许可共存

代码（MIT）与字体（OFL）是聚合关系，互不传染：

- `LICENSE-MIT` — 代码，保留 Rishi Shah 版权
- `OFL.txt` — 字体，SIL OFL 1.1 全文；文件头已按随包字体填写 Punchcutter（无 RFN）与 Adobe Noto（RFN `'Source'`）的版权行

## 免责

本软件按"原样"提供，不提供任何明示或暗示担保。详见 LICENSE-MIT 与 OFL.txt 的免责条款。
