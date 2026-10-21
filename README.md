# 跳舞兰 H5 电商系统

深圳市跳舞兰科技有限公司的花艺电商系统。

**定位：可交付的完整业务系统** —— 打通「用户下单 → 支付 → 后台履约 → 售后」全闭环，并预留 AI 智能体接入能力（MCP）。

---

## 这个项目是什么

| 维度 | 说明 |
|---|---|
| **交付形态** | 完整可运行的系统，不是演示 Demo |
| **业务闭环** | 已打通，134 项测试全通过 |
| **数据状态** | 商品/配送/联系方式为示例数据，老板接手后替换 |
| **AI 接入** | MCP Server 已就绪，9 个工具，可接千问/Claude/Cursor |
| **上线状态** | 未上线（等 ICP 备案 + 真实数据） |

**⚠ 当前 `DEMO_MODE=true`** —— 前台顶部显示「演示环境」提示，下单不会真实扣款。接手后改 `.env` 即可关闭。

---

## 快速开始

### 一键启动（Windows）

```
双击 启动.bat
```

### 手动启动

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -e .
copy .env.example .env          # 然后填数据库密码
.venv\Scripts\alembic upgrade head
.venv\Scripts\python scripts\seed.py
$env:PYTHONUTF8="1"
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 访问

| 地址 | 内容 |
|---|---|
| http://127.0.0.1:8000/ | 前台首页 |
| http://127.0.0.1:8000/shop.html | 商城 |
| http://127.0.0.1:8000/admin.html | 管理后台 |
| http://127.0.0.1:8000/docs | 接口文档 |

**后台需要管理员账号。** 首次使用：

```sql
UPDATE users SET is_admin = TRUE WHERE phone = '你的手机号';
```

开发环境验证码会自动填入（从 `/auth/send-code` 返回的 `dev_code`），不需要真实短信。

---

## 业务闭环（这是核心）

### 用户侧

```
浏览商品 → 看详情 → 查配送 → 加入购物袋 → 填地址 → 下单 → 支付 → 查订单 → 申请售后
```

### 后台侧

```
登录 → 看订单列表 → 逐单推进状态 → 处理工单 → 回复用户 → 看数据统计
```

### 订单状态机

```
待支付 ──支付──→ 已支付 ──→ 配花中 ──→ 配送中 ──→ 已送达 ──→ 已完成
   │
   └──→ 已取消
```

**白名单约束**：非法流转（跳步、回退）返回 409。

### 闭环实测

```bash
cd scripts
python test_loop.py
```

**21 项全部通过：**

| 环节 | 项数 | 内容 |
|---|---|---|
| 用户侧 | 9 | 浏览、详情、配送、下单、查单、支付、回调、状态、幂等 |
| 后台侧 | 6 | 登录、订单列表、统计、推进 4 步、非法流转拒绝 |
| 售后 | 4 | 提工单、后台可见、回复、状态变更 |

---

## 项目结构

```
跳舞兰/
│
├── frontend/                  前端（21 个页面）
│   ├── index.html             首页
│   ├── shop.html              商城
│   ├── product.html           商品详情
│   ├── cart.html              购物袋
│   ├── checkout.html          确认订单
│   ├── pay.html               支付
│   ├── order-success.html     下单成功
│   ├── login.html             登录
│   ├── orders.html            我的订单
│   ├── order-detail.html      订单详情
│   ├── address.html           地址簿
│   ├── after-sale.html        申请售后
│   ├── flower-language.html   花语百科
│   ├── flower-language-detail.html  花语详情
│   ├── about.html             关于
│   ├── contact.html           联系
│   ├── search.html            搜索
│   ├── help-delivery.html     配送范围
│   ├── help-returns.html      售后政策
│   ├── help-faq.html          常见问题
│   ├── admin.html             管理后台
│   ├── js/api.js              接口封装
│   ├── images/                商品图（WebP）
│   └── robots.txt / sitemap.xml / llms.txt
│
├── backend/                   后端（FastAPI + PostgreSQL）
│   ├── app/                   应用代码
│   │   ├── api/               路由层
│   │   ├── services/          业务层
│   │   ├── repositories/      数据访问层
│   │   ├── models/            数据库模型
│   │   ├── schemas/           请求/响应格式
│   │   ├── adapters/          外部服务适配器
│   │   ├── web/               SSR 渲染
│   │   ├── core/              配置、日志、异常
│   │   └── mcp_server.py      MCP Server（给 AI 用）
│   ├── tests/                 单元测试（20 个）
│   ├── alembic/               数据库迁移
│   ├── scripts/seed.py        灌数据
│   └── storage/uploads/       用户上传的文件
│
├── content/                   内容源文件（Markdown）
│   ├── README.md              写作规范
│   ├── 选题清单.md             75 篇选题规划
│   ├── 花语/                  7 篇
│   ├── 养护/                  3 篇
│   └── 场景/                  5 篇
│
├── docs/                      文档
│   ├── index.html             文档索引
│   ├── 01-需求/               任务书、前端协作协议
│   ├── 02-技术/               工程书、前端开发方案、MCP接入
│   ├── 03-交付/               项目状态总结、阶段总结
│   ├── 04-原型/               页面清单
│   └── 05-交付/               接手清单
│
├── assets/                    设计素材（原图）
├── scripts/                   脚本
│   ├── start.ps1              启动
│   ├── test_loop.py           业务闭环测试（21 项）
│   ├── test_mcp.py            MCP 工具测试（13 项）
│   ├── full_test.py           全流程测试（62 项）
│   ├── security_test.py       安全测试（18 项）
│   ├── audit_seo.py           SEO 综合测评
│   ├── check_crawl.py         爬虫可读性
│   ├── check_paths.py         路径可移植性
│   ├── check_perf.py          性能测评
│   ├── import_content.py      Markdown 导入
│   ├── gen_site_files.py      生成 sitemap/llms
│   ├── apply_seo.py           注入 meta
│   └── reset_demo.py          清空演示数据
│
├── 启动.bat                   双击启动
├── .env.example               环境变量模板
├── .gitignore
└── README.md                  本文档
```

