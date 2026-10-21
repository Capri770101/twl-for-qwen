# 跳舞兰 H5 电商系统

深圳市跳舞兰科技有限公司的花艺电商网站。

以品牌官网为主体、内容平台为支撑、购物渠道为落地，服务 100+ 家美团体系花店。

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
| 部署上线 | 未开始（等 ICP 备案） |

**详细状态见** → [项目状态总结](docs/03-交付/项目状态总结.html)

---

## 快速开始

### 环境要求

- Python 3.11
- PostgreSQL 18
- Node.js 18+（仅用于图片处理脚本，非必需）

### 启动后端

```bash
cd backend

# 1. 复制环境变量
cp .env.example .env
# 编辑 .env，填数据库密码

# 2. 装依赖
python -m venv .venv
.venv\Scripts\pip install -e .

# 3. 建表
alembic upgrade head

# 4. 灌测试数据
.venv\Scripts\python seed.py

# 5. 启动
$env:PYTHONUTF8="1"
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 访问

| 地址 | 内容 |
|---|---|
| http://127.0.0.1:8000/ | 前台首页 |
| http://127.0.0.1:8000/admin.html | 管理后台 |
| http://127.0.0.1:8000/docs | 接口文档 |

**后台需要管理员账号**。首次使用需要把手机号设为管理员：

```sql
UPDATE users SET is_admin = TRUE WHERE phone = '你的手机号';
```

开发环境验证码会自动填入，不需要真实短信。

---

## 技术栈

### 后端

```
FastAPI 0.150      Web 框架
Python 3.11        运行时
SQLAlchemy 2.1     ORM（async）
asyncpg            PostgreSQL 驱动
PostgreSQL 18      数据库
Alembic 1.20       迁移工具
Pydantic 2.14      数据校验
structlog 26.1     日志
```

### 前端

```
原生 HTML / CSS / JS    无框架、无构建
21 个页面               全部自包含（CSS 内联 + 图片 base64）
api.js                  统一请求封装
localStorage            购物袋状态
```

**为什么不用框架**：页面结构简单，原生足够。省掉构建步骤，改完刷新就能看。

---

## 项目结构

```
跳舞兰/
├── docs/                    所有文档
│   ├── index.html           文档索引（从这里进）
│   ├── 01-需求/             任务书、前端协作协议
│   ├── 02-技术/             工程书、前端开发方案
│   ├── 03-交付/             项目状态总结
│   └── 04-原型/             页面清单
│
├── prototype/luxe/          21 个页面（源文件）
│
├── backend/                 后端
│   ├── app/                 应用（三层架构）
│   │   ├── api/             路由层
│   │   ├── services/        业务层
│   │   ├── repositories/    数据访问层
│   │   ├── models/          ORM 模型
│   │   ├── schemas/         请求/响应格式
│   │   ├── adapters/        外部服务适配器
│   │   └── core/            配置、数据库、日志、异常
│   ├── static/              部署用的前端副本
│   ├── tests/               单元测试
│   └── alembic/             数据库迁移
│
├── assets/                  图片素材
│
└── gen/                     生成脚本 + 测试脚本
    ├── full_test.py         62 项全流程测试
    ├── security_test.py     18 项安全测试
    └── ...                  各种生成/修复脚本
```

**`backend/static/` 是 `prototype/luxe/` 的副本**。改页面要改 `prototype/luxe/`，然后复制过去。生产环境用 Nginx 直接托管 `prototype/luxe/` 即可。

---

## 架构

### 三层结构

```
api/          路由层：接请求、验参数、调 Service
  ↓
services/     业务层：业务逻辑、状态流转、事务边界
  ↓
repositories/ 数据访问层：只负责跟数据库打交道
```

**为什么要分三层**：业务逻辑不掺 SQL，换数据库只改一层，能单独测业务。

### 端口-适配器

外部依赖全部抽成接口，可切换实现：

| 能力 | 开发环境 | 生产环境 | 状态 |
|---|---|---|---|
| 支付 | mock（模拟收银台） | 微信/支付宝 | 未接 |
| 履约 | mock（本地流转） | 真实配送系统 | 未接 |
| 短信 | mock（验证码打日志） | 阿里云/腾讯云 | 空壳 |
| 缓存 | memory（进程内存） | Redis | 代码完整 |
| 存储 | local（本地磁盘） | 阿里云 OSS | 空壳 |

**切换方式**：改 `.env` 里的配置项，不改代码。

---

## 测试

```bash
# 单元测试（20 个）
cd backend
.venv\Scripts\python -m pytest tests/ -v

# 全流程测试（62 项，需服务在跑）
cd gen
python full_test.py

# 安全测试（18 项，需服务在跑）
python security_test.py
```

**当前结果**：20/20 · 62/62 · 18/18，全部通过。

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
- [ ] 后台订单状态推进（接口有，前端未接）

### 需要内容

- [ ] 20 篇花语文章（现在 1 篇）
- [ ] 真实花艺摄影（现在全是 AI 图）
- [ ] 全站 meta / OG / JSON-LD
- [ ] llms.txt + sitemap.xml

---

## 环境变量

见 `backend/.env.example`，有详细注释。

**生产环境必改项**（启动时会自动检查，不合规拒绝启动）：

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
