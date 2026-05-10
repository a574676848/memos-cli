# 安装与升级

本文说明 memos-cli 在 Linux、macOS 和 Windows 上的一键安装方式，以及重复执行脚本时的升级行为。

## 环境要求

- Python `3.11+`
- 推荐安装 `pipx`，用于隔离 CLI 运行环境
- 没有 `pipx` 时，脚本会回退到 `python -m pip install --user --upgrade`

## Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/<owner>/memos-cli/main/scripts/install.sh | sh
```

本地仓库安装：

```bash
cd memos-cli
MEMOS_CLI_PACKAGE_SPEC=. scripts/install.sh
```

## Windows PowerShell

```powershell
iwr https://raw.githubusercontent.com/<owner>/memos-cli/main/scripts/install.ps1 -UseB | iex
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
- 没有 `pipx` 时使用 `pip --user --upgrade`。

可用环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `MEMOS_CLI_PACKAGE_SPEC` | `memos-cli` | pip / pipx 可识别的包来源，可设为 PyPI 包名、Git URL 或本地路径 |
| `MEMOS_CLI_PACKAGE_NAME` | `memos-cli` | pipx 升级时使用的包名 |
| `MEMOS_CLI_COMMAND_NAME` | `memos` | CLI 命令名 |
| `MEMOS_CLI_INSTALL_MANAGER` | `auto` | 可选 `auto`、`pipx`、`pip` |
| `PYTHON` | `python3` 或 `python` | pip 模式使用的 Python |

## 独立升级命令

安装后可以直接运行：

```bash
memos upgrade
```

指定来源升级：

```bash
memos upgrade --source "git+https://github.com/<owner>/memos-cli.git"
```

只打印将要执行的命令：

```bash
memos -j upgrade --dry-run
```

脚本形式：

```bash
scripts/upgrade.sh
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
