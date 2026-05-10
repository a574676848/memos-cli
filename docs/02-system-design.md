# Memos CLI — 系统设计文档

> **版本**: v1.0  
> **日期**: 2026-05-10  
> **作者**: AI 技术合伙人  
> **状态**: ✅ 已确认  

---

## 1. 架构概览

### 1.1 系统架构图

```
                          memos-cli 架构
                          
   ┌─────────────────────────────────────────────────────┐
   │                    用户入口 (main.go)                 │
   └──────────────────────┬──────────────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────────────┐
   │              Cobra Root Command                      │
   │    ┌──────────────────────────────────────────┐      │
   │    │  Sub-Commands: memo / config / user /     │      │
   │    │                share / resource            │      │
   │    └──────────────────────────────────────────┘      │
   └──────────────────────┬──────────────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────────────┐
   │                中间件层 (Middleware)                   │
   │  ┌────────────┐ ┌────────────┐ ┌────────────────┐   │
   │  │ Auth Token │ │ HTTP Retry │ │ Rate Limiter   │   │
   │  │ Injection  │ │ + Timeout  │ │ (可选)          │   │
   │  └────────────┘ └────────────┘ └────────────────┘   │
   └──────────────────────┬──────────────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────────────┐
   │          API Client Layer (resty / http.Client)      │
   │  ┌──────────────────────────────────────────────┐   │
   │  │  RestHTTP  →  GET /api/v1/memos               │   │
   │  │             →  POST /api/v1/memos              │   │
   │  │             →  PATCH /api/v1/{name=memos/*}    │   │
   │  │             →  DELETE /api/v1/{name=memos/*}   │   │
   │  └──────────────────────────────────────────────┘   │
   └──────────────────────┬──────────────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────────────┐
   │              输出格式化层 (Renderer)                   │
   │  ┌────────────┐ ┌────────────┐ ┌────────────────┐   │
   │  │ JSON       │ │ Table      │ │ Plain Text     │   │
   │  │ (AI Agent) │ │ (人类用户) │ │ (管道友好)     │   │
   │  └────────────┘ └────────────┘ └────────────────┘   │
   └─────────────────────────────────────────────────────┘
```

---

## 2. 目录结构

```
memos-cli/
├── cmd/
│   └── memos/
│       └── main.go                  # 入口，初始化 root command
├── internal/
│   ├── cmd/                         # Cobra 子命令定义
│   │   ├── root.go                  # 根命令 + 全局 flags
│   │   ├── config.go                # memos config 子命令
│   │   ├── auth.go                  # memos auth 子命令
│   │   ├── memo.go                  # memos memo 子命令 (CRUD)
│   │   ├── resource.go              # memos resource 子命令
│   │   ├── share.go                 # memos share 子命令
│   │   ├── user.go                  # memos user 子命令
│   │   └── shortcuts.go             # memos new / ls / rm / edit 快捷命令
│   ├── api/                         # API 客户端封装
│   │   ├── client.go                # RestHTTP 基础客户端
│   │   ├── memo.go                  # Memo Service 封装
│   │   ├── resource.go              # Resource Service 封装
│   │   ├── share.go                 # Share Service 封装
│   │   └── user.go                  # User Service 封装
│   ├── config/                      # 配置管理
│   │   ├── config.go                # Viper 封装，~/.memos-cli.yaml
│   │   └── types.go                 # 配置结构体定义
│   ├── renderer/                    # 输出格式化
│   │   ├── renderer.go              # Renderer 接口
│   │   ├── json.go                  # JSON 输出
│   │   ├── table.go                 # ASCII 表格输出
│   │   └── plain.go                 # 纯文本输出
│   └── errors/                      # 统一错误处理
│       └── errors.go                # 错误类型 + 退出码映射
├── proto/                           # 可选：proto 类型定义（自动生成）
│   └── api/v1/                      # 从 memos 官方 proto 复制
├── docs/                            # 项目文档
│   ├── 01-requirements.md
│   ├── 02-system-design.md
│   └── 03-task-plan.md
├── .goreleaser.yml                  # 多平台构建配置
├── Makefile
├── go.mod
└── README.md
```

---

## 3. 配置系统

### 3.1 配置文件位置

| 环境 | 路径 |
|------|------|
| macOS | `~/Library/Application Support/memos-cli/config.yaml` |
| Linux | `~/.config/memos-cli/config.yaml` |
| Windows | `%APPDATA%\memos-cli\config.yaml` |
| 覆盖 | `$MEMOSCLI_CONFIG` 环境变量 |

### 3.2 配置文件格式

