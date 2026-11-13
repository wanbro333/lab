# 本机环境补充：独立 MySQL 启动方式

## 为什么有这份说明

本次本机 Docker Desktop 无法启动：先遇到 `Docker/run/dockerInference` 残留 socket，随后在 `docker-secrets-engine/engine.sock` 继续报 Windows 1920“系统无法访问此文件”。原有容器、镜像、数据卷未清理，也未恢复出厂设置。

为完成真实 MySQL 联调，在 `D:\lab\.runtime` 放置了官方 MySQL 8.4.13 Windows ZIP 发行版，单独运行本项目数据库。它与 Compose 方案使用同样的 `.env`、应用账号和 3308 端口，Django 无需改代码。**两种数据库启动方式二选一，不能同时占用 3308；两者存储的数据也不会自动同步。**

## 这台电脑的日常命令

已完成首次初始化后，数据库启动与停止：

```powershell
cd D:\lab
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev-mysql.ps1
# 停止时执行（保留数据）
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev-mysql.ps1 -Action stop
```

随后按 README 分别运行前后端脚本。启动脚本会在后台启动本项目 MySQL；停止命令先核对数据库实际 datadir，避免关闭其他 MySQL 实例。重复 start 会报告已运行。

本次交付时前后端预览也在后台运行，PID 记录在 `.runtime/frontend.pid` 和 `.runtime/backend.pid`。需要关闭这些预览时，运行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/stop-preview.ps1`，再按需停止数据库。脚本会核对进程归属，避免 PID 已被其他程序复用时误关。之后正式写代码时用 README 中的两个终端启动，便于直接查看日志和热更新。

数据库目录 `.runtime/mysql-data`，日志 `.runtime/mysql.log`；均不进 Git。不能把 `.runtime` 当成随便可清的缓存，里面含本机数据库和开发账号凭据。不要将运行中的 datadir 直接复制给同伴；交换测试数据应使用明确的导出或初始化脚本。

## 其他成员若也选择 ZIP 方式

默认仍建议按团队 Compose 方式启动。需要 ZIP 方式时：

1. 先运行 `scripts/setup.ps1`，准备 `.env` 和依赖。
2. 从 [MySQL 官方下载页](https://dev.mysql.com/downloads/mysql/8.4.html) 下载 Windows ZIP，核对官方校验值。
3. 解压到 `.runtime/mysql-8.4.13-winx64/`；可用 `local_mysql.py --basedir` 指定其他实际版本目录。
4. 首次执行 `python scripts/local_mysql.py init`（使用 `.venv` 解释器）；它只允许初始化空的新目录，自动设置随机 root／应用密码并启动数据库。
5. 执行 Django `migrate` 与可选 `seed_demo --create-user`。

本次下载 `mysql-8.4.13-winx64.zip`，MD5 核对为 `7b94489d5524dea9b27097068bea25a8`；来源为官方 HTTPS 下载页。后续更新版本时应重新核对来源和校验值，不能沿用旧值。

## Docker 故障现场记录

只做过正常启动、停止由本次启动的 Docker 进程、检查日志，以及将临时运行目录 `C:\Users\Lenovo\AppData\Local\Docker\run` 改名备份为 `run.stale-20261113`，再创建新的 run 目录。旧目录保留。

第二处 `docker-secrets-engine` 目录重命名失败，socket 删除也失败，保持原样。未修改其权限。Docker 仍需单独排障。可参考 [Docker 官方故障诊断](https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/)，不要把清空数据作为第一步。

另发现本机 CLI 未识别 `docker compose` 插件；已通过 Docker 安装目录内的 `docker-compose.exe` 验证 compose.yml 语法。CLI 插件发现问题与引擎启动问题是两件事；修复前使用本页 ZIP 方式。
