# 后端

跳舞兰 H5 的 API 服务。FastAPI + PostgreSQL。

---

## 结构

```
backend/
├── app/                        应用代码
│   ├── main.py                 入口
│   ├── api/                    路由层
│   │   ├── deps.py             依赖注入（认证、数据库会话）
│   │   └── v1/                 接口实现
│   │       ├── router.py       路由汇总
│   │       ├── auth.py         认证
│   │       ├── addresses.py    地址簿
│   │       ├── products.py     商品
│   │       ├── orders.py       订单
│   │       ├── payments.py     支付
│   │       ├── tickets.py      售后
│   │       ├── deliveries.py   配送
│   │       ├── articles.py     花语文章
│   │       ├── settings.py     配置
│   │       ├── uploads.py      文件上传
│   │       └── admin.py        后台
│   ├── services/               业务层
│   │   ├── auth_service.py     验证码 / token / 限流
│   │   ├── address_service.py  地址增删改查
│   │   ├── product_service.py  商品
│   │   ├── order_service.py    订单 + 状态机
│   │   ├── payment_service.py  支付
│   │   ├── ticket_service.py   售后 + 配送
│   │   ├── content_service.py  文章 + 配置
│   │   └── order_task.py       订单超时自动取消
│   ├── repositories/           数据访问层
│   │   ├── base.py             通用 CRUD
│   │   ├── product_repo.py
│   │   ├── order_repo.py
│   │   ├── payment_repo.py
│   │   └── ticket_repo.py
│   ├── models/                 ORM 模型（数据库表）
│   │   ├── product.py          商品
│   │   ├── order.py            订单 + 明细 + 日志
│   │   ├── payment.py          支付 + 配送
│   │   ├── ticket.py           售后工单
│   │   ├── user.py             用户 + 地址
│   │   └── content.py          文章 + 配置
│   ├── schemas/                请求/响应格式（Pydantic）
│   ├── web/                    服务端渲染（SSR）
│   │   ├── render.py           渲染函数
│   │   └── routes.py           4 个 SSR 路由
│   ├── mcp_server.py           MCP Server（给 AI 智能体用）
│   ├── adapters/               外部服务适配器
│   │   ├── payment/            支付网关
│   │   ├── fulfillment/        履约系统
│   │   ├── sms/                短信服务
│   │   ├── cache/              缓存
│   │   └── storage/            文件存储
│   └── core/                   基础设施
│       ├── config.py           配置
│       ├── database.py         数据库连接
│       ├── logging.py          日志
│       ├── exceptions.py       异常处理
│       └── request_log.py      请求日志 + 脱敏
│
├── tests/                      单元测试（20 个）
│   └── test_core_logic.py
│
├── alembic/                    数据库迁移
│   ├── env.py
│   └── versions/
│
├── scripts/                    后端脚本
│   └── seed.py                 灌商品数据（有就更新，没有就新增）
│
├── storage/                    运行时数据
│   └── uploads/                用户上传的图片
│
├── .venv/                      虚拟环境（不提交）
├── .env                        环境变量（不提交，有密码）
├── .env.example                模板
├── alembic.ini                 迁移配置
├── pyproject.toml              依赖和打包
└── README.md                   本文档
```

---

## 关于 `.venv`

**放在 `backend/` 里是对的。**

原因：
- `backend/` 有 `pyproject.toml`，是一个独立的 Python 包
- 虚拟环境就是给这个包装依赖的
- 换项目不会冲突

**其他位置都不合适：**
- 项目根 `/.venv` —— 根目录不是 Python 项目
- 全局环境 —— 项目之间会冲突

**注意：** `.venv` 在 `.gitignore` 里，不进仓库。复制项目到别的机器要重建。

---

## 快速开始

```bash
cd backend

# 1. 建虚拟环境
python -m venv .venv
.venv\Scripts\pip install -e .

# 2. 配环境变量
copy .env.example .env
# 编辑 .env，填数据库密码

# 3. 建表
.venv\Scripts\alembic upgrade head

# 4. 灌数据
.venv\Scripts\python scripts\seed.py

# 5. 启动
$env:PYTHONUTF8="1"
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**或者从项目根目录：**

```bash
.\启动.bat
```

---

## 接口

启动后访问 `http://127.0.0.1:8000/docs` 看完整接口文档（能直接点着测）。

**46+ 个接口，分 11 组：**

| 组 | 接口数 | 说明 |
|---|---|---|
| 认证 | 4 | 发码/登录/查我/退出 |
| 地址簿 | 5 | 增删改查 + 设默认 |
| 商品 | 7 | 列表/详情/分类/筛选/后台 CRUD |
| 订单 | 5 | 建单/查单/列表/取消/状态推进 |
| 支付 | 4 | 创建/回调/记录/模拟收银台 |
| 售后 | 3 | 提交/查询/回复 |
| 配送 | 3 | 推送履约/回调/查询 |
| 花语 | 6 | 列表/详情/后台 CRUD |
| 配置 | 2 | 读写配送规则 |
| 上传 | 1 | 图片上传 |
| 后台 | 4 | 统计/订单/商品/日志 |

---

## 数据库

**PostgreSQL 18。**

11 张表：

```
products          商品
users             用户（含 is_admin）
addresses         地址簿
orders            订单主表
order_items       订单明细
order_logs        状态流转日志
payments          支付记录
deliveries        配送单
tickets           售后工单
articles          花语文章
settings          系统配置
```

