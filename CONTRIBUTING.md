# 参与开发

先阅读 [启动说明](docs/01-local-development.md) 与 [Git 教程](docs/04-git-collaboration.md)。

1. 从最新 `main` 建立 `feat/模块-功能`、`fix/问题` 或 `docs/主题` 分支。
2. 一个 Issue 对应一个清晰的任务和一个 PR；提前约定接口与文件负责人。
3. 模型变化提交对应 migration；新增依赖同时提交锁文件，不手工修改锁文件。
4. 修改共享路由、用户模型或基础样式时先在任务中协调。
5. 提交前运行 `scripts/check.ps1`；数据库相关行为另用 MySQL 验证。
6. PR 写清操作前后行为、验证方法、截图及迁移影响，由另一名成员审查。

代码约定：Vue 使用 `<script setup>` 和 JavaScript；Python 使用 4 空格；前端使用 2 空格；接口以 `/api/` 开头，使用末尾斜杠。数量和金额跨接口用十进制字符串。

前端可在 `frontend` 目录运行 `npm.cmd run format` 统一格式，检查命令和 CI 会验证格式，减少多人协作时纯排版造成的冲突。

不要提交 `.env`、`.runtime`、`.venv`、`node_modules`、`dist`、真实实验室数据。也不要把 GitHub token、数据库密码、AI 密钥放进任何 `VITE_*` 变量。
