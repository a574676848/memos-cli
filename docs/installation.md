# 安装与升级

本文说明 memos-cli 在 Linux、macOS 和 Windows 上的一键安装方式，以及重复执行脚本时的升级行为。

## 环境要求

- Python `3.11+`
- 推荐安装 `pipx`，用于隔离 CLI 运行环境
- 没有 `pipx` 时，脚本会自动使用独立 venv

安装脚本默认从本仓库 GitHub 源码安装：

```text
git+https://github.com/a574676848/memos-cli.git
```

这样可以确保 Linux、macOS 和 Windows 获得同一套源码产物，避免 Windows PowerShell 误装到 PyPI 上旧版同名包。

## Linux / macOS

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/install.sh)"
```

这个命令的工作方式是：`curl` 从 GitHub raw 地址下载 `scripts/install.sh`，`/bin/bash -c` 在本机执行脚本。脚本内部负责检测 `pipx`、Python、已有 `memos` 命令，并决定安装或升级。

本地仓库安装：

```bash
cd memos-cli
MEMOS_CLI_PACKAGE_SPEC=. scripts/install.sh
```

## Windows PowerShell

```powershell
iwr https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/install.ps1 -UseB | iex
```

本地仓库安装：

```powershell
cd memos-cli
$env:MEMOS_CLI_PACKAGE_SPEC="."
.\scripts\install.ps1
```

## 可重复执行策略

安装脚本是幂等入口：

- 如果系统中没有 `memos` 命令，执行安装。
- 如果系统中已经存在 `memos` 命令，执行升级或强制重装。
- 默认优先使用 `pipx`。
- 没有 `pipx` 时使用独立 venv，并把 `memos` 命令包装到本机用户 bin 目录。

可用环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `MEMOS_CLI_PACKAGE_SPEC` | `git+https://github.com/a574676848/memos-cli.git` | pip / pipx 可识别的包来源，可设为 PyPI 包名、Git URL 或本地路径 |
| `MEMOS_CLI_PACKAGE_NAME` | `memos-cli` | pipx 升级时使用的包名 |
| `MEMOS_CLI_COMMAND_NAME` | `memos` | CLI 命令名 |
| `MEMOS_CLI_INSTALL_MANAGER` | `auto` | 可选 `auto`、`pipx`、`pip`、`venv` |
| `MEMOS_CLI_VENV_DIR` | Linux/macOS: `~/.local/share/memos-cli/venv`；Windows: `%LOCALAPPDATA%\memos-cli\venv` | venv 模式的安装目录 |
| `MEMOS_CLI_BIN_DIR` | Linux/macOS: `~/.local/bin`；Windows: `%USERPROFILE%\.local\bin` | venv 模式的命令包装目录 |
| `PYTHON` | `python3` 或 `python` | pip 模式使用的 Python |

## 独立升级命令

安装后可以直接运行：

```bash
memos upgrade
```

`memos upgrade` 默认从本仓库 GitHub 源码升级。需要改用本地目录、私有 fork 或 PyPI 包时，使用 `--source` 显式指定。

指定来源升级：

```bash
memos upgrade --source "."
```

只打印将要执行的命令：

```bash
memos -j upgrade --dry-run
```

脚本形式：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/upgrade.sh)"
```

Windows:

```powershell
.\scripts\upgrade.ps1
```

## PATH 提示

如果脚本安装成功但提示 `memos` 不在 `PATH`，需要把 Python user scripts 目录加入 `PATH`。常见位置：

- Linux / macOS：`~/.local/bin`
- Windows：`%APPDATA%\Python\Python3x\Scripts`

加入后重新打开终端并验证：

```bash
memos --version
```