```yaml
# ~/.memos-cli.yaml
version: "1"
default_context: production

contexts:
  production:
    server: "http://192.168.5.251:5230"
    token: "memos_pat_ges4qdncjVPUBqxgI5y7XLUX4Y9tYTpe"
    username: "root"

  staging:
    server: "https://memos-staging.example.com"
    token: "memos_pat_xxxx"
    username: "admin"
```

### 3.3 环境变量覆盖

| 变量 | 说明 |
|------|------|
| `MEMOS_SERVER` | API 地址，优先级高于配置文件 |
| `MEMOS_TOKEN` | PAT Token，优先级高于配置文件 |
| `MEMOS_FORMAT` | 默认输出格式：`json` / `table` / `plain` |
| `MEMOS_NO_COLOR` | 禁用颜色输出 |

---

## 4. API 客户端层

### 4.1 基础客户端结构

```go
// internal/api/client.go

type Client struct {
    base   *resty.Client   // resty HTTP client
    server string          // 服务地址
    token  string          // PAT token
}
```

### 4.2 服务封装（对应 Proto 定义）

```go
// Memo 服务封装
type MemoService struct {
    client *Client
}

// 对应 Proto: MemoService.CreateMemo
func (s *MemoService) Create(ctx context.Context, memo *Memo) (*Memo, error)

// 对应 Proto: MemoService.ListMemos
func (s *MemoService) List(ctx context.Context, req *ListMemosRequest) (*ListMemosResponse, error)

// 对应 Proto: MemoService.GetMemo
func (s *MemoService) Get(ctx context.Context, name string) (*Memo, error)

// 对应 Proto: MemoService.UpdateMemo
func (s *MemoService) Update(ctx context.Context, memo *Memo, updateMask []string) (*Memo, error)

// 对应 Proto: MemoService.DeleteMemo
func (s *MemoService) Delete(ctx context.Context, name string, force bool) error

// 对应 Proto: MemoService.CreateMemoComment
func (s *MemoService) CreateComment(ctx context.Context, name string, comment *Memo) (*Memo, error)

// 对应 Proto: MemoService.ListMemoComments
func (s *MemoService) ListComments(ctx context.Context, name string) ([]*Memo, error)

// 对应 Proto: MemoService.UpsertMemoReaction
func (s *MemoService) UpsertReaction(ctx context.Context, name string, reaction *Reaction) (*Reaction, error)

// 对应 Proto: MemoService.CreateMemoShare
func (s *MemoService) CreateShare(ctx context.Context, name string, share *MemoShare) (*MemoShare, error)

// 对应 Proto: MemoService.DeleteMemoShare
func (s *MemoService) DeleteShare(ctx context.Context, name string) error
```

### 4.3 REST 端点映射表

完整的 API 端点到方法的映射（基于 memos v0.28.0 proto 定义）：

| 模块 | Proto RPC | HTTP 方法 | 端点 |
|------|-----------|----------|------|
| **Memo** | CreateMemo | `POST` | `/api/v1/memos` |
| | ListMemos | `GET` | `/api/v1/memos` |
| | GetMemo | `GET` | `/api/v1/{name=memos/*}` |
| | UpdateMemo | `PATCH` | `/api/v1/{memo.name=memos/*}` |
| | DeleteMemo | `DELETE` | `/api/v1/{name=memos/*}` |
| | SetMemoAttachments | `PATCH` | `/api/v1/{name=memos/*}/attachments` |
| | ListMemoAttachments | `GET` | `/api/v1/{name=memos/*}/attachments` |
| | SetMemoRelations | `PATCH` | `/api/v1/{name=memos/*}/relations` |
| | ListMemoRelations | `GET` | `/api/v1/{name=memos/*}/relations` |
| | CreateMemoComment | `POST` | `/api/v1/{name=memos/*}/comments` |
| | ListMemoComments | `GET` | `/api/v1/{name=memos/*}/comments` |
| | UpsertMemoReaction | `POST` | `/api/v1/{name=memos/*}/reactions` |
| | ListMemoReactions | `GET` | `/api/v1/{name=memos/*}/reactions` |
| | DeleteMemoReaction | `DELETE` | `/api/v1/{name=memos/*/reactions/*}` |
| | CreateMemoShare | `POST` | `/api/v1/{parent=memos/*}/shares` |
| | ListMemoShares | `GET` | `/api/v1/{parent=memos/*}/shares` |
| | DeleteMemoShare | `DELETE` | `/api/v1/{name=memos/*/shares/*}` |
| | GetMemoByShare | `GET` | `/api/v1/shares/{share_id}` |
| | GetLinkMetadata | `GET` | `/api/v1/memos/-/linkMetadata` |
| | BatchGetLinkMetadata | `POST` | `/api/v1/memos/-/linkMetadata:batchGet` |
| **User** | ListUsers | `GET` | `/api/v1/users` |
| | GetUser | `GET` | `/api/v1/{name=users/*}` |
| | CreateUser | `POST` | `/api/v1/users` |
| | UpdateUser | `PATCH` | `/api/v1/{user.name=users/*}` |
| | DeleteUser | `DELETE` | `/api/v1/{name=users/*}` |
| | GetUserStats | `GET` | `/api/v1/{name=users/*}:getStats` |
| | ListAllUserStats | `GET` | `/api/v1/users:stats` |
| | GetUserSetting | `GET` | `/api/v1/{name=users/*/settings/*}` |
| | UpdateUserSetting | `PATCH` | `/api/v1/{setting.name=users/*/settings/*}` |
| | ListPersonalAccessTokens | `GET` | `/api/v1/{parent=users/*}/personalAccessTokens` |
| | CreatePersonalAccessToken | `POST` | `/api/v1/{parent=users/*}/personalAccessTokens` |
| | DeletePersonalAccessToken | `DELETE` | `/api/v1/{name=users/*/personalAccessTokens/*}` |
| | ListUserWebhooks | `GET` | `/api/v1/{parent=users/*}/webhooks` |
| | CreateUserWebhook | `POST` | `/api/v1/{parent=users/*}/webhooks` |
| | UpdateUserWebhook | `PATCH` | `/api/v1/{webhook.name=users/*/webhooks/*}` |
| | DeleteUserWebhook | `DELETE` | `/api/v1/{name=users/*/webhooks/*}` |

