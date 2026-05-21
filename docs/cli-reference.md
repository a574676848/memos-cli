# 命令参考

本文按资源类型列出 memos-cli 的主要命令。全局参数必须放在子命令前。

## 全局参数

```bash
memos --version
memos -j memo list --limit 5
memos -f csv user list
memos -o memos.json -j memo list --limit 100
memos --context production auth status
```

常用全局参数：

| 参数 | 说明 |
| --- | --- |
| `--config` | 指定配置文件路径 |
| `--context` | 指定 context |
| `-f, --format` | 输出格式：`table`、`json`、`plain`、`csv` |
| `-j, --json` | 等价于 `--format json` |
| `-o, --output-file` | 写入文件 |
| `--timeout` | 请求超时时间 |
| `-v, --verbose` | 输出调试请求信息 |

## 配置与授权

```bash
memos config init --server http://127.0.0.1:5230 --token 'memos_pat_xxx'
memos config show
memos config contexts
memos config set-context production
memos auth status
```

## Memo

```bash
memos new "from shortcut"
memos memo create "hello"
echo "from stdin" | memos new --stdin
memos ls --limit 10
memos memo get abc123
memos memo update abc123 --content "updated" --visibility PRIVATE --pinned true
memos memo delete abc123 --force
memos rm abc123 --force
memos memo search cloudflare
memos edit abc123
```

评论、关系与反应：

```bash
memos memo comment abc123 "follow-up"
memos memo comments abc123
memos memo link abc123 def456 --type REFERENCE
memos memo relations abc123
memos memo react abc123 +1
memos memo reactions abc123
```

## 附件

Memos `v0.28.x` 使用 `attachments` 端点。`resource` 命令作为兼容别名保留，内部同样调用 `/api/v1/attachments`。

```bash
memos attachment upload ./image.png
memos attachment list
memos attachment get attachments/abc123
memos attachment update abc123 --filename cover.png
memos attachment delete abc123 --force
memos attachment batch-delete abc123 def456 --force
memos memo attach memo123 attachments/abc123
```

## 分享

```bash
memos share create memo123 --expire-in-days 7
memos share list memo123
memos share revoke memos/memo123/shares/share456 --force
memos share get share-token
```

`memos share create` 会在返回结果中额外包含 `shareUrl` 字段，按当前激活 context 的 `server`
配置自动拼接成可直接打开的分享链接，例如：

```text
http://your-memos-host/memos/shares/<token>
```

不会写死域名。

## 用户与自动化资源

```bash
memos user list
memos user get root
memos user create alice --password 'change-me'
memos user update alice --display-name Alice
memos user stats root
memos user stats-all

memos pat list --user root
memos pat create --user root --description "automation"
memos pat delete users/root/personalAccessTokens/token-id --force

memos webhook list --user root
memos webhook create https://example.com/hook --user root
memos webhook update users/root/webhooks/hook-id --display-name "Deploy"
memos webhook delete users/root/webhooks/hook-id --force

memos shortcut create "Bugs" --filter 'content.contains("bug")'
memos shortcut list --user root
```

## 原始 API

尚未封装成一等命令的官方端点可以通过 `api` 访问：

```bash
memos api GET /api/v1/users/root/settings
memos api PATCH /api/v1/users/root/settings/GENERAL \
  --data '{"generalSetting":{"locale":"zh","memoVisibility":"PRIVATE"}}'
memos api POST /api/v1/example --data-file body.json
```

查询参数：

```bash
memos api GET /api/v1/memos --param pageSize=10 --param filter='content.contains("ops")'
```

## 升级

```bash
memos upgrade
memos upgrade --check
memos upgrade --source "."
memos -j upgrade --dry-run
```
