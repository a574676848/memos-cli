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
gh repo create a574676848/memos-cli \
  --public \
  --source . \
  --remote origin \
  --push
```

如果仓库已在 GitHub Web 创建：

```bash
git remote add origin git@github.com:a574676848/memos-cli.git
git branch -M main
git push -u origin main
```

## 验证安装地址

README 和安装文档已使用 GitHub owner `a574676848`。推送前确认文档中的安装地址都指向真实仓库：

```bash
rg 'github.com/a574676848/memos-cli|raw.githubusercontent.com/a574676848/memos-cli' README.md docs
```

如果后续迁移仓库 owner，需要同步替换这些地址。

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
MEMOS_CLI_PACKAGE_SPEC="git+https://github.com/a574676848/memos-cli.git" scripts/install.sh
```

Windows:

```powershell
$env:MEMOS_CLI_PACKAGE_SPEC="git+https://github.com/a574676848/memos-cli.git"
.\scripts\install.ps1
```

README 中的一键安装命令本质上依赖 GitHub raw 文件地址：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/a574676848/memos-cli/main/scripts/install.sh)"
```

只要 `scripts/install.sh` 已推送到公开仓库的 `main` 分支，这个命令就可以直接使用。脚本内容变更后，用户再次执行同一个命令会拿到最新脚本，并按脚本内的幂等逻辑安装或升级。

## GitHub 社区文件

仓库根目录包含：

- `LICENSE`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`

这些文件用于降低外部贡献者进入成本，并与 GitHub 社区健康检查保持一致。
