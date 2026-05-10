# 文档中心

memos-cli 是面向 Memos `v0.28.x` REST API 的命令行客户端。本文档中心按使用路径组织，优先服务安装、授权、命令使用和开源发布。

## 快速导航

- [安装与升级](installation.md)：Linux、macOS、Windows 的一键安装脚本，重复执行和升级策略。
- [授权与配置](authentication.md)：Personal Access Token、配置文件、环境变量和多 context。
- [命令参考](cli-reference.md)：全局参数、memo、附件、分享、用户管理和原始 API。
- [发布到 GitHub](github-release.md)：初始化 git、创建 GitHub 仓库、设置包来源和发布前检查。
- [生产可用性](05-production-readiness.md)：当前能力边界、运行建议和风险。

## 项目背景

以下文档记录需求、设计与实施计划，适合维护者追溯上下文：

- [需求分析](01-requirements.md)
- [系统设计](02-system-design.md)
- [任务清单](03-task-plan.md)
- [差距分析](04-gap-analysis.md)
- [生产可用性](05-production-readiness.md)

## 维护入口

- 根目录 [README](../README.md) 是对外门面，保持短路径和稳定表达。
- 新增用户教程优先放在 `docs/`，再从 README 链接。
- 脚本行为变更时，同步更新 [安装与升级](installation.md)。
