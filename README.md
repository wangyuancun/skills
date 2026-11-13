# My Skills Collection

这里收集了我开发的一系列 AI Agent Skills，旨在提升工作效率和创造力。

## 📦 Skills 列表

| Skill 名称 | 描述 | 状态 |
| :--- | :--- | :--- |
| **[wechat-illustrator](./wechat-illustrator/)** | 🎨 微信公众号文章配图神器。自动提取痛点、生成手绘风格插图与封面。 | ✅ 已发布 |
| **[novel-analyzer](./novel-analyzer/)** | 📚 热门小说分析师。分析网文趋势并提供创作灵感。 | ✅ 已发布 |
| **[wechat-draft-porter](./wechat-draft-porter/)** | 📤 公众号草稿搬运工。只写草稿不发布；实现在 [mcp 仓库](https://github.com/wangyuancun/mcp) 的 `wechat-mp/` 子目录，本目录只放技能定义。 | ✅ 已发布 |

## 🚀 如何使用

你可以通过 `npx skills add` 命令直接安装这些 Skill：

```bash
# 安装 wechat-illustrator (公众号配图)
npx skills add Christian-wyc/skills/wechat-illustrator

# 安装 novel-analyzer (小说分析)
npx skills add Christian-wyc/skills/novel-analyzer

# 安装 wechat-draft-porter (公众号草稿搬运工)
npx skills add wangyuancun/skills/wechat-draft-porter
```

部分技能自带可执行代码（如 `wechat-draft-porter` 依赖 mcp 合集仓库里的服务），安装后需按该技能 README 的指引把服务本体拉下来并配置凭证。例如：

```bash
git clone https://github.com/wangyuancun/mcp.git
cd mcp/wechat-mp && cp config.example.json config.json
python3 -m wxmp.api --check
```

## 📁 合集约定

本仓库采用「一个技能一个子目录」的合集结构，新增技能请遵守以下约定：

1. **每个技能一个顶层子目录**，目录名用小写连字符（如 `wechat-draft-porter`），与技能 `name` 保持一致。
2. **目录内必须有 `SKILL.md`**，带 YAML frontmatter：`name`、`description`、`version`、`tags`、`author`、`license`。`description` 要写清「什么时候该调用」。
3. **目录内必须有 `README.md`**，面向使用者：这是什么、解决什么问题、怎么装、怎么跑、已知限制。
4. **不得提交任何凭证**：AppSecret、token、Cookie、真实 AppID、真实 IP、草稿 ID、私有域名一律不入库；示例配置只用占位值（`wx0000000000000000`）。各目录自带 `.gitignore` 排除 `config.json`、`.env`。
5. **代码归属唯一**：能自包含就自包含；需要独立部署的（如 MCP 服务）放独立仓库，技能目录只留 `SKILL.md` + `README.md` 薄壳，并在 README 里写清实现仓库地址与安装方式。**同一份源码不得在两个仓库各存一份**，避免漂移。
6. **默认最小依赖**：优先标准库；需要第三方依赖时在目录内提供 `requirements.txt` 或 `pyproject.toml`。
7. **根目录 README 的表格要同步更新**，新增技能加一行链接与一句话说明。

## 🤝 贡献与反馈

欢迎提交 Issue 或 PR 来改进这些 Skills！
