# 发布到 GitHub

本文说明如何把当前本地项目发布成 GitHub 开源仓库，并让一键安装脚本指向真实仓库地址。

## 前置条件

- 已安装 `git`
- 已安装并登录 GitHub CLI：`gh auth login`
- 或者已在 GitHub Web 创建空仓库

## 初始化本地仓库

```bash
git init
git add .
git commit -m "Initial open source release"
```

## 使用 GitHub CLI 创建远端仓库

```bash
gh repo create <owner>/memos-cli \
  --public \
  --source . \
  --remote origin \
  --push
```

如果仓库已在 GitHub Web 创建：

```bash
git remote add origin git@github.com:<owner>/memos-cli.git
git branch -M main
git push -u origin main
```

## 替换文档中的占位符

README 和安装文档使用 `<owner>` 作为 GitHub owner 占位符。创建远端仓库后替换为真实 owner：

```bash
python3 - <<'PY'
from pathlib import Path
for path in [Path("README.md"), Path("docs/installation.md"), Path("docs/cli-reference.md")]:
    text = path.read_text()
    path.write_text(text.replace("<owner>", "your-github-owner"))
PY
```

替换后验证安装命令指向真实地址：

```bash
rg '<owner>' README.md docs
```

没有输出表示占位符已清理。

## 发布前检查

```bash
python3 -m unittest discover -s tests
python3 -m py_compile memos_cli/*.py
python3 -m memos_cli --version
python3 -m memos_cli -j upgrade --manager pip --source . --dry-run
```

## 包来源策略

脚本默认安装 `memos-cli` 包名，适合发布到 PyPI 后使用。发布到 PyPI 前，可以使用 GitHub 仓库作为包来源：

```bash
MEMOS_CLI_PACKAGE_SPEC="git+https://github.com/<owner>/memos-cli.git" scripts/install.sh
```

Windows:

```powershell
$env:MEMOS_CLI_PACKAGE_SPEC="git+https://github.com/<owner>/memos-cli.git"
.\scripts\install.ps1
```

## GitHub 社区文件

仓库根目录包含：

- `LICENSE`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`

这些文件用于降低外部贡献者进入成本，并与 GitHub 社区健康检查保持一致。
