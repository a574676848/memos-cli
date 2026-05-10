# Memos CLI — 任务清单文档

> **版本**: v1.0  
> **日期**: 2026-05-10  
> **作者**: AI 技术合伙人  
> **状态**: ✅ 已确认  

---

## 总览

本文档将任务按 **阶段（Phase）** 分解，每个任务包含：描述、前置依赖、预估工时、验收标准。

| 阶段 | 内容 | 工时 | 优先级 |
|------|------|------|--------|
| **P0 — 基础骨架** | 项目初始化、配置系统、API Client | 4h |  |
| **P1 — 核心 CRUD** | Memo 创建/列表/查看/更新/删除 | 4h |  |
| **P2 — 快捷命令** | new / ls / rm / edit 等快捷别名 | 2h |  |
| **P3 — 用户与认证** | auth status / user 管理 | 2h |  |
| **P4 — 输出系统** | 多格式输出（表格/JSON/纯文本） | 2h |  |
| **P5 — 资源与分享** | resource、share、comment 管理 | 3h |  |
| **P6 — 生产化** | 构建、发布、文档、测试 | 3h |  |

**总计：约 20 小时（5 工作日）**

---

## 阶段 P0：基础骨架（4 小时）

### Task 1：Go 模块初始化

| 项目 | 内容 |
|------|------|
| **编号** | P0-01 |
| **描述** | 初始化 `go.mod`，设置模块名为 `github.com/usememos/memos-cli` |
| **依赖** | 无 |
| **预估** | 0.5h |
| **产出** | `go.mod`、`go.sum`、`cmd/memos/main.go` |
| **验收** | `go build ./...` 通过 |

```bash
mkdir memos-cli && cd memos-cli
go mod init github.com/usememos/memos-cli
go get github.com/spf13/cobra@latest
go get github.com/spf13/viper@latest
go get github.com/go-resty/resty/v2@latest
```

---

### Task 2：Cobra 根命令与全局 Flags

| 项目 | 内容 |
|------|------|
| **编号** | P0-02 |
| **描述** | 创建 Cobra root command，注册全局 flags |
| **依赖** | P0-01 |
| **预估** | 1h |
| **产出** | `internal/cmd/root.go`、`cmd/memos/main.go` |
| **验收** | `memos --help` 输出完整帮助信息 |

需实现的全局 flags：
```
--json / -j       (bool)
--format / -f     (string: table|json|plain)
--no-color        (bool)
--output-file / -o (string)
--config / -c     (string)
--context         (string)
--verbose / -v    (bool)
--version         (bool)
```

---

### Task 3：配置系统

| 项目 | 内容 |
|------|------|
| **编号** | P0-03 |
| **描述** | 实现 Viper 配置管理，支持 `~/.memos-cli.yaml` 多上下文 |
| **依赖** | P0-01 |
| **预估** | 1h |
| **产出** | `internal/config/config.go`、`internal/config/types.go` |
| **验收** | 能读写配置文件，支持多上下文切换 |

配置结构体定义：
```go
type Config struct {
    Version        string              `yaml:"version"`
    DefaultContext string              `yaml:"default_context"`
    Contexts       map[string]Context  `yaml:"contexts"`
}

type Context struct {
    Server   string `yaml:"server"`
    Token    string `yaml:"token"`
    Username string `yaml:"username"`
}
```

---

### Task 4：API Client 基础层

| 项目 | 内容 |
|------|------|
| **编号** | P0-04 |
| **描述** | 实现 Resty HTTP Client，注入 Auth Header，支持超时和重试 |
| **依赖** | P0-03 |
| **预估** | 1.5h |
| **产出** | `internal/api/client.go` |
| **验收** | `client := NewClient(cfg)` 能创建；`GET /api/v1/users/root` 正确返回 |

核心实现要点：
```go
type Client struct {
    base   *resty.Client
    server string
    token  string
}

func NewClient(cfg *config.Context) *Client {
    rc := resty.New().
        SetBaseURL(cfg.Server).
        SetHeader("Authorization", "Bearer " + cfg.Token).
        SetTimeout(30 * time.Second).
        SetRetryCount(2).
        SetRetryWaitTime(500 * time.Millisecond)

    return &Client{base: rc, server: cfg.Server, token: cfg.Token}
}
```

