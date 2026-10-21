# 跳舞兰 H5 电商系统

深圳市跳舞兰科技有限公司的花艺电商网站。

以品牌官网为主体、内容平台为支撑、购物渠道为落地。

---

## 快速开始

### 一键启动（Windows）

```
双击 启动.bat
```

### 手动启动

```bash
# 1. 后端
cd backend
python -m venv .venv
.venv\Scripts\pip install -e .
copy .env.example .env          # 然后填数据库密码
.venv\Scripts\alembic upgrade head
.venv\Scripts\python seed.py
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

开发环境验证码会自动填入，不需要真实短信。

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
│   └── images/                商品图
│
├── backend/                   后端（FastAPI + PostgreSQL）
│   ├── app/                   应用代码
│   │   ├── api/               路由层
│   │   ├── services/          业务层
│   │   ├── repositories/      数据访问层
│   │   ├── models/            数据库模型
│   │   ├── schemas/           请求/响应格式
│   │   ├── adapters/          外部服务适配器
│   │   └── core/              配置、日志、异常
│   ├── tests/                 单元测试（20 个）
│   ├── alembic/               数据库迁移
│   └── static/uploads/        用户上传的文件
│
├── docs/                      文档
│   ├── index.html             文档索引
│   ├── 01-需求/               任务书、前端协作协议
│   ├── 02-技术/               工程书、前端开发方案
│   ├── 03-交付/               项目状态总结
│   └── 04-原型/               页面清单
│
├── assets/                    设计素材（原图）
│   ├── products/              商品原图
│   └── hero/                  首页大图
│
├── scripts/                   脚本
│   ├── start.ps1              启动脚本
│   ├── full_test.py           62 项全流程测试
│   ├── security_test.py       18 项安全测试
│   └── embed_luxe.py          图片内嵌工具
│
├── 启动.bat                   双击启动
├── .env.example               环境变量模板
├── .gitignore
└── README.md                  本文档
```

**目录职责：**

| 目录 | 只放什么 | 不放什么 |
|---|---|---|
| `frontend/` | 页面、JS、图片 | 后端代码、文档 |
| `backend/` | 后端代码、迁移、测试 | 前端页面、文档 |
| `docs/` | 所有文档 | 代码 |
| `assets/` | 设计原图 | 前端用的压缩图 |
| `scripts/` | 脚本 | 业务代码 |

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
| 支付 | mock | 微信/支付宝 | 未接 |
| 履约 | mock | 真实配送系统 | 未接 |
| 短信 | mock | 阿里云/腾讯云 | 空壳 |
| 缓存 | memory | Redis | 代码完整 |
| 存储 | local | 阿里云 OSS | 空壳 |

---

## 测试

```bash
# 单元测试（20 个，不需要服务）
cd backend
.venv\Scripts\python -m pytest tests/ -q

# 集成测试（需服务在跑）
cd ../scripts
python full_test.py         # 62 项全流程
python security_test.py     # 18 项安全
```

**当前结果：20/20 · 62/62 · 18/18，全部通过。**

---

## 文档

| 文档 | 内容 |
|---|---|
| [文档索引](docs/index.html) | 所有文档的入口 |
| [任务书](docs/01-需求/任务书.md) | 需求定义（最权威） |
| [工程书](docs/02-技术/工程书.md) | 技术实现 |
| [前端开发方案](docs/02-技术/前端开发方案.md) | 前端设计 |
| [前端协作协议](docs/01-需求/前端协作协议.md) | 接口约定 |
| [项目状态总结](docs/03-交付/项目状态总结.html) | 当前进度 |
| [页面清单](docs/04-原型/页面清单.html) | 21 页预览入口 |

---

## 当前状态

| 层面 | 状态 |
|---|---|
| 前端页面 | 21 页，全部完成 |
| 后端接口 | 46+ 个，全部实测通过 |
| 前后端联调 | 已打通，同端口部署 |
| 单元测试 | 20 个，全通过 |
| 全流程测试 | 62 项，全通过 |
| 安全测试 | 18 项，全通过 |
| SEO / GEO 技术层 | 已完成（21 页 meta + JSON-LD + sitemap + llms.txt） |
| 内容 | 1 篇花语（目标 75 篇） |
| 部署上线 | 未开始（等 ICP 备案） |

---

## ⚠ 这是交付演示版，不是生产站

**系统本身是完整的、可用的。** 但里面的**数据是示例数据**：

| 项目 | 状态 |
|---|---|
| 8 个商品 | 示例数据（is_demo=true），老板接手后清空重灌 |
| 配送规则 | 未配置，页面显示「待配置」 |
| 支付 | Mock，点一下"支付成功"，不真实扣款 |
| 短信 | Mock，验证码打到日志，不发真短信 |

**DEMO_MODE=true 时**，前台顶部会显示「演示环境 · 商品与配送信息为示例数据」的提示。

**为什么要这么做：** 演示数据可以编，但服务承诺（比如「2 小时达」）不能编 —— 那是虚假宣传。

**接手后的操作步骤见** → [接手清单](docs/05-交付/接手清单.md)

---

## 待办

### 需要外部申请

- [ ] ICP 备案（7–20 天，不可压缩）
- [ ] 短信签名 + 模板（1–2 天）
- [ ] 微信支付商户号（备案后才能申请）

### 需要开发

- [ ] 补 `AliyunSms.send_code`（约 20 行）
- [ ] 补 `OssStorage.save`（约 10 行）
- [ ] 新建 `WechatPayment`（约 100 行）
- [ ] 退款流程
- [ ] 物流轨迹
- [ ] 后台订单状态推进

### 需要内容

- [ ] 20 篇花语文章（现在 1 篇）
- [ ] 真实花艺摄影（现在全是 AI 图）
- [ ] 全站 meta / OG / JSON-LD
- [ ] llms.txt + sitemap.xml

---

## 环境变量

见 `.env.example`，有详细注释。

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
```

---

## 许可

私有项目，未开源。

© 深圳市跳舞兰科技有限公司
