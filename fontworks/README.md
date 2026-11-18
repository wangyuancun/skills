# FontWorks · 字体工坊

中文优先的字体工作室。用一句话描述、手写照片或参考图，生成**真正可安装**的字体家族（TTF / OTF / 可变字体 / WOFF2），带字距、字偶距、OpenType 特性和 Studio 试字页面。

基于 [Punchcutter](https://github.com/byrishi/punchcutter)（Rishi Shah，MIT）二次开发。详见 [NOTICE.md](NOTICE.md)。

## 特点

- **离线**：无任何网络上报、无远程下载。所有数据留在本地。
- **中文**：remix 路线可把内置或本地的 OFL 中文字体改造成新字体（内置 Noto Sans CJK SC 的 3000 常用字子集，3,514 字符；全量汉字可另挂本地字体）。
- **真字体文件**：不是图片里的字，是能装进系统、能打字的字体。

## 安装

需要 Python 3.10+。以下命令都在本文件所在目录（skill 根目录）执行。

```bash
pip install -r scripts/requirements.txt
# 或者：bash setup.sh
```

macOS 若 `cairosvg` 报找不到 cairo：

```bash
export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH"
```

`setup.sh` 会自动探测 Homebrew 并生成 `cairo-env.sh`，执行 `source cairo-env.sh` 即可。

## 使用

```bash
python scripts/fontworks.py menu                    # 交互菜单
python scripts/fontworks.py new "字名" --preset humanist --weights 300,400,700
python scripts/fontworks.py build 字名.json --draft  # 快速预览
python scripts/fontworks.py build 字名.json          # 完整发布
```

中文字体（走 remix 路线），`base` 可以直接用内置字体：

```json
{
  "family": "我的字体",
  "mode": "remix",
  "base": "NotoSansSC-VF.ttf",
  "weights": [400]
}
```

```bash
python scripts/fontworks.py build 我的字体.json --draft
```

内置的 `NotoSansSC-VF.ttf` 是 Noto Sans CJK SC 的 **3000 常用字子集**（3,514 字符 / 3,561 字形，wght 100–900），随包体积受限只保留高频汉字；生僻字、日文假名等超出子集时，请把完整的本地 OFL `.ttf` 路径填进 `base`，行为完全一致。

`bases` 会列出已知的 OFL base，并标出哪些随包内置；未内置的字体需要提供本地 `.ttf` 路径。完整操作手册见 [SKILL.md](SKILL.md)。

## 许可

- 代码：MIT（见 `LICENSE-MIT`，保留 Rishi Shah 版权）
- 随包字体：SIL OFL 1.1（见 `OFL.txt`）
- 你生成的字体：参数化路线归你；基于 OFL base 的衍生字体须继续 OFL、保留原版权声明并使用新名称，不能单独售卖字体文件

## 隐私

本版本不收集任何数据，不联网。无遥测。

## 已知限制

- 绘制路线仅覆盖拉丁字符；中文等其他文字走 remix 路线。
- 内置中文字体只含 3000 常用字（3,514 字符）；生僻字或日文假名需要换用完整的本地 OFL 字体。
- 若挂载完整中文字体（65,535 字形），多字重/全可变同时构建会占满内存，建议单字重 + `--draft`。
- 超大字体可能因 Cairo 限制跳过 PNG 预览，SVG 预览仍会生成。