---

## 技术栈

### 后端

```
FastAPI 0.150      Web 框架
Python 3.11        运行时
SQLAlchemy 2.1     ORM（async）
asyncpg            PostgreSQL 驱动
PostgreSQL 18      数据库
Alembic 1.20       迁移
Pydantic 2.14      数据校验
structlog 26.1     日志
MCP SDK 1.30       AI 智能体接入
```

### 前端

```
原生 HTML / CSS / JS    无框架、无构建
21 个页面               改完刷新就能看
```

**为什么不用框架：** 页面结构简单，原生足够。省掉 363MB 的 node_modules 和构建等待。

---

## 架构

### 三层结构

```
api/           接请求、验参数
  ↓
services/      业务逻辑、状态流转
  ↓
repositories/  只跟数据库打交道
```

### 端口-适配器

外部依赖全部抽成接口，改配置就能换：

| 能力 | 开发环境 | 生产环境 | 状态 |
|---|---|---|---|
| 支付 | mock | 微信/支付宝 | 待接入 |
| 履约 | mock | 真实配送系统 | 待接入 |
| 短信 | mock | 阿里云/腾讯云 | 骨架已写 |
| 缓存 | memory | Redis | 代码完整 |
| 存储 | local | 阿里云 OSS | 骨架已写 |

### SSR（服务端渲染）

**为什么需要：** 页面是静态 HTML + JS 渲染，搜索引擎爬虫不执行 JS，看到的是空壳。

**实测：** 改造前爬虫可读性 3/7，改造后 7/7。

**做法：** 后端给 4 个页面加 SSR 路由（商城/商品详情/花语列表/花语详情），读模板 + 查数据 + 注入内容。

**用户无感** —— JS 加载后接管交互。

---

## AI 接入（MCP）

**两层 GEO：**

| 方式 | AI 能做什么 |
|---|---|
| `llms.txt` | **读**到你的内容（被动） |
| **MCP Server** | **操作**你的系统（主动） |

### 9 个工具

| 类别 | 工具 |
|---|---|
| 查询 | `search_flowers` `get_product` `check_delivery` `list_categories` |
| 交易 | `create_order` `query_order` `create_ticket` |
| 内容 | `get_flower_meaning` `list_articles` |

### 启动

```bash
cd backend
.venv\Scripts\python.exe -m app.mcp_server
```

**接入 AI 客户端的配置见** → [MCP 接入文档](docs/02-技术/MCP接入.md)

---

## 测试

```bash
cd scripts

# 业务闭环（21 项，需服务在跑）
python test_loop.py

# 退款 + 配送（18 项，需服务在跑）
python test_refund_delivery.py

# 全流程（62 项，需服务在跑）
python full_test.py

# 安全（18 项，需服务在跑）
python security_test.py

# SEO 测评
python audit_seo.py

# MCP 工具（13 项，不需要服务）
cd ../backend && .venv\Scripts\python.exe ..\scripts\test_mcp.py

# 单元测试（20 个）
.venv\Scripts\python.exe -m pytest tests/ -q
```

**当前结果：**