迁移用 Alembic：

```bash
alembic revision --autogenerate -m "说明"
alembic upgrade head
alembic downgrade -1        # 回退一步
```

---

## 脚本

### `scripts/seed.py` —— 灌商品数据

```bash
.venv\Scripts\python scripts\seed.py
```

**行为：按 ID 查，有就更新、没有就新增（upsert）**

不会删除重建，因为订单表引用了商品 ID。

可以重复跑，结果一致。

---

## 测试

```bash
# 单元测试（20 个，不连数据库）
.venv\Scripts\python -m pytest tests/ -v

# 集成测试（需服务在跑）
cd ..\scripts
python full_test.py         # 62 项全流程
python security_test.py     # 18 项安全
```

---

## MCP Server（给 AI 用）

**9 个工具，让 AI 智能体直接操作业务。**

```bash
.venv\Scripts\python.exe -m app.mcp_server
```

| 类别 | 工具 |
|---|---|
| 查询 | `search_flowers` `get_product` `check_delivery` `list_categories` |
| 交易 | `create_order` `query_order` `create_ticket` |
| 内容 | `get_flower_meaning` `list_articles` |

**协议验证：**
```
initialize  ✓ server: tiaowulan 1.30.0, protocol 2024-11-05
tools/list  ✓ 9 个工具
```

### 一个必须知道的坑

**MCP 里没有 `get_db` 依赖，写操作必须手动 `commit`。**

```python
async with AsyncSessionLocal() as db:
    svc = order_service.OrderService(db)
    order = await svc.create_order(payload)
    await db.commit()   # ← 必须，否则数据不落库
```

**原因：** service 层只 `flush` 不 `commit`；commit 是 `get_db` 依赖在 FastAPI 请求结束时做的。MCP 不走 FastAPI，所以没人提交。

**完整接入文档见** → `docs/02-技术/MCP接入.md`

---

## 环境变量

见 `.env.example`，每一项都有注释。

**生产环境必改**（启动时自动检查，不合规拒绝启动）：

```
SECRET_KEY           ≥32 位随机串
DEBUG                false
CORS_ORIGINS         不能含 *
CACHE_PROVIDER       redis
SMS_PROVIDER         不能 mock
STORAGE_PROVIDER     不能 local
PAYMENT_PROVIDER     不能 mock
ADMIN_PHONES         必须清空
```

---

## 关键设计

### 订单状态机

```
pending_payment  待支付
  ├→ paid        已支付
  │   ├→ preparing   配花中
  │   │   ├→ delivering  配送中
  │   │   │   └→ delivered  已送达
  │   │   │       └→ completed  已完成
  │   │   └→ cancelled
  │   └→ cancelled
  └→ cancelled
```

**白名单约束**（`services/order_service.py::TRANSITIONS`），非法流转返回 409。

每次流转写 `order_logs`，可追溯。

### 库存防超卖

下单时用 `SELECT FOR UPDATE` 锁行，再扣减。两个人同时买最后一个不会超卖。

### 支付幂等

同一订单已支付时，再次创建支付返回 409，不会重复扣钱。

### 订单超时

后台任务每 60 秒扫一次，`expire_at < now` 且仍待支付的订单自动取消并释放库存。

### 验证码

- 存缓存层（开发=内存，生产=Redis）
- 5 分钟有效
- 只能用一次
- 试错 5 次作废
- 三重限流：手机号间隔 60s / 日限 10 / IP 时限 20

### Token

HMAC-SHA256 签名，格式 `user_id.expire.sig`。

无状态，但支持黑名单 —— 退出登录后立即失效。

---

## 静态资源托管

**后端负责提供前端页面和用户上传的文件。**

```
http://127.0.0.1:8000/                 → frontend/index.html
http://127.0.0.1:8000/shop.html        → frontend/shop.html
http://127.0.0.1:8000/js/api.js        → frontend/js/api.js
http://127.0.0.1:8000/images/xx.png    → frontend/images/xx.png
http://127.0.0.1:8000/uploads/xx.png   → backend/storage/uploads/xx.png
http://127.0.0.1:8000/api/v1/...       → 接口
```

**挂载顺序**（`main.py` 末尾）：

```python
app.mount("/uploads", ...)   # 先挂子路径
app.mount("/", ...)          # 再挂兜底
```

**部署时**可以用 Nginx 直接托管前端，后端只提供 `/api` 和 `/uploads`。

---

## 部署

```bash
# 生产环境
APP_ENV=production
DEBUG=false

# 用 gunicorn（Linux）或 waitress（Windows）
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Nginx 反代：**

```nginx
server {
    listen 443 ssl http2;
    server_name h5.tiaowulan.com;

    # 前端静态文件（直接托管，不经过后端）
    location / {
        root /var/www/twl/frontend;
        try_files $uri $uri/ /index.html;
    }

    # 后端接口
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 用户上传的文件
    location /uploads/ {
        alias /var/www/twl/backend/storage/uploads/;
    }
}
```

**生产环境注意：**

- 关掉 `/docs`（在 `main.py` 里判断 `settings.DEBUG`）
- 配日志采集（`LOG_FORMAT=json`）
- 配数据库备份
- 配监控告警（健康检查 `/health`）
