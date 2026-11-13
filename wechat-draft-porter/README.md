# wechat-draft-porter

微信公众号草稿搬运工技能的**薄壳**：这里只放技能定义，不包含实现代码。

> 真正的实现在 [mcp 仓库](https://github.com/wangyuancun/mcp) 的 **[wechat-mp 子目录](https://github.com/wangyuancun/mcp/tree/main/wechat-mp)**（MCP 服务 + CLI + 投递逻辑）。
> 本目录刻意不放源码，避免两处代码漂移；升级只需更新那一处。

## 这个技能负责什么

它只回答一个问题：**什么时候该调用、参数怎么传**。

- 用户说「把这篇文章投到草稿箱」「发到公众号后台」「排版稿入库」→ 调用
- 用户说「发布/群发/推文上线」→ 不调用。个人主体账号没有发布接口权限，最后一步必须人工点发表
- 改稿后不想堆出多条草稿 → 调用时带 `update_existing`

## 安装（两步）

1. 装服务本体：

```bash
git clone https://github.com/wangyuancun/mcp.git
cd mcp/wechat-mp
cp config.example.json config.json    # 填 appid / appsecret
chmod 600 config.json
python3 -m wxmp.api --check           # 看到 ✓ draft/count 才算通
```

2. 把服务注册进你的 agent 客户端（配置片段见 MCP 仓库的 `mcp_config.example.json`），技能即可生效。

凭证与白名单要求（AppID 在哪拿、IP 白名单怎么加、为什么发布接口用不了）全部见 MCP 仓库的 README，本目录不重复。

## 参数怎么传

调 MCP 工具 `draft_push`：

| 参数 | 必填 | 说明 |
|---|---|---|
| `file` | 是 | html 或 md 文件绝对路径 |
| `title` | 否 | ≤32 字；不填取 `<h1>`，再退到文件名。**超长会直接报错，不会静默截断** |
| `cover` | 否 | 封面图路径，建议 2.35:1；不填读配置 `default_cover` |
| `author` | 否 | ≤16 字；不填读配置 |
| `digest` | 否 | ≤120 字 |
| `update_existing` | 否 | `true` 时按标题查重，命中则原地更新，默认 `false` |

另有 `check`（体检）与 `list_drafts`（列最近草稿标题）两个工具，用于投前确认。

## 边界

- 只写草稿，**绝不调用 `freepublish/*`**
- 正文图片必须是本地文件，服务会自动上传换成微信图床地址
- 动态公网 IP 失效会报 40164，按 `check` 输出的 IP 去白名单补一条
