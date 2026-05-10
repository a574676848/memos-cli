# Memos CLI — 需求分析文档

> **版本**: v1.0  
> **日期**: 2026-05-10  
> **作者**: AI 技术合伙人  
> **状态**: ✅ 已确认  

---

## 1. 项目背景

### 1.1 源项目概述

[Memos](https://github.com/usememos/memos) 是 GitHub 上 **59.5k Stars** 的开源自托管笔记工具，核心特点：

| 特性 | 说明 |
|------|------|
| **即时捕获** | Timeline-first UI，打开即写 |
| **数据自主** | 自托管，Markdown 格式存储，零遥测 |
| **极简部署** | 单一 Go 二进制，~20MB Docker 镜像，支持 SQLite/MySQL/PostgreSQL |
| **开放生态** | MIT 协议，完整 REST + gRPC API |

### 1.2 当前环境

| 项目 | 详情 |
|------|------|
| **Memos 实例** | `http://192.168.5.251:5230` |
| **认证用户** | `root` (ADMIN) |
| **认证方式** | Personal Access Token (PAT) |
| **当前服务版本** | v0.28.0（2026-04-27 最新） |

### 1.3 痛点与动机

1. **GUI 依赖问题**：现有操作全部依赖 Web GUI，无法在终端环境下使用
2. **自动化缺失**：无 CLI 就无法做脚本化批量操作（如导入、导出、定时备份）
3. **AI Agent 不可用**：2026 年 AI Agent 生态主要靠 CLI 驱动，Memos 缺乏 CLI 入口
4. **开发者效率**：程序员更喜欢终端操作，每次切到浏览器记笔记效率低
5. **同类工具趋势**：飞书、Google Workspace、Stripe、网易云音乐均已发布 CLI

---

## 2. 用户画像

### 2.1 核心用户群

| 画像 | 典型场景 | 优先级 |
|------|---------|--------|
| **独立开发者** | 终端内快速记录想法/代码片段 | P0 |
| **运维工程师** | 通过脚本自动记录服务器状态日志 | P0 |
| **AI Agent 调用者** | 让 AI Agent 通过 CLI 读写知识库 | P1 |
| **笔记重度用户** | 批量导入导出、标签管理 | P1 |
| **自托管爱好者** | 管理多用户、监控服务状态 | P2 |

### 2.2 典型用户故事

```
# Alice - 后端开发
$ memos new "修复了 payment 模块的空指针异常 #bug #fixed"
## ✅ Memo created: memos/abc123

# Bob - SRE
$ memos log "CPU 使用率超过 90%，已触发自动扩容"
## 通过 cron + memos CLI 每天定时记录集群状态

# Carol - AI Agent
$ memos list --filter "bug" --limit 5 --json
## 返回结构化 JSON，供 LLM 上下文使用
```

---

## 3. 竞品 CLI 设计参考

### 3.1 2026 年新一代 CLI 设计范式

参考 **Claude Code CLI**、**飞书 Lark CLI**、**OpenAI Codex CLI**、**Google Workspace CLI**，归纳设计原则：

| 设计原则 | 说明 |
|---------|------|
| **子命令层次** | `{binary} {resource} {action} [flags]`，如 `memos memo create` |
| **CRUD 一致性** | 所有资源统一 `list/create/get/update/delete` 动词 |
| **双模式输出** | 默认人类可读表格，`--json` 输出结构化 JSON（供 AI 消费） |
| **管道友好** | 支持 stdin 输入、stdout 输出可被下游管道处理 |
| **非交互默认** | 默认 `--no-interactive`，不弹交互式提示，适合脚本和 AI |
| **配置文件驱动** | 通过 `~/.memos-cli.yaml` 管理多实例连接配置 |
| **--dry-run** | 危险操作支持预览模式，AI Agent 安全调用 |

### 3.2 参考 CLI 具体设计

#### Claude Code CLI 设计特点
- 使用 `claude` 为主命令，内置多个 subcommands
- 支持 slash commands（`/command` 语法）
- session 管理（可恢复对话）
- 高度可配置的 `~/.claude.yaml`

#### 飞书 Lark CLI 设计特点
- 层级化资源模型：`lark-cli calendar agenda`、`lark-cli message send`
- 每个资源下 CRUD 齐全
- `--json` / `--csv` 多格式输出
- OAuth 设备码认证流程

#### Codex CLI 设计特点
- `codex` 为主入口
- 极强的管道和组合能力
- `--model` 支持切换后端模型
- 与 Git 深度集成

---

## 4. 功能需求

### 4.1 总体目标

将 Memos Web 的全部功能 CLI 化，实现 **「终端就是你的 Memos 客户端」**。

### 4.2 功能矩阵（基于 Proto API 完整分析）

#### 模块 A：认证与配置 (P0)

| ID | 功能 | 描述 |
|----|------|------|
| A1 | `memos config init` | 交互式配置向导，设置 API 地址和 PAT |
| A2 | `memos config show` | 显示当前配置 |
| A3 | `memos auth status` | 验证 Token 是否有效 |
| A4 | `memos config set-context` | 多实例上下文切换 |

#### 模块 B：Memo 笔记 CRUD (P0)

| ID | 功能 | 描述 | REST 端点 |
|----|------|------|----------|
| B1 | `memos memo create` | 创建新笔记（支持 `--content`、`--visibility`、`--pinned`） | `POST /api/v1/memos` |
| B2 | `memos memo list` | 分页列出笔记（支持 `--filter`、`--tag`、`--limit`、`--state`） | `GET /api/v1/memos` |
| B3 | `memos memo get` | 查看单条笔记详情 | `GET /api/v1/{name=memos/*}` |
| B4 | `memos memo update` | 修改笔记（内容、可见性、置顶） | `PATCH /api/v1/{memo.name=memos/*}` |
| B5 | `memos memo delete` | 删除笔记（支持 `--force`） | `DELETE /api/v1/{name=memos/*}` |
| B6 | `memos memo search` | 全文搜索（基于服务端 CEL filter） | `GET /api/v1/memos?filter=...` |

#### 模块 C：Memo 快捷操作 (P0)

| ID | 功能 | 描述 |
|----|------|------|
| C1 | `memos new "内容"` | `memos memo create` 的快捷别名 |
| C2 | `memos ls` | `memos memo list` 的快捷别名 |
| C3 | `memos rm <id>` | `memos memo delete` 的快捷别名 |
| C4 | `memos edit <id>` | 通过 `$EDITOR` 打开编辑器修改笔记 |

#### 模块 D：附件与资源 (P1)

| ID | 功能 | 描述 | REST 端点 |
|----|------|------|----------|
| D1 | `memos resource upload` | 上传附件（图片、文件等） | `POST /api/v1/resources` |
| D2 | `memos resource list` | 列出所有资源 | `GET /api/v1/resources` |
| D3 | `memos resource delete` | 删除资源 | `DELETE /api/v1/{name=resources/*}` |
| D4 | `memos memo attach` | 将资源关联到笔记 | `PATCH /api/v1/{name=memos/*}/attachments` |

#### 模块 E：评论 (P1)

| ID | 功能 | 描述 | REST 端点 |
|----|------|------|----------|
| E1 | `memos memo comment` | 给笔记添加评论 | `POST /api/v1/{name=memos/*}/comments` |
| E2 | `memos memo comments` | 查看笔记的评论列表 | `GET /api/v1/{name=memos/*}/comments` |

#### 模块 F：分享 (P1)

| ID | 功能 | 描述 | REST 端点 |
|----|------|------|----------|
| F1 | `memos share create` | 创建分享链接（支持过期时间） | `POST /api/v1/{parent=memos/*}/shares` |
| F2 | `memos share list` | 列出笔记的分享链接 | `GET /api/v1/{parent=memos/*}/shares` |
| F3 | `memos share revoke` | 撤销分享链接 | `DELETE /api/v1/{name=memos/*/shares/*}` |

#### 模块 G：关联与引用 (P2)

| ID | 功能 | 描述 |
|----|------|------|
| G1 | `memos memo link` | 设置笔记之间的引用关系 |
| G2 | `memos memo relations` | 查看笔记的关系图 |

#### 模块 H：用户管理 (P1，admin only)

| ID | 功能 | 描述 | REST 端点 |
|----|------|------|----------|
| H1 | `memos user list` | 列出所有用户 | `GET /api/v1/users` |
| H2 | `memos user get` | 查看用户详情 | `GET /api/v1/{name=users/*}` |
| H3 | `memos user create` | 创建新用户 | `POST /api/v1/users` |
| H4 | `memos user stats` | 查看用户统计（笔记数、标签等） | `GET /api/v1/{name=users/*}:getStats` |

#### 模块 I：输出与格式化 (P0)

| ID | 功能 | 描述 |
|----|------|------|
| I1 | `--json` | 输出原始 JSON（供 AI Agent 消费） |
| I2 | `--format table\|csv\|plain` | 人类可读的多种格式 |
| I3 | `--no-color` | 禁用 ANSI 颜色 |
| I4 | `--output-file` | 输出到文件 |

#### 模块 J：管道与脚本 (P0)

| ID | 功能 | 描述 |
|----|------|------|
| J1 | stdin 读取 | `echo "note" | memos new` |
| J2 | 管道输出 | `memos list --json | jq` |
| J3 | 退出码规范 | 0=成功, 1=业务错误, 2=网络错误 |

---

## 5. 非功能需求

### 5.1 性能
- 启动时间 < 100ms（二进制无冷启动开销）
- API 调用超时默认 30s，可配置
- 支持 HTTP/2 连接复用

### 5.2 安全
- Token 存储在 `~/.memos-cli.yaml`，权限设为 `0600`
- 不在日志中输出 Token 明文
- 支持 `--dry-run` 预览危险操作

### 5.3 可移植性
- 单一二进制分发（Go 编译）
- 支持 macOS (arm64/amd64)、Linux (arm64/amd64)、Windows (amd64)
- 通过 `brew install` / `go install` / 直接下载安装

### 5.4 可维护性
- 代码 100% 对应 REST API proto 定义
- API 模型自动从 proto 生成
- 完整的单元测试和集成测试

### 5.5 文档
- `memos help` 内置完整帮助
- `memos memo create --help` 逐命令帮助
- README 包含快速开始指南

---

## 6. 技术选型建议

| 维度 | 推荐方案 | 理由 |
|------|---------|------|
| **语言** | Go | Memos 本身是 Go 写的，生态一致；编译为单二进制，跨平台零依赖 |
| **CLI 框架** | [Cobra](https://github.com/spf13/cobra) | Go 生态最成熟 CLI 框架，Kubernetes/kubectl 同款 |
| **配置管理** | [Viper](https://github.com/spf13/viper) | 与 Cobra 无缝集成，支持 YAML/ENV/Flag 多来源 |
| **HTTP 客户端** | [resty](https://github.com/go-resty/resty) | 链式调用，自动重试，中间件支持 |
| **输出格式化** | [tablewriter](https://github.com/olekukuty/tablewriter) | ASCII 表格渲染 |
| **JSON 处理** | 标准库 + protojson | 直接使用 memos proto 定义的类型 |
| **跨平台编译** | Go 原生交叉编译 | `GOOS/GOARCH` 一键编译 |

---

## 7. 与现有生态的关系

```
┌────────────────────────────────────────────┐
│                  Memos 生态                  │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Web UI   │  │ iOS App  │  │ Android   │  │
│  │ (React)  │  │ (Swift)  │  │ (Kotlin)  │  │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │             │              │         │
│  ┌────▼─────────────▼──────────────▼─────┐  │
│  │         REST / gRPC API (HTTP)         │  │
│  └────────────────┬──────────────────────┘  │
│                   │                          │
│  ┌────────────────▼──────────────────────┐  │
│  │         memos-cli  ←  NEW!            │  │
│  │  ┌─────────┐ ┌──────────┐ ┌───────┐  │  │
│  │  │ 人类用户  │ │ Shell脚本 │ │AI Agent│  │  │
│  │  └─────────┘ └──────────┘ └───────┘  │  │
│  └───────────────────────────────────────┘  │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 8. 风险与约束

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| API 版本变更 | 高 | 基于 proto 自动生成客户端代码，版本变更时只需重新生成 |
| PAT 泄漏 | 高 | 文件权限控制 + .gitignore 模板 |
| 网络不可达 | 中 | 明确的超时和重试机制 + 有意义的错误消息 |
| 大笔记性能 | 低 | 服务端分页，CLI 默认 `--limit 20` |

---

## 9. 验收标准

1. ✅ 能用 `memos new "hello"` 从终端创建一条笔记
2. ✅ 能用 `memos ls` 列出最近 20 条笔记（表格格式）
3. ✅ 能用 `memos ls --json` 输出 JSON 格式
4. ✅ 能用 `memos edit <id>` 打开 `$EDITOR` 编辑笔记
5. ✅ 管道输入 `echo "test" | memos new` 正常工作
6. ✅ 在 macOS / Linux / Windows 上均可编译运行
7. ✅ `memos help` 有完整、准确的帮助信息

---

> **下一步**：请确认需求分析内容，随后进入 [系统分析文档 (02-system-design.md)](./02-system-design.md)