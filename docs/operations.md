# 运维说明

## 能力状态

- Python CLI 包，无第三方运行时依赖。
- 覆盖 Memos `v0.28.x` 的 memo、attachment、share、user、PAT、webhook、shortcut 和 raw API 入口。
- 配置文件权限为 `0600`。
- `memos config show` 会脱敏 token。
- 支持 `json`、`table`、`csv`、`plain` 和文件输出。
- 支持 Linux、macOS 和 Windows 安装脚本。

## 自动化建议

- CI 中优先使用 `MEMOS_SERVER` 和 `MEMOS_TOKEN`。
- 自动化脚本优先使用 `-j` 输出 JSON。
- 删除资源时使用完整资源名并显式传入 `--force`。
- 未封装的官方端点使用 `memos api METHOD PATH`。

## 兼容说明

- Memos `v0.28.x` 使用 `attachments` 端点。
- `resource` 命令是 `attachment` 的兼容别名。
- 配置文件 YAML 仅覆盖 CLI 自身生成的结构。
