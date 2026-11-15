---
name: "wechat-draft-porter"
display_name: "公众号草稿搬运工"
display_name_en: "WeChat Draft Porter"
description: "把 markdown 或行内样式 HTML 文章送进微信公众号草稿箱，只写草稿、绝不发布。当用户说「投草稿」「发到草稿箱」「把这篇文章传到公众号后台」「公众号排版稿入库」时使用。"
description_zh: "把本地 HTML 或 Markdown 文章写入微信公众号草稿箱，自动上传正文图片与封面。使用前需自备公众号 AppID 与 AppSecret，并把本机出口 IP 加入公众号后台的 IP 白名单。本技能只创建草稿，是否发布始终由作者本人在公众号后台点击确认。"
description_en: "Writes a local HTML or Markdown article into the WeChat Official Account draft box and uploads inline images and the cover automatically. You need your own AppID and AppSecret, and your egress IP must be whitelisted in the WeChat console. It only creates drafts; publishing is always confirmed manually."
version: "0.1.1"
tags:
  - wechat
  - official-account
  - publishing
  - draft
  - mcp
author: "wangyuancun"
license: "MIT"
examples_zh:
  - "帮我把 ~/Desktop/article.html 投到公众号草稿箱，标题用「我的标题」"
  - "先跑一次体检，看本机出口 IP 和草稿权限是否正常"
  - "更新已经投过的那篇草稿，不要新建一条"
examples_en:
  - "Push ~/Desktop/article.html to my WeChat Official Account draft box with the title 'My Post'"
  - "Run a health check to verify the egress IP and draft permission"
  - "Update the existing draft with the same title instead of creating a new one"
---

# 公众号草稿搬运工 (WeChat Draft Porter)

判定何时调用，以及参数怎么传。

实现不在本目录，在 [mcp 仓库](https://github.com/wangyuancun/mcp) 的 `wechat-mp/` 子目录。本目录只是一个薄壳，避免两处代码漂移。

## 何时调用

- ✅ 用户说「把这篇文章投到草稿箱」「发到公众号后台」「排版稿入库」
- ✅ 需要确认某篇是否已投过（工具 `list_drafts`）
- ✅ 改稿后不想堆出多条（工具 `draft_push` 带 `update_existing: true`）
- ❌ 用户要求发布、群发、定时发表 —— 个人主体账号没有发布接口权限，最后一步必须人工点发表

## 前置条件

服务需已安装并完成配置：

```bash
git clone https://github.com/wangyuancun/mcp.git
cd mcp/wechat-mp && cp config.example.json config.json && chmod 600 config.json
python3 -m wxmp.api --check     # 必须看到 ✓ draft/count
```

出口 IP 需已在微信开发者平台的 API IP 白名单中（一行一个 IP，保存需管理员扫码）。

## 调用方式

MCP 工具 `draft_push`，参数：

| 参数 | 必填 | 说明 |
|---|---|---|
| `file` | 是 | html 或 md 文件绝对路径 |
| `title` | 否 | ≤32 字，超长直接报错；不填取 `<h1>` 或文件名 |
| `cover` | 否 | 封面路径，建议 2.35:1；不填读配置 |
| `author` | 否 | ≤16 字 |
| `digest` | 否 | ≤120 字 |
| `update_existing` | 否 | 默认 `false`；`true` 时按标题查重并原地更新 |

不用 MCP 时可直接跑 CLI：

```bash
cd /path/to/mcp/wechat-mp
python3 -m wxmp.api --html article.html --title "标题" --cover cover.jpg
```

## 约束

- 只写草稿，**绝不调用 `freepublish/*`**
- 标题 ≤ 32 字，图片需本地文件，封面走永久素材
- 凭证只从配置文件或环境变量读，不打印、不入库
