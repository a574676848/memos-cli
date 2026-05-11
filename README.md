# memos-cli

面向自托管 Memos 的命令行客户端，让终端、脚本和自动化任务可以直接读写 Memos `v0.28.x` REST API。

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 核心能力

- 管理 memo：创建、列表、查看、更新、删除、搜索、编辑。
- 管理附件与分享：上传附件、关联 memo、创建和撤销分享链接；创建分享时自动输出基于当前配置服务地址的可访问链接。
- 管理用户侧资源：用户、Personal Access Token、Webhook、Shortcut。
- 提供 `memos api METHOD PATH` 原始 API 入口，覆盖尚未封装成一等命令的 Memos REST 端点。
- 无第三方运行时依赖，支持 Linux、macOS 和 Windows。

## 快速开始

Linux / macOS:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/install.sh)"
```

Windows PowerShell:

```powershell
iwr https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/install.ps1 -UseB | iex
```

源码安装:

```bash
python3 -m pip install -e .
memos --version
```

安装脚本可重复执行。检测到已有 `memos` 命令时会执行升级路径；未安装时会优先使用 `pipx`，没有 `pipx` 时使用独立 venv。
默认包来源为本仓库 GitHub 源码，避免 Windows 环境误装到 PyPI 上旧版同名包。

## 授权与配置

memos-cli 使用 Memos Web 中创建的 Personal Access Token，不保存账号密码。

```bash
memos config init \
  --name production \
  --server http://127.0.0.1:5230 \
  --token 'memos_pat_xxx' \
  --username root

memos auth status
```

配置文件默认写入 `~/.config/memos-cli/config.yaml`，权限为 `0600`。也可以用环境变量覆盖配置：

```bash
export MEMOS_SERVER="http://127.0.0.1:5230"
export MEMOS_TOKEN="memos_pat_xxx"
memos auth status
```

## 常用命令

```bash
memos new "ship CLI support #memos"
memos ls --limit 10
memos memo get memos/abc123
memos memo update abc123 --content "updated" --pinned true
memos rm abc123 --force
```

附件、分享和管理命令：

```bash
memos attachment upload ./image.png
memos memo attach abc123 attachments/def456
memos share create abc123 --expire-in-days 7
memos user list
memos pat list --user root
memos webhook list --user root
```

原始 API 入口：

```bash
memos api GET /api/v1/users/root/settings
memos api PATCH /api/v1/users/root/settings/GENERAL \
  --data '{"generalSetting":{"locale":"zh","memoVisibility":"PRIVATE"}}'
```

全局参数需要放在子命令前：

```bash
memos -j memo list --limit 5
memos -f csv user list
memos -o memos.json -j memo list --limit 100
```

## 升级

独立升级命令：

```bash
memos upgrade
```

脚本升级：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/upgrade.sh)"
```

Windows:

```powershell
iwr https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/upgrade.ps1 -UseB | iex
```

默认升级来源同样是本仓库 GitHub 源码；需要临时改用其他来源时，可显式指定：

```bash
MEMOS_CLI_PACKAGE_SPEC="." scripts/install.sh
memos upgrade --source "."
```

## 文档

- [安装与升级](docs/installation.md)
- [授权与配置](docs/authentication.md)
- [命令参考](docs/cli-reference.md)
- [运维说明](docs/operations.md)
- [发布与安装入口](docs/release.md)
- [文档中心](docs/README.md)

## 开发

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q memos_cli
```

本地 smoke test:

```bash
python3 -m memos_cli -j --config /tmp/memos-cli.yaml config init \
  --name production \
  --server http://127.0.0.1:5230 \
  --token "$MEMOS_TOKEN" \
  --username root

python3 -m memos_cli --config /tmp/memos-cli.yaml auth status
python3 -m memos_cli --config /tmp/memos-cli.yaml memo list --limit 2
```

## 贡献

欢迎提交 issue 和 pull request。开始前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

## 许可证

本项目使用 [MIT License](LICENSE)。

## 致谢

感谢 [usememos/memos](https://github.com/usememos/memos) 提供优秀的自托管笔记系统和 REST API。
