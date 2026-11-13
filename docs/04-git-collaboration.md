# Git 与 GitHub 协作：从第一次提交到并行开发

以下命令在 PowerShell 中执行。`D:\lab` 是负责人电脑的目录，新成员可以使用自己的路径。

## 1. 先分清六个概念

| 名称 | 可以怎样理解 |
| --- | --- |
| 工作区 | 当前磁盘上正在编辑的文件 |
| 暂存区 | 下一次准备提交的内容；`git add` 放进这里 |
| commit | 一次本地版本快照，还没有上传 GitHub |
| branch | 一条有名称的开发线，可独立修改再合并 |
| origin | GitHub 远端仓库的本地简称 |
| Pull Request / PR | 请求把一个分支的改动审查并合入另一个分支；不是 `git pull` |

最常见路径：**改文件 → add → commit → push → 创建 PR → 审查 → merge**。

本项目采用 `main + 功能分支`。`main` 保持可运行；每个人每项任务开一个短期分支，不按人长期积累一个大分支。

## 2. 负责人：首次发布本地基础工程

这次没有自动推送 GitHub。交付时本地有一个最小 `main` 基线和 `chore/project-scaffold` 基础工程分支；完整代码在后者。先检查：

```powershell
cd D:\lab
git status
git branch
git log --oneline --all --graph
git remote -v
```

远端在搭建时为空。发布前重新 `git ls-remote origin`；若同伴已经创建远端历史，先协调，不强制覆盖。

远端仍为空时执行：

```powershell
git push -u origin main
git push -u origin chore/project-scaffold
```

`-u` 建立本地分支与远端分支的跟踪关系，以后在该分支直接 `git push` 即可。HTTPS 推送可能弹出 Git Credential Manager 的浏览器登录；使用 GitHub 授权，不在聊天或代码中粘贴 token。GitHub 账号密码不能直接当 Git HTTPS 密码使用。