---

## 阶段 P1：核心 CRUD（4 小时）

### Task 5：Memo 创建命令

| 项目 | 内容 |
|------|------|
| **编号** | P1-01 |
| **描述** | 实现 `memos memo create` 命令 |
| **依赖** | P0-04 |
| **预估** | 1h |
| **产出** | `internal/cmd/memo.go` (create 子命令) |
| **验收** | `memos memo create "hello" --visibility PUBLIC` 创建成功 |

关键实现：
- 支持 `--content`（或第一个位置参数作为内容）
- 支持 `--visibility`（PRIVATE / PROTECTED / PUBLIC）
- 支持 `--pinned`
- 支持从 stdin 读取内容（管道模式）
- 输出创建结果（Memo ID）

---

### Task 6：Memo 列表命令

| 项目 | 内容 |
|------|------|
| **编号** | P1-02 |
| **描述** | 实现 `memos memo list` 命令，支持分页和过滤 |
| **依赖** | P0-04 |
| **预估** | 1h |
| **产出** | `internal/cmd/memo.go` (list 子命令) |
| **验收** | `memos memo list --limit 5` 返回正确列表 |

关键参数：
```bash
memos memo list \
  --limit 20           # 页大小 (default: 20)
  --page-token <token> # 分页游标
  --filter "tag in ['bug']"  # CEL 过滤
  --state NORMAL       # 状态过滤
  --order-by "pinned desc, create_time desc"
```

---

### Task 7：Memo 查看命令

| 项目 | 内容 |
|------|------|
| **编号** | P1-03 |
| **描述** | 实现 `memos memo get <ID>` 命令 |
| **依赖** | P0-04 |
| **预估** | 0.5h |
| **产出** | `internal/cmd/memo.go` (get 子命令) |
| **验收** | `memos memo get abc123` 显示完整 memo 详情 |

---

### Task 8：Memo 更新命令

| 项目 | 内容 |
|------|------|
| **编号** | P1-04 |
| **描述** | 实现 `memos memo update <ID>` 命令 |
| **依赖** | P0-04 |
| **预估** | 0.5h |
| **产出** | `internal/cmd/memo.go` (update 子命令) |
| **验收** | `memos memo update abc123 --content "新内容"` 修改成功 |

关键：使用 `update_mask` 只更新指定字段

---

### Task 9：Memo 删除命令

| 项目 | 内容 |
|------|------|
| **编号** | P1-05 |
| **描述** | 实现 `memos memo delete <ID>` 命令 |
| **依赖** | P0-04 |
| **预估** | 0.5h |
| **产出** | `internal/cmd/memo.go` (delete 子命令) |
| **验收** | `memos memo delete abc123` 删除成功 |

关键实现：
- 默认需确认（`Confirm deletion? [y/N]`）
- `--force` 跳过确认（适合脚本使用）
- `memos memo search` 全文搜索（复用 `--filter`）

---

### Task 10：Memo 搜索命令

| 项目 | 内容 |
|------|------|
| **编号** | P1-06 |
| **描述** | 实现 `memos memo search <QUERY>` 命令，基于服务端 filter |
| **依赖** | P0-04 |
| **预估** | 0.5h |
| **产出** | `internal/cmd/memo.go` (search 子命令) |
| **验收** | `memos memo search "cloudflare"` 返回匹配笔记 |

---

## 阶段 P2：快捷命令（2 小时）

### Task 11：快捷别名命令

| 项目 | 内容 |
|------|------|
| **编号** | P2-01 |
| **描述** | 实现 `memos new` / `memos ls` / `memos rm` 快捷别名 |
| **依赖** | P1-01 至 P1-05 |
| **预估** | 1h |
| **产出** | `internal/cmd/shortcuts.go` |
| **验收** | `memos new "hello"` / `memos ls` / `memos rm abc123` 正常工作 |

```bash
memos new "内容"            # → memos memo create
memos ls                    # → memos memo list
memos rm <id>               # → memos memo delete
```

---

### Task 12：Editor 集成