---

## 5. 认证机制

### 5.1 认证流程

```
┌──────────────────────────────────────────────────┐
│  memos auth login                                │
│                                                  │
│  1. 提示输入 Server URL                          │
│     > http://192.168.5.251:5230                  │
│                                                  │
│  2. 提示输入 PAT Token                           │
│     > memos_pat_xxxx                             │
│                                                  │
│  3. 调用 GET /api/v1/users/root 验证 Token       │
│     - 成功 → 写入 ~/.memos-cli.yaml              │
│     - 失败 → 提示 Token 无效                     │
│                                                  │
│  输出: ✅ Logged in as root@production            │
└──────────────────────────────────────────────────┘
```

### 5.2 认证头格式

```http
Authorization: Bearer memos_pat_ges4qdncjVPUBqxgI5y7XLUX4Y9tYTpe
```

---

## 6. 输出渲染系统

### 6.1 Renderer 接口

```go
type Renderer interface {
    Render(w io.Writer, data interface{}) error
}
```

### 6.2 三种渲染模式对比

| 模式 | 用途 | 示例 |
|------|------|------|
| `table` | 人类阅读 | 带对齐列的 ASCII 表格 |
| `json` | AI Agent | 原始 JSON，可被 jq 解析 |
| `plain` | 管道处理 | 简单键值对 |

### 6.3 表格输出示例

```
  ID     | Content              | Visibility | Created
─────────┼──────────────────────┼────────────┼────────────────────
  abc123 | 修复了 payment 模块  | PRIVATE    | 2026-05-10 14:21
  def456 | server metrics log   | PRIVATE    | 2026-05-09 01:48
  ghi789 | cloudflare dns 配置  | PRIVATE    | 2026-05-08 01:36
```

### 6.4 JSON 输出示例

```json
{
  "memos": [
    {
      "name": "memos/abc123",
      "content": "修复了 payment 模块",
      "visibility": "PRIVATE",
      "createTime": "2026-05-10T06:21:03Z"
    }
  ],
  "nextPageToken": "..."
}
```

---

## 7. 错误处理系统

### 7.1 错误分类与退出码

| 退出码 | 含义 | 示例 |
|--------|------|------|
| `0` | 成功 | 正常执行 |
| `1` | 业务错误 | 资源不存在、Token 无效 |
| `2` | 网络错误 | 连接超时、DNS 解析失败 |
| `3` | 参数错误 | 必需参数缺失 |
| `4` | 配置错误 | 未初始化配置 |

### 7.2 错误消息格式

```
Error: memo not found
  Code: 5 (NOT_FOUND)
  Hint: check the memo ID with 'memos memo list'
```

---

## 8. 命令层次设计

### 8.1 完整命令树

