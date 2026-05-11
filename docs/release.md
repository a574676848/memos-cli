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
python3 -m compileall -q memos_cli
python3 -m memos_cli --version
python3 -m memos_cli -j upgrade --manager pip --source . --dry-run
```

## 包来源

默认包来源为本仓库 GitHub 源码：

```text
git+https://github.com/a574676848/memos-cli.git
```

一键安装脚本和 `memos upgrade` 都使用这个默认来源，确保跨平台安装到当前仓库产物，而不是 PyPI 上旧版同名包。

需要改用其他来源时，显式覆盖 `MEMOS_CLI_PACKAGE_SPEC`：

```bash
MEMOS_CLI_PACKAGE_SPEC="." scripts/install.sh
```

Windows PowerShell:

```powershell
$env:MEMOS_CLI_PACKAGE_SPEC="."
.\scripts\install.ps1
```