| 项目 | 内容 |
|------|------|
| **编号** | P2-02 |
| **描述** | 实现 `memos edit <ID>` 命令，调用 `$EDITOR` 打开编辑器 |
| **依赖** | P1-03, P1-04 |
| **预估** | 1h |
| **产出** | `internal/cmd/shortcuts.go` (edit 子命令) |
| **验收** | `memos edit abc123` 打开 Vim/VSCode 编辑，保存后更新笔记 |

实现逻辑：
1. `GET /api/v1/memos/{id}` 获取当前内容
2. 写入临时文件 `/tmp/memos-edit-xxxx.md`
3. 调用 `$EDITOR /tmp/memos-edit-xxxx.md`
4. 读取新内容
5. `PATCH /api/v1/memos/{id}` 更新

---

## 阶段 P3：用户与认证（2 小时）

### Task 13：认证管理命令

| 项目 | 内容 |
|------|------|
| **编号** | P3-01 |
| **描述** | 实现 `memos auth status` 命令 |
| **依赖** | P0-03, P0-04 |
| **预估** | 1h |
| **产出** | `internal/cmd/auth.go` |
| **验收** | `memos auth status` 显示当前认证用户和服务器 |

输出示例：
```
Server:   http://192.168.5.251:5230
User:     root (ADMIN)
Version:  0.28.0
Status:   ✅ Connected
```

---

### Task 14：用户管理命令

| 项目 | 内容 |
|------|------|
| **编号** | P3-02 |
| **描述** | 实现 `memos user list/get/stats` 命令 |
| **依赖** | P0-04 |
| **预估** | 1h |
| **产出** | `internal/cmd/user.go` |
| **验收** | `memos user list` / `memos user stats` 正常输出 |

---

## 阶段 P4：输出系统（2 小时）

### Task 15：多格式 Renderer

| 项目 | 内容 |
|------|------|
| **编号** | P4-01 |
| **描述** | 实现 Table / JSON / Plain 三种渲染器 |
| **依赖** | P0-01 |
| **预估** | 1.5h |
| **产出** | `internal/renderer/` 目录下所有文件 |
| **验收** | `memos list --json` 输出可被 jq 解析；默认输出为表格 |

---

### Task 16：管道与文件输出

| 项目 | 内容 |
|------|------|
| **编号** | P4-02 |
| **描述** | 实现 stdin 读取、stdout 输出控制、文件输出 |
| **依赖** | P0-04, P4-01 |
| **预估** | 0.5h |
| **产出** | 内嵌于 `internal/cmd/memo.go` 和 `internal/renderer/` |
| **验收** | `echo "test" \| memos new` 正常创建 |

---

## 阶段 P5：资源与分享（3 小时）

### Task 17：资源管理命令

| 项目 | 内容 |
|------|------|
| **编号** | P5-01 |
| **描述** | 实现 `memos resource upload/list/delete` 命令 |
| **依赖** | P0-04 |
| **预估** | 1h |
| **产出** | `internal/cmd/resource.go`、`internal/api/resource.go` |
| **验收** | `memos resource upload photo.jpg` 上传成功 |

---

### Task 18：评论命令

| 项目 | 内容 |
|------|------|
| **编号** | P5-02 |
| **描述** | 实现 `memos memo comment/comments` 命令 |
| **依赖** | P0-04 |
| **预估** | 0.5h |
| **产出** | `internal/cmd/memo.go` (comment/comments 子命令) |
| **验收** | `memos memo comment abc123 "nice work"` 添加评论成功 |

---

### Task 19：分享管理命令

| 项目 | 内容 |
|------|------|
| **编号** | P5-03 |
| **描述** | 实现 `memos share create/list/revoke` 命令 |
| **依赖** | P0-04 |
| **预估** | 1h |
| **产出** | `internal/cmd/share.go`、`internal/api/share.go` |
| **验收** | `memos share create abc123` 生成分享链接 |

---

### Task 20：关联关系命令

| 项目 | 内容 |
|------|------|
| **编号** | P5-04 |
| **描述** | 实现 `memos memo link/relations` 命令 |
| **依赖** | P0-04 |
| **预估** | 0.5h |
| **产出** | `internal/cmd/memo.go` (link/relations 子命令) |
| **验收** | `memos memo link abc123 def456` 建立引用关系 |