```
memos
├── config
│   ├── init                      # 初始化配置
│   ├── show                      # 显示当前配置
│   └── set-context               # 切换上下文
├── auth
│   └── status                    # 验证认证状态
├── memo
│   ├── create [CONTENT]          # 创建笔记
│   │   --visibility string       #   PRIVATE / PROTECTED / PUBLIC
│   │   --pinned bool             #   是否置顶
│   │   --tag string[]            #   标签（自动解析 #tag）
│   ├── list                      # 列出笔记
│   │   --filter string           #   CEL 表达式过滤
│   │   --state string            #   NORMAL / ARCHIVED
│   │   --order-by string         #   排序字段
│   │   --limit int               #   条数限制 (default: 20)
│   │   --page-token string       #   分页 token
│   ├── get <ID>                  # 查看单条笔记
│   ├── update <ID>               # 修改笔记
│   │   --content string          #   新内容
│   │   --visibility string       #   新可见性
│   │   --pinned bool             #   新置顶状态
│   ├── delete <ID>               # 删除笔记
│   │   --force bool              #   强制删除
│   ├── search <QUERY>            # 全文搜索
│   ├── comment <ID> <CONTENT>    # 评论笔记
│   ├── comments <ID>             # 查看评论列表
│   ├── link <ID> <RELATED_ID>    # 建立引用关系
│   └── relations <ID>            # 查看关系列表
├── resource
│   ├── upload <FILE>             # 上传附件
│   ├── list                      # 列出资源
│   └── delete <ID>               # 删除资源
├── share
│   ├── create <ID>               # 创建分享链接
│   │   --expire-in string        #   过期时间 (e.g. "7d")
│   ├── list <ID>                 # 查看分享链接
│   └── revoke <SHARE_NAME>       # 撤销分享链接
├── user
│   ├── list                      # 列出用户
│   ├── get <USERNAME>            # 查看用户
│   ├── stats [USERNAME]          # 用户统计
│   └── webhooks                  # Webhook 管理
│       ├── list
│       ├── create <URL>
│       └── delete <ID>
│
│   ── 快捷命令 ──
├── new [CONTENT]                 # 快捷创建笔记 (= memo create)
├── ls                            # 快捷列出笔记 (= memo list)
├── rm <ID>                       # 快捷删除笔记 (= memo delete)
└── edit <ID>                     # 编辑器打开笔记 (= $EDITOR)
```

### 8.2 全局 Flags

| Flag | 别名 | 说明 | 默认值 |
|------|------|------|--------|
| `--json` | `-j` | JSON 输出 | false |
| `--format` | `-f` | 输出格式 (table/json/plain/csv) | table |
| `--no-color` | | 禁用颜色 | false |
| `--output-file` | `-o` | 输出到文件 | stdout |
| `--config` | `-c` | 配置文件路径 | 默认路径 |
| `--context` | | 使用指定上下文 | default_context |
| `--verbose` | `-v` | 详细输出 | false |
| `--help` | `-h` | 帮助 | |
| `--version` | | 版本 | |

---

## 9. 构建与分发

### 9.1 GoReleaser 配置

```yaml
# .goreleaser.yml
builds:
  - main: ./cmd/memos
    binary: memos
    ldflags:
      - -s -w -X main.version={{.Version}} -X main.commit={{.ShortCommit}}
    goos:
      - darwin
      - linux
      - windows
    goarch:
      - amd64
      - arm64

brews:
  - repository:
      owner: usememos
      name: homebrew-tap
    homepage: "https://github.com/usememos/memos-cli"
    description: "CLI client for Memos"
```

### 9.2 安装方式

```bash
# Go 安装（开发阶段）
go install github.com/usememos/memos-cli/cmd/memos@latest

# Homebrew（正式发布后）
brew install usememos/tap/memos-cli

# 直接下载二进制（手动）
curl -sL https://github.com/usememos/memos-cli/releases/latest/download/memos_Darwin_arm64.tar.gz | tar xz
mv memos /usr/local/bin/
```

---

## 10. 测试策略

| 层级 | 工具 | 覆盖范围 |
|------|------|---------|
| 单元测试 | `go test` | API Client 层、Renderer 层、Config 层 |
| 集成测试 | `testcontainers-go` | 启动真实 Memos 容器，测试完整命令流 |
| E2E 测试 | `shell` + `memos` 二进制 | 端到端 CLI 使用场景 |
| Mock | `httptest.NewServer` | 模拟 API 响应，无需真实服务 |

---

## 11. 日志与调试

```bash
# 详细模式
memos memo list --verbose

# 调试模式（打印 HTTP 请求详情）
MEMOSCLI_DEBUG=true memos memo list
# 输出:
# [DEBUG] GET http://192.168.5.251:5230/api/v1/memos?pageSize=20
# [DEBUG] Authorization: Bearer memos_pat_...
# [DEBUG] Response: 200 OK (89ms)
```

---

> **下一步**：请确认系统设计内容，随后进入 [任务清单文档 (03-task-plan.md)](./03-task-plan.md)