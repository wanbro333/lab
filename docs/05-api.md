# 基础 API 约定

开发时前端只访问相对地址 `/api/...`，由 Vite 代理。所有路径保留末尾 `/`。请求正文为 JSON，文本 UTF-8，日期 `YYYY-MM-DD`，数量使用十进制字符串。

## 已实现接口

| 方法 | 路径 | 权限与结果 |
| --- | --- | --- |
| GET | `/api/health/` | 公开；连接数据库执行 SELECT 1，成功 200，数据库不可用 503 |
| GET | `/api/auth/csrf/` | 公开；设置 CSRF Cookie，返回 `csrfToken` |
| GET | `/api/auth/me/` | 返回当前登录状态，未登录也是 200 |
| POST | `/api/auth/login/` | CSRF 必需；用户名与密码，成功建立 Session |
| POST | `/api/auth/logout/` | CSRF 必需；销毁当前 Session |
| GET | `/api/inventory/items/` | 需要登录；查询列表 |
| POST | `/api/inventory/items/` | 登录且 `is_staff`；新增物品，成功 201 |

没有实现的接口不要自行在前端假定为可用。更新／删除、领用／归还、采购、收货、AI 接口留待对应任务设计。

## 登录及 Cookie

```json
{"username": "你自己的账号", "password": "你自己的密码"}
```

`me` 和成功登录返回：

```json
{"authenticated": true, "user": {"username": "lab_dev", "display_name": "开发管理员", "is_staff": true}}
```

未登录返回 `{"authenticated": false, "user": null}`。所有写请求携带 `X-CSRFToken` 与同源 Cookie；登录会轮换 CSRF token，所以客户端在每次写操作前重新获取。项目已在 `api/client.js` 封装，不在业务组件里重复实现。

## 物品查询

可选参数：`kind=equipment|material`、`q=关键词`、`page=正整数`。类型为空表示全部；搜索名称／编号／位置；每页固定 20 条，超出末页返回空列表，不回退到第一页。

```json
{
  "count": 1,
  "page": 1,
  "page_size": 20,
  "results": [{
    "id": 1, "code": "EQ-001", "name": "示波器", "kind": "equipment",
    "specification": "100 MHz", "unit": "台", "quantity": "2.00",
    "location": "A101", "expires_on": null
  }]
}
```

## 新增物品

```json
{
  "code": "MT-001", "name": "实验用线", "kind": "material",
  "specification": "20 cm", "unit": "根", "quantity": "12.50",
  "location": "A102 / 材料柜", "expires_on": null
}
```

必填：code、name、kind、unit、quantity。quantity 范围为 0 至 99999999.99，最多两位小数。code 唯一；器材不允许设置 expires_on。成功返回创建后的完整对象，包含 id。

## 错误处理

| 状态 | 含义 |
| --- | --- |
| 400 | JSON、字段或查询参数不合法 |
| 401 | 未登录／登录凭据不正确 |
| 403 | 没有写入权限或 CSRF 失败 |
| 409 | 并发写入造成编号冲突；普通重复编号通常在 Form 阶段返回 400 |
| 405 | 方法不支持；由 Django 返回，前端需容忍非 JSON 错误体 |
| 503 | 健康检查发现数据库不可用 |

字段错误示例：

```json
{"message":"请检查输入内容。","errors":{"quantity":[{"message":"确保该值大于或等于0。","code":"min_value"}]}}
```

不要依赖错误中文的精确字面值判断逻辑；按 HTTP 状态和字段错误码处理。基础版尚未提供统一业务错误码、登录限流和版本化 `/api/v1/`；涉及公开部署或接口升级时统一设计。