---

## 阶段 P6：生产化（3 小时）

### Task 21：单元测试

| 项目 | 内容 |
|------|------|
| **编号** | P6-01 |
| **描述** | 编写 API Client 层和 Renderer 层单元测试 |
| **依赖** | 所有 P0-P5 任务 |
| **预估** | 1h |
| **产出** | `*_test.go` 文件 |
| **验收** | `go test ./...` 全部通过 |

---

### Task 22：集成测试

| 项目 | 内容 |
|------|------|
| **编号** | P6-02 |
| **描述** | 编写端到端集成测试（连接真实 Memos 实例） |
| **依赖** | P0-P5 |
| **预估** | 1h |
| **产出** | `tests/integration/` 目录 |
| **验收** | 完整生命周期测试通过（创建 → 获取 → 更新 → 删除） |

---

### Task 23：GoReleaser 构建配置

| 项目 | 内容 |
|------|------|
| **编号** | P6-03 |
| **描述** | 配置 GoReleaser，实现多平台二进制构建 |
| **依赖** | 所有任务 |
| **预估** | 0.5h |
| **产出** | `.goreleaser.yml`、`Makefile` |
| **验收** | `goreleaser build --snapshot` 生成 6 个平台二进制 |

---

### Task 24：README 文档

| 项目 | 内容 |
|------|------|
| **编号** | P6-04 |
| **描述** | 编写 README.md，包含安装、快速开始、命令参考 |
| **依赖** | 所有任务 |
| **预估** | 0.5h |
| **产出** | `README.md` |
| **验收** | 文档完整、示例可运行 |

---

## 任务依赖关系图

```
P0-01 (Go Init)
  ├──→ P0-02 (Cobra Root)
  │      └──→ P0-04 (API Client)
  │             ├──→ P1-01 (Memo Create)   ──┐
  │             ├──→ P1-02 (Memo List)      ──┤
  │             ├──→ P1-03 (Memo Get)       ──┤
  │             ├──→ P1-04 (Memo Update)    ──┼──→ P2-01 (Shortcuts)
  │             ├──→ P1-05 (Memo Delete)    ──┘        │
  │             │                                      ├──→ P2-02 (Editor)
  │             ├──→ P1-06 (Memo Search)
  │             ├──→ P3-01 (Auth Status)
  │             ├──→ P3-02 (User Mgmt)
  │             ├──→ P5-01 (Resource Mgmt)
  │             ├──→ P5-02 (Comments)
  │             ├──→ P5-03 (Shares)
  │             └──→ P5-04 (Relations)
  └──→ P0-03 (Config)
         └──→ P0-04 (API Client)
  └──→ P4-01 (Renderer) ──→ P4-02 (Pipe/File)

ALL ──→ P6-01 (Unit Tests)
ALL ──→ P6-02 (Integration Tests)
ALL ──→ P6-03 (GoReleaser)
ALL ──→ P6-04 (README)
```

---

## 开发里程碑

| 里程碑 | 交付内容 | 预计完成 |
|--------|---------|---------|
| **M1 — 可运行骨架** | 配置系统 + API Client + Auth Status | 第 1 天 |
| **M2 — 核心功能** | Memo CRUD 全部命令 + 输出系统 | 第 2 天 |
| **M3 — 完整功能** | 快捷命令 + 用户管理 + 资源/分享/评论 | 第 3-4 天 |
| **M4 — 生产就绪** | 测试 + 构建 + 文档 | 第 5 天 |

---

## 技术风险与备选方案

| 风险 | 概率 | 缓解方案 |
|------|------|---------|
| Memos API 版本不兼容 | 低 | 基于已验证的 API (v0.28.0) 开发；proto 定义稳定 |
| CEL filter 语法复杂 | 低 | CLI 封装常用过滤场景，提供 `--tag` / `--keyword` 等语义化参数 |
| 管道模式信号处理 | 中 | 使用 `signal.NotifyContext` 正确处理 SIGINT |
| Windows 编码问题 | 低 | Go 标准库处理；Windows 专用 CI 测试 |

---

> **本文档完成后，即可开始编码开发。**