```
业务闭环      21 / 21   ✓
退款 + 配送    18 / 18   ✓
MCP 工具      13 / 13   ✓
全流程        62 / 62   ✓
安全          18 / 18   ✓
单元          20 / 20   ✓
──────────────────────────
合计         152 / 152
```

**全部可重复跑。** 脚本已处理验证码限流（60 秒 1 次），
连续跑两次会自动等待，不会静默跳过测试项。

**注意：** 早期版本脚本在限流时静默跳过管理员相关测试，
导致 `full_test` 显示 50/50（而非 62/62）。
已修复，现在无论何时跑都是完整数量。

---

## SEO / GEO

| 指标 | 结果 |
|---|---|
| Lighthouse Performance | **98** |
| Lighthouse SEO | **100** |
| Lighthouse Accessibility | **100** |
| Lighthouse Best Practices | **96** |
| 爬虫可读性 | 7 / 7 |
| 结构化数据 | 12 种 schema |
| sitemap | 31 个 URL |
| llms.txt | 4.7KB |

**核心指标：**

| 指标 | 实测 | 标准 |
|---|---|---|
| FCP | 0.8s | < 1.8s |
| LCP | 2.4s | < 2.5s |
| TBT | 0ms | < 200ms |
| CLS | 0.041 | < 0.1 |
| 接口 P95 | 13–16ms | < 500ms |

---

## 内容

**15 篇已发布**（花语 7 / 养护 3 / 场景 5），71 个 FAQ。

| 类型 | 目标 | 现状 |
|---|---|---|
| 花语百科 | 30 篇 | 7 篇 |
| 养护指南 | 15 篇 | 3 篇 |
| 送花指南 | 20 篇 | 5 篇 |
| 本地内容 | 10 篇 | 0 篇（需真实配送范围） |
| 节日专题 | 按节日 | 0 篇 |

**写作规范见** → [content/README.md](content/README.md)
**选题清单见** → [content/选题清单.md](content/选题清单.md)

**导入新文章：**
```bash
cd scripts
python import_content.py
python gen_site_files.py   # 更新 sitemap
```

---

## 文档

| 文档 | 内容 |
|---|---|
| [文档索引](docs/index.html) | 所有文档的入口 |
| [阶段总结](docs/03-交付/阶段总结.html) | **对照任务书 36 项验收，含差距分析** |
| [接手清单](docs/05-交付/接手清单.md) | **老板接手操作手册** |
| [MCP 接入](docs/02-技术/MCP接入.md) | AI 客户端配置 |
| [任务书](docs/01-需求/任务书.md) | 需求定义（最权威） |
| [工程书](docs/02-技术/工程书.md) | 技术实现 |
| [前端开发方案](docs/02-技术/前端开发方案.md) | 前端设计 |
| [前端协作协议](docs/01-需求/前端协作协议.md) | 接口约定 |
| [项目状态总结](docs/03-交付/项目状态总结.html) | 完成度明细 |
| [页面清单](docs/04-原型/页面清单.html) | 21 页预览入口 |

---

## 待办

### 业务闭环补强（已全部完成）

- [x] 后台商品新增/编辑表单
- [x] 退款流程
- [x] 配送管理 + 状态映射

### 需要外部条件

- [ ] ICP 备案（7–20 天，所有上线工作的前置）
- [ ] 微信支付商户号（备案后才能申请）
- [ ] 短信签名 + 模板（1–2 天）

### 需要真实数据

- [ ] 真实商品清单（现在是 8 个示例）
- [ ] 真实配送规则（现在全部 null）
- [ ] 真实联系方式（现在全是占位）
- [ ] 真实花艺摄影（现在全是 AI 图）

### 内容

- [ ] 60 篇（花语 23 + 养护 12 + 场景 15 + 本地 10）

### 可选

- [ ] 物流轨迹
- [ ] 发票
- [ ] 数据库连接管理后台
- [ ] 数据源接入（映射层）

---

## 环境变量

见 `.env.example`，有详细注释。

**演示模式：**

```ini
DEMO_MODE=true    # 显示演示提示，下单不扣款
DEMO_MODE=false   # 正常运营
```

**生产环境必改（启动时自动检查，不合规拒绝启动）：**

```
SECRET_KEY          ≥32 位随机字符串
DEBUG               false
CORS_ORIGINS        不能含 *
CACHE_PROVIDER      redis
SMS_PROVIDER        不能是 mock
STORAGE_PROVIDER    不能是 local
PAYMENT_PROVIDER    不能是 mock
ADMIN_PHONES        必须清空
DEMO_MODE           false
```

---

## 许可

私有项目，未开源。

© 深圳市跳舞兰科技有限公司
