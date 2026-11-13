# 本地启动与日常开发

## 1. 运行关系

```text
浏览器 → Vue / Vite（127.0.0.1:5173）
             ↓ /api 开发代理
         Django（127.0.0.1:8000）
             ↓ ORM
         MySQL（127.0.0.1:3308 → 容器内 3306）
```

沿用 `D:\aaasoftware_learning\company-site` 的学习路线。新工程有自己的 `.venv`、`node_modules`、数据库与数据卷。教学数据库的 3307 与本项目的 3308 分开。

本机本次因 Docker 故障采用独立 MySQL，按 [本机环境补充](08-local-environment.md) 用 `scripts/dev-mysql.ps1` 代替 `docker compose up`；其余前后端步骤相同。

## 2. 首次准备

推荐 Python 3.12、Node.js 24、Git、Docker Desktop（Linux containers）。`python --version`、`node --version` 和 `docker version` 可查看版本；Docker 的 Client 和 Server 都应可连接。

新成员先克隆仓库，路径不必与负责人相同：

```powershell
git clone https://github.com/wanbro333/lab.git
cd lab
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1
```

`setup.ps1` 做三件事：首次生成 `.env` 随机密钥、创建本项目虚拟环境、安装 Python／前端依赖。如果已建 `.venv`，继续使用它；更换 Python 版本请先检查解释器，不覆盖其他项目环境。

本机也可明确选用已安装的基础解释器：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1 -PythonCommand 'C:\Users\Lenovo\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe'
```

接着初始化数据库：

```powershell
docker compose up -d --wait
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py seed_demo --create-user
```

- Compose 只启动本项目 MySQL；应用用 `lab_app` 连接，不使用 root。
- `migrate` 建表；模型文件不会自动创建数据库表。
- `seed_demo` 可选，只添加缺失的 `DEMO-` 物品。
- `--create-user` 创建本地 `lab_dev` 开发管理员，随机密码写入 `.runtime/dev-account.txt`。若已有此用户，命令不会重置密码。
- 无需示例账号时改用 `createsuperuser`，由自己输入用户名和密码。

Docker volume 首次初始化后，修改 `.env` 中的数据库密码不会自动修改库内账号密码；应同步修改数据库账号，不要通过删除数据卷解决密码不一致。

## 3. 日常启动与关闭

先打开 Docker Desktop，再在根目录执行 `docker compose up -d --wait`。

两个终端分别执行 `scripts/dev-backend.ps1` 与 `scripts/dev-frontend.ps1`（命令完整写法见根 README）。统一用 `127.0.0.1` 访问，避免在 `localhost` 和 `127.0.0.1` 之间切换造成 Cookie 不一致。

| 服务 | 地址 |
| --- | --- |
| Vue 工作台 | http://127.0.0.1:5173/ |
| Django Admin | http://127.0.0.1:8000/admin/ |
| 接口健康检查 | http://127.0.0.1:8000/api/health/ |

关闭时在前后端终端按 `Ctrl+C`，再执行 `docker compose stop`。这会保留数据。`docker compose down` 同样保留命名卷；**不要随意添加 `-v`，它会删除数据库卷**。

若 8000 或 5173 已由教学工程占用，先确认服务归属。也可将后端改为 `dev-backend.ps1 -Port 8001`，并复制 `frontend/.env.example` 为 `frontend/.env`，设置 `API_PROXY_TARGET=http://127.0.0.1:8001`；前端另用 `npm.cmd run dev -- --port 5174`。不要结束不明进程。

## 4. 新成员的最小验收

1. 首页“服务连接正常”，健康接口返回 `status: ok`、`database: mysql`。
2. 使用开发账号登录；器材／材料分类和搜索可以切换。
3. 新增一个唯一编号的物品；刷新页面仍能找到它。
4. Django Admin 中也能找到同一条记录。
5. 重启后端，记录仍在；这说明数据保存在 MySQL，而不是浏览器内存。

## 5. 修改代码与测试

```powershell
# 修改模型之后生成并执行迁移，迁移文件需要提交
.\.venv\Scripts\python.exe backend\manage.py makemigrations
.\.venv\Scripts\python.exe backend\manage.py migrate

# 快速检查：不依赖 Docker，不写业务数据库
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

快速测试的内存 SQLite 仅用于测试，不能代替 MySQL 验证。`check --database default` 及真实页面保存可验证本机 MySQL。CI 会用 MySQL 执行同一组自动测试；本地 `lab_app` 无权创建 `test_lab_dev` 测试库，不要为跑测试直接扩大日常账号权限。需要本地完整 MySQL 自动测试时，使用专门测试实例／账号。

依赖调整：前端执行 `npm install 包名` 并提交 `package.json`、`package-lock.json`；Python 修改 `requirements.in`，使用 `uv pip compile requirements.in --output-file requirements.txt` 重新锁定，再安装并提交两个文件。常规成员安装用 `npm ci` 和 `pip install -r requirements.txt`。

## 6. 常见问题

| 现象 | 检查与处理 |
| --- | --- |
| 无法执行 npm.ps1 | 用 `npm.cmd`；脚本均已使用该形式 |
| 连接不到 Docker 引擎 | 打开 Docker Desktop，确认 Linux 引擎就绪；先检查诊断，不执行恢复出厂设置 |
| MySQL 连接拒绝 | `docker compose ps`、`docker compose logs --tail 60 db`；确认 3308 与 `.env` 一致 |
| Access denied | 核对 `.env` 和数据库中账号实际密码，初始化后的卷不会随 `.env` 自动改密码 |
| 表不存在 | 执行 `migrate`；拉取包含迁移的 PR 后也要执行 |
| 403 安全验证 | 统一主机名并刷新；前端写操作会先取 CSRF token，不要删除后端中间件 |
| 401 | 会话过期或未登录，重新登录 |
| 忘记本地账号密码 | `python backend/manage.py changepassword lab_dev`（使用 `.venv` 中的 Python） |
| Linux 安装 mysqlclient 失败 | 安装 `python3-dev default-libmysqlclient-dev build-essential pkg-config` 后重试 |

macOS/Linux 可用 `python3 -m venv .venv`、`.venv/bin/python -m pip install -r requirements.txt`、复制并填写 `.env`，再执行相同 Compose／Django／npm 命令；PowerShell 脚本仅作为 Windows 便利入口。
