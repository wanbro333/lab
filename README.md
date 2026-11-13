# 实验室管理系统 · Lab

供小组开始共同开发的 **Vue + Django + MySQL 基础工程**。沿用教学项目的前后端分离结构，通过一个可运行的物品台账示例说明页面、接口、模型与数据库如何协作。

## 已有能力

- Vue 工作台、侧边导航、登录和个人信息页。
- 器材／材料列表、分类筛选、搜索、分页、新增与 MySQL 持久化。
- Django Session 登录、CSRF 保护、管理员写入权限、Admin 管理入口。
- 采购、收货、智能问答的规划入口，**尚未实现这些业务**。
- 独立环境、锁定依赖、数据库迁移、PR 模板、Issue 模板、GitHub Actions。

本项目是本地开发起点。当前数量是初始台账数量，尚无领用、归还、审批和库存流水，不应当作完整库存管理系统投入使用。

**这台电脑已准备独立 MySQL**：因 Docker 启动故障，日常先运行 `scripts/dev-mysql.ps1`，再启动前后端。具体命令见 [本机环境补充](docs/08-local-environment.md)。下方 Docker 路线供正常安装 Docker 的团队成员使用。

## 从这里开始

| 文档 | 用途 |
| --- | --- |
| [本地启动与日常开发](docs/01-local-development.md) | 安装、启动、关闭、验证和排错 |
| [前端初步设计整理](docs/02-frontend-design.md) | 将四张草图整理为页面、字段、交互与待讨论项 |
| [架构与目录说明](docs/03-architecture.md) | 对照教学项目理解代码，并找到扩展位置 |
| [Git 与 GitHub 协作教程](docs/04-git-collaboration.md) | 提交、分支、PR、并行开发和冲突处理 |
| [接口约定](docs/05-api.md) | 前后端联调依据 |
| [成员分工与后续任务](docs/06-team-backlog.md) | 可拆成 Issue 的任务与验收条件 |
| [验证记录](docs/07-verification.md) | 当前版本的实际检查结果与局限 |
| [本机环境补充](docs/08-local-environment.md) | Docker 故障记录与独立 MySQL 备用方式 |

## 最快启动（Windows PowerShell）

需要 Python 3.12、Node.js 24、Git，以及已启动的 Docker Desktop Linux 引擎。

```powershell
cd D:\lab
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1
docker compose up -d --wait
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py seed_demo --create-user
```

`setup.ps1` 首次生成随机本地密钥和独立 `.venv`，重复执行保留 `.env`。可用 `-PythonCommand '你的Python3.12路径'` 指定解释器。

随后在两个终端分别运行：

```powershell
# 终端 A，保持运行
powershell -NoProfile -ExecutionPolicy Bypass -File D:\lab\scripts\dev-backend.ps1
```

```powershell
# 终端 B，保持运行
powershell -NoProfile -ExecutionPolicy Bypass -File D:\lab\scripts\dev-frontend.ps1
```

打开 [工作台](http://127.0.0.1:5173/)。本地示例管理员的随机密码在 `.runtime/dev-account.txt`，该文件被 Git 忽略。示例数据带 `DEMO-` 前缀，重复初始化不会覆盖原值。

## 提交前检查

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
git status
git diff
```

本地快速测试使用内存 SQLite；应用默认连接 MySQL。GitHub CI 使用临时 MySQL 测试库。检查通过后走功能分支 → PR → 同伴审查 → 合并，不把密码、虚拟环境或数据库文件提交到 Git。

仓库：[wanbro333/lab](https://github.com/wanbro333/lab)。本次先交付本地代码；首次推送的步骤见 Git 教程。
