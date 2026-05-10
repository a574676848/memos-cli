# 发布与安装入口

memos-cli 的公开仓库地址：

```text
https://github.com/a574676848/memos-cli
```

## 一键安装

Linux / macOS:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/install.sh)"
```

Windows PowerShell:

```powershell
iwr https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/install.ps1 -UseB | iex
```

## 一键升级

Linux / macOS:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/upgrade.sh)"
```

Windows PowerShell:

```powershell
iwr https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/upgrade.ps1 -UseB | iex
```

CLI 内置升级命令：

```bash
memos upgrade
```

## 质量检查

```bash
python3 -m unittest discover -s tests
python3 -m py_compile memos_cli/*.py
python3 -m memos_cli --version
python3 -m memos_cli -j upgrade --manager pip --source . --dry-run
```

## 包来源

默认包来源为 `memos-cli`。需要从 GitHub 安装时使用：

```bash
MEMOS_CLI_PACKAGE_SPEC="git+https://github.com/a574676848/memos-cli.git" scripts/install.sh
```

Windows:

```powershell
$env:MEMOS_CLI_PACKAGE_SPEC="git+https://github.com/a574676848/memos-cli.git"
.\scripts\install.ps1
```
