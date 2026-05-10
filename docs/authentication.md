# 授权与配置

memos-cli 通过 Memos Personal Access Token 调用 REST API，不实现账号密码登录，也不会保存用户密码。

## 获取 Token

1. 打开 Memos Web。
2. 进入用户设置中的 Personal Access Token 页面。
3. 创建一个用于 CLI 的 token。
4. 保存生成的 token，后续命令用 `Bearer` 方式发送到 Memos API。

## 初始化配置

```bash
memos config init \
  --name production \
  --server http://127.0.0.1:5230 \
  --token 'memos_pat_xxx' \
  --username root
```

验证授权：

```bash
memos auth status
```

`auth status` 会请求 `/api/v1/auth/me`，用于确认当前 token 是否可用。

## 配置文件

默认路径：

```text
~/.config/memos-cli/config.yaml
```

示例：

```yaml
version: "1"
default_context: production
contexts:
  production:
    server: "http://127.0.0.1:5230"
    token: "memos_pat_xxx"
    username: "root"
```

配置文件写入时会设置为 `0600` 权限。查看配置时 token 会被脱敏：

```bash
memos config show
```

## 多环境

新增或更新 context：

```bash
memos config init \
  --name staging \
  --server http://staging.example.com \
  --token 'memos_pat_staging' \
  --username root
```

切换默认 context：

```bash
memos config set-context staging
```

临时指定 context：

```bash
memos --context production memo list --limit 5
```

## 环境变量覆盖

环境变量优先级高于配置文件：

| 变量 | 说明 |
| --- | --- |
| `MEMOS_SERVER` | Memos API 地址 |
| `MEMOS_TOKEN` | Personal Access Token |
| `MEMOS_CONTEXT` | 默认 context 名称 |
| `MEMOSCLI_CONFIG` | 配置文件路径 |
| `MEMOS_FORMAT` | 默认输出格式 |
| `MEMOS_TIMEOUT` | 请求超时时间 |

CI 或临时脚本中推荐使用环境变量：

```bash
MEMOS_SERVER="http://127.0.0.1:5230" \
MEMOS_TOKEN="memos_pat_xxx" \
memos -j memo list --limit 3
```
