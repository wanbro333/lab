# 采购批准与确认入库

本阶段已接入正式后端：管理员批准采购单，再确认收货单入库。每条收货明细生成一个库存批次和一笔入库流水。保存收货草稿不会增加库存。

## 1. 代码写在哪里

| 文件 | 用途 |
| --- | --- |
| [inventory/models.py](../backend/apps/inventory/models.py) | `StockBatch` 库存批次、`StockMovement` 库存流水 |
| [procurement/models.py](../backend/apps/procurement/models.py) | 采购单批准人/时间、收货单确认人/时间、自定义权限 |
| [procurement/services.py](../backend/apps/procurement/services.py) | `approve_purchase_order()`、`post_receipt()` 两个业务入口 |
| [procurement/admin.py](../backend/apps/procurement/admin.py) | 后台批准、确认入库操作，以及单据编辑权限和锁 |
| [procurement/forms.py](../backend/apps/procurement/forms.py) | 收货明细表单校验 |
| [inventory/admin.py](../backend/apps/inventory/admin.py) | 库存批次和流水的只读后台 |
| [procurement/test_posting.py](../backend/apps/procurement/test_posting.py) | 正常流程、权限、回滚、重复及并发测试 |

数据库结构的变更记录在 `inventory/migrations/0003_stockbatch_stockmovement_and_more.py` 和 `procurement/migrations/0005_alter_purchaseorder_options_alter_receipt_options_and_more.py`。Django 会根据依赖先执行采购模块的迁移，再创建库存表。已经执行过的旧迁移不需要删除或重写。

## 2. 库存批次的每个字段

批次表示一批实物当前放在哪里、剩下多少。厂家批号可以重复；系统的内部批次号不能重复。

| 字段 | 意义 |
| --- | --- |
| `id` | Django 自动生成的主键，用于数据库关联 |
| `code` | 唯一内部批次号；服务按收货明细 ID 生成，例如 `B0000000001` |
| `item` | 指向物品档案的外键，说明是什么物品 |
| `location` | 指向库位的外键，说明存放在哪里 |
| `receipt_line` | 指向来源收货明细的一对一关系，一条明细最多生成一个批次 |
| `unit` | 入库时计量单位的快照；数量按这个单位解释 |
| `manufacturer_batch_no` | 厂家批号，可以留空，同一厂家批号可以分多次到货 |
| `manufactured_on` | 生产日期，可以为空 |
| `expires_on` | 有效期至，可以为空；不能早于生产日期 |
| `quantity` | 当前在库数量，用两位小数保存，数据库禁止负数 |
| `created_at` / `updated_at` | 创建时间和最后更新时间，由 Django 自动维护 |

`ForeignKey` 表示多条记录可以指向同一个对象，例如多个批次都属于同一物品。`OneToOneField` 额外保证来源唯一，重复插入相同收货明细会被数据库拒绝。

`on_delete=models.PROTECT` 让 Django 拒绝删除仍被引用的来源对象，保护历史关联。`related_name` 是反向查询名称，例如 `item.stock_batches.all()` 查询某物品的批次，`receipt_line.stock_batch` 获取该明细的批次。数据库实际保存的是 `item_id`、`location_id` 等关联主键。

## 3. 库存流水的每个字段

流水记录一次库存变动；批次保存当前余额。以后发生出库时，应该追加新流水并更新余额，不能修改旧流水来代替新的业务事件。

| 字段 | 意义 |
| --- | --- |
| `id` | 自动主键，标识这笔流水 |
| `batch` | 外键，指向这次发生变动的库存批次 |
| `receipt_line` | 一对一指向来源收货明细，防止同一来源重复记账 |
| `kind` | 变动类型，本阶段只支持 `receipt`，即采购入库 |
| `quantity_change` | 本次增加的数量；当前入库类型必须大于零 |
| `posted_by` | 外键，指向执行确认入库的用户 |
| `posted_at` | 业务记账时间；同张收货单的流水使用同一个确认时间 |

例如采购 10 瓶，第一次收 6 瓶、第二次收 4 瓶：分别确认两张收货单后，得到两个批次（6、4）和两笔流水（+6、+4），批次数量合计为 10。

当前模型只开放采购入库。出库、归还和冲销需要新增来源关联及对应约束，不能仅增加一个类型名称就直接使用。

## 4. 确认入库的事务如何工作

`post_receipt(receipt_id, actor)` 中的 `@transaction.atomic` 把整张收货单的操作包在一个事务里：所有明细、批次、流水和状态全部成功才提交；中途出现异常，已经写入的部分全部回滚。