打开 [仓库](https://github.com/wanbro333/lab)，点击 **Compare & pull request**，确认：

- base：`main`，即希望合入的目标。
- compare：`chore/project-scaffold`，即完整基础工程。
- 标题建议：`搭建 Vue + Django + MySQL 实验室基础工程`。
- 正文写已实现范围、怎么启动、测试结果；模板会自动出现。

先查看 **Files changed** 和 **Checks**，再请一名成员 Review。没有云端运行记录时不能把本地测试当作 Actions 已通过。小组可选 **Squash and merge** 合并；合并后同步本地：

```powershell
git switch main
git pull --ff-only origin main
```

若以后用 Squash 合并，源分支的提交 ID 不一定是 main 的祖先，`git branch -d` 可能拒绝删除。这不代表功能没合并；可先保留分支，经核对远端 PR 和内容后再清理，不急于强制删除。

## 3. 邀请成员并保护主分支

在 GitHub 仓库 Settings 的 Collaborators 页面邀请成员，他们接受后可推送自己的分支。每人使用自己的账号，不共享负责人密码。

在仓库支持的分支保护／Rulesets 设置中，针对 `main` 建议要求：PR 合并、另一人批准、CI 的 `frontend` 与 `backend` 检查通过、解决讨论。先让 CI 至少成功运行一次再选择对应检查名称。这些设置需要仓库管理员操作，本次没有代为修改。

保护规则的可用性可能受仓库可见性与 GitHub 方案影响；若界面不提供，团队仍按 PR 流程执行，不声称仓库已强制保护。

## 4. 成员：开始第一项任务

首次克隆与配置身份：

```powershell
git clone https://github.com/wanbro333/lab.git
cd lab
git config user.name "你的名字"
git config user.email "你的GitHub提交邮箱"
```

这只设置当前仓库的提交署名，不是登录。邮箱可用 GitHub 提供的 noreply 地址。按启动文档安装自己的环境，每个人都有自己的数据库和 `.env`。

开始任务：

```powershell
git switch main
git pull --ff-only origin main
git switch -c feat/inventory-detail
```

例如给物品增加详情页。改完后先检查，再选择相关文件暂存：

```powershell
git status
git diff
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
# 下列路径是示例，用你的真实改动路径替换
git add frontend/src/views/InventoryView.vue
git diff --staged
git commit -m "feat(inventory): add item detail entry"
git push -u origin feat/inventory-detail
```

`git diff` 查看尚未暂存的改动，`git diff --staged` 查看此次 commit 的内容。不要不看状态就把无关文件全部加入。

到 GitHub 建 PR，选择 base `main`、compare 自己的分支。还没完成但希望同伴早看，可创建 **Draft PR**。审查提出修改后，在同一分支继续 `add → commit → push`，原 PR 会自动更新，不需要另建 PR。

## 5. 多人怎样真正并行

例如：

| 成员 | 分支 | 主要文件 | 先协调的内容 |
| --- | --- | --- | --- |
| A | `feat/inventory-detail` | inventory 后端／接口 | 详情接口字段 |
| B | `feat/procurement-ui` | views/procurement、api/procurement.js | 采购接口约定与占位数据标识 |
| C | `feat/receipts-api` | apps/receipts | 采购单状态和入库事务 |
| D | `docs/acceptance` | docs、验收用例 | 各功能完成标准 |

大家各自在自己的电脑克隆，不共享一个工作目录；分支也不等于复制一套数据库。优先按模块分工，避免两人同时大量改 App.vue、router、settings、同一迁移或锁文件。

在写页面和后端之前，先把接口路径、请求字段、返回样例、错误状态写到同一个 Issue 或 `docs/05-api.md`。前端可用明确标注的模拟数据推进，但合并前验证真实接口。

同伴的 PR 合并后，在自己的功能分支同步主线：

```powershell
# 先确保工作区干净，或先提交自己的工作
git fetch origin
git merge origin/main
# 处理冲突／重新验证后
git push
```

`fetch` 只更新本地看到的远端信息；`merge origin/main` 才把最新主线合入当前功能分支。初学阶段优先使用 merge，避免在共享分支上 rebase 和 force push。

## 6. 冲突处理示范

出现冲突后运行 `git status`，打开冲突文件：

```text
  <<<<<<< HEAD
  当前分支内容
  =======
  主线内容
  >>>>>>> origin/main
```

与同伴确认两边意图，编辑成最终应该保留的内容，删除三个冲突标记，然后：

```powershell
git add 发生冲突的文件路径
git commit
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
git push
```

暂时无法判断时可 `git merge --abort` 回到合并前，再协调。它用于取消正在进行的 merge；不要把它当成日常清空改动的命令。

**Django 迁移冲突**：两个分支都给同一 app 新增了同号迁移时，先检查数据库变更语义；兼容的分支可用 `makemigrations --merge` 生成合并迁移，再迁移和测试。不要删除已被他人执行的迁移去“重新来过”。

**锁文件冲突**：先合并依赖清单，再用包管理器重新生成锁文件并测试，不逐行猜测 npm 锁文件内容。

## 7. 临时切任务与常见恢复

```powershell
# 临时保存未提交工作（-u 包含未跟踪文件，但不包含忽略的 .env）
git stash push -u -m "正在做库存详情"
git switch main
# 回来继续
git switch feat/inventory-detail
git stash pop
```

`stash pop` 也可能冲突，需要处理。多个任务长期并行时，可用独立 worktree；每个 worktree 的 `.env`、依赖、端口和数据库要独立配置，基础阶段不必急着用。

| 目的 | 命令与注意点 |
| --- | --- |
| 查看最近提交 | `git log --oneline -8` |
| 取消某文件暂存，保留编辑 | `git restore --staged 文件路径` |
| 撤销已共享的提交 | `git revert 提交ID`，生成一条反向提交，再走 PR |
| push 被拒绝 | 先 `git fetch` 查看远端变化；不要立即 `--force` |
| pull 拒绝快进 | 检查当前分支和本地独有提交，协调后合并；不直接重置 |
| `.env` 不显示在 status | 正常，被忽略；用 `git check-ignore .env` 验证 |

`git restore 文件` 会丢弃该文件未提交的编辑；`reset --hard` 会丢工作区改动。初学阶段无需用它们解决一般同步问题。

## 8. 一次可以照着做的小练习

基础工程 PR 合并后，从 main 新建 `docs/your-name-onboarding`，在团队文档补充一条你实际完成的启动验证，提交、推送并开 PR。让另一位成员审查；他提出一条修改，你在同分支追加一次提交；检查通过后合并，再同步 main。这样能完整练习协作而不影响业务逻辑。

参考：[GitHub Flow 官方说明](https://docs.github.com/en/get-started/using-github/github-flow)、[创建 Pull Request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request)。
