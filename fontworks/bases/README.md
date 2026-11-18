# 内置 OFL 基础字体

## NotoSansSC-VF.ttf

- **来源**：Noto Sans CJK SC（Adobe，`https://github.com/notofonts/noto-cjk`），原文件 65,535 字形 / 44,810 字符，Version 2.004。
- **本包内是子集**：按字频取 GB2312 一级汉字（3,755 个常用字）中的前 3,000 字，另加 Basic Latin、Latin-1、常用标点、CJK 标点与全角形式。结果 3,514 字符 / 3,561 字形，保留 `wght` 100–900 可变轴。
- **字符表**：`subset-chars.txt`（精确列出子集包含的 3,000 个汉字，便于核对覆盖面）。
- **为什么子集**：分发平台对技能包有体积上限。需要全量汉字时，把完整 Noto Sans CJK SC（或其他 OFL 可变字体）的本地路径填进 `base`，功能不受影响。

### 重建方式

```bash
pyftsubset NotoSansSC-VF-full.ttf \
  --text-file=subset-chars.txt \
  --unicodes="U+0020-007E,U+00A0-00FF,U+2000-206F,U+3000-303F,U+FF00-FFEF" \
  --layout-features="kern,ccmp,mark,mkmk,vert,vrt2,palt" \
  --name-IDs='*' --name-languages='*' \
  --drop-tables+=DSIG --no-hinting \
  --output-file=NotoSansSC-VF.ttf
```

生成后需再把 name ID 1/4 改为 `Noto Sans CJK SC Subset`、name ID 6 改为 `NotoSansCJKscSubset`、name ID 3 改为 `2.004;FONTWORKS;NotoSansCJKscSubset`；name ID 0（Adobe 版权 + RFN `'Source'`）、7、13、14 必须原样保留。

## 许可

上述字体为 SIL Open Font License 1.1，本目录的 `OFL.txt` 是随字体分发的许可全文。子集属于 OFL 意义上的 Modified Version：继续以 OFL 分发、保留原版权声明、不使用保留字体名 `'Source'`。详见包根目录 `NOTICE.md`。