执行顺序如下：

1. 检查操作人处于启用状态，具有后台访问资格以及确认入库、修改收货单的权限。
2. 用 `select_for_update()` 锁住采购单父记录，再锁收货单。后续明细、库位按固定顺序锁定。
3. 如果收货单已入库，直接返回“未重复处理”，不会再次生成库存。
4. 检查收货单为草稿、采购单已批准，且存在收货明细。
5. 重新验证明细字段、采购明细归属、库位启用状态和有效期。
6. 按采购明细汇总本单实收数量，并查询以前已经入库的数量。其他草稿不计入已入库数量。
7. 保证“历史已入库 + 本次实收”不超过采购数量。
8. 为每条明细创建批次，再创建对应正数入库流水。
9. 将收货单状态改为已入库，记录确认人和确认时间。
10. 正常退出函数时提交事务；异常退出时回滚。

`atomic` 解决“写到一半出错”；行锁解决“两个请求同时操作”。两个收货单若属于同一采购单，会争用同一个采购单行锁。第二个请求必须等待第一个提交，再重新计算已入库数量，避免采购 10 瓶却同时收进 6 + 6 瓶。

后台修改草稿也遵循同样的父记录加锁顺序；采购单批准后、收货单入库后，后台禁止修改其单头和明细。收货单保存后固定所属采购单。库存批次和流水仅允许查看。

每个后台批量操作中的单据拥有独立事务：一张失败不会撤销其他已成功单据，后台逐张显示结果。以后增加 API 时，应复用这些服务与加锁约定；直接使用 ORM `update()` 或手写 SQL 绕过入口，不会自动获得这些业务保护。

## 5. 批准和确认人字段

`PurchaseOrder.approved_by`、`approved_at` 记录批准人和时间；`Receipt.posted_by`、`posted_at` 记录确认入库的人和时间。草稿时这些字段为空，成功操作后由服务写入，后台不可手工填写。

`received_by` 是收货登记人，可能与最终确认入库人不同。收货单有数据库约束：已入库必须同时有确认人和时间，其他状态必须保持两者为空。

采购批准采用本阶段的管理员单级审批：草稿或待审批单可以批准；没有采购明细的单据不能批准。完整多级审批和审批历史表留待后续实现。

## 6. 在后台实际操作

启动数据库、后端后，打开 [管理后台](http://127.0.0.1:8000/admin/)。

1. 在「采购单」中填写单据和明细，保存。
2. 回到采购单列表，勾选单据，在操作下拉框选择「批准所选采购单（单级审批）」，执行。
3. 在「收货单」中选择对应采购单，填写收货明细、库位、数量及批号日期，保存草稿。
4. 回到收货单列表，勾选单据，选择「确认所选收货单入库」，执行。
5. 到「库存批次」「库存流水」查看新增记录。

超级管理员具备操作权限。普通后台人员除了查看及录入所需的模型权限，还需要 `procurement.approve_purchaseorder` + `procurement.change_purchaseorder` 才能批准，`procurement.post_receipt` + `procurement.change_receipt` 才能确认入库；库存查询需要对应的查看权限。

如果发生超量、库位停用、过期或未批准等问题，后台会显示错误，该张单据仍为草稿。确认入库前可修正明细；已入库不能通过删除或修改来撤回，冲销功能尚未实现。

## 7. 迁移、测试和团队同步

拉取包含本次改动的代码后，在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe backend\manage.py check --database default
.\.venv\Scripts\python.exe backend\manage.py migrate --plan
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py test apps --settings=config.settings_test
```

迁移文件已经包含在项目里，团队成员只需 `migrate`，不用重复生成。模型再次改变时，才运行 `makemigrations` 并将新迁移一起提交。

2026-11-14 验证：正式项目代码在独立 MySQL 8.4 测试库运行 32 项测试全部通过，包含两个真实多连接并发测试。SQLite 快速测试通过 30 项，明确跳过两项行锁测试。GitHub Actions 现有 MySQL 作业会运行全部测试。本机业务数据库不应直接当测试库；测试需要独立库及相应的建库权限。

Vue 列表和现有物品接口的 `Item.quantity` 仍是旧台账字段，本次入库不更新它。当前以「库存批次」的数量为新流程库存依据；后续需要先处理旧台账的期初数据，再将前端切到批次汇总接口。不要把两套数量直接相加，以免重复计算。
