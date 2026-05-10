# 贡献指南

感谢你考虑参与 memos-cli。这个项目优先保持 CLI 行为稳定、文档可执行、实现简单。

## 开发环境

```bash
python3 -m pip install -e .
memos --version
```

运行测试：

```bash
python3 -m unittest discover -s tests
python3 -m py_compile memos_cli/*.py
```

## 提交变更前

- 保持命令、文档和测试同步。
- 不引入不必要的运行时依赖。
- 新增命令时补充 `docs/cli-reference.md`。
- 修改安装或升级行为时补充 `docs/installation.md`。
- 涉及 Memos API 路径时确认与 `v0.28.x` REST gateway 一致。

## Pull Request 建议

PR 描述建议包含：

- 变更目的
- 用户可见行为
- 测试结果
- 是否影响安装、配置或升级路径

## Issue 建议

报告问题时请提供：

- memos-cli 版本：`memos --version`
- Memos 版本
- 操作系统和 Python 版本
- 复现命令
- 错误输出或 HTTP 状态码
