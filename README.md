# 跳舞兰 H5 电商系统

深圳市跳舞兰科技有限公司的花艺电商系统。

**定位：可交付的完整业务系统** —— 打通「用户下单 → 支付 → 后台履约 → 售后」全闭环，并预留 AI 智能体接入能力（MCP）。

---

## 这个项目是什么

| 维度 | 说明 |
|---|---|
| **交付形态** | 完整可运行的系统，不是演示 Demo |
| **业务闭环** | 已打通，152 项测试全通过（含退款 + 配送管理） |
| **后端规模** | 54 个接口 / 45 个路由 / 13 张表（含退款表 refunds） |
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

启动器依次完成：虚拟环境 → 依赖包 → `.env` → 数据库连通性 → 端口接管 → 起 uvicorn → 等端口就绪后自动开浏览器。
任一步失败会直接告诉你错在哪、该怎么补，不会黑屏闪退。

可选参数（在项目根目录调 PowerShell）：

| 参数 | 作用 |
|---|---|
| `-Check` | 只做环境自检，不启动服务 |
| `-NoBrowser` | 不自动打开浏览器 |
| `-Reload` | 开热重载（开发用） |
| `-Port 8001` | 换端口 |

```powershell
.\scripts\start.ps1 -Check
```

#### 编码约定（中文不乱码的前提）

| 文件 | 必须保存为 | 原因 |
|---|---|---|
| `scripts\*.ps1` | UTF-8 **with BOM** | Windows PowerShell 5.1 对「UTF-8 无 BOM」的 .ps1 按系统代码页（简体中文 = GBK/936）解码，中文会变成 `璺宠垶鍏?` 这类乱码 |
| `启动.bat` | **纯 ASCII，无 BOM** | cmd.exe 会把 BOM 字节当命令执行；且 GBK 代码页下解析 UTF-8 中文必乱。中文提示一律写在 `start.ps1` 里 |

改完脚本跑一次校验：

```powershell
.\scripts\check-encoding.ps1
```

启动链还会把 `chcp 65001`、`[Console]::OutputEncoding`、`PYTHONUTF8`、`PYTHONIOENCODING` 全部对齐到 UTF-8，
所以 uvicorn / structlog 打到控制台的中文日志也是正常的。

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
├── frontend/                  前端（22 个页面 = 21 交付页 + 1 动效自检页）
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
│   ├── 02-技术/               工程书、首页改版说明、前端开发方案、MCP接入、第三方接入说明

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
22 个页面               改完刷新就能看
```

**为什么不用框架：** 页面结构简单，原生足够。省掉 363MB 的 node_modules 和构建等待。

#### 动效层

| 文件 | 作用 |
|---|---|
| `css/motion.css` | 动效样式：整页淡入、滚动入场、按钮按压、导航下划线、卡片抬升、图片淡入、购物袋弹跳、骨架屏，以及各页面的专项动效 |
| `js/motion.js` | 动效运行时：滚动入场（可重复触发）、图片淡入、数字滚动、动态内容自动接管 |

两个文件都由脚本批量注入到全部页面，无需手动维护引用。另有 `favicon.svg`（品牌图标，白底近黑的跳舞兰花形）。

**滚动入场 · 丝滑感从哪来（三个技巧叠加）：**

1. **三属性不同时长** —— `transform` 1200ms 最慢，`opacity` / `filter` 900ms。位置慢慢落定、显形先完成，形成惯性拖尾。
2. **透明度延迟 120ms 起步** —— 位移先动、显形后跟，内容是「从雾里浮上来」而不是「原地变清晰」。
3. **缓动用 quart-out** `cubic-bezier(.22, 1, .36, 1)` —— expo-out 前 15% 时间就跑完 60% 位移，看着像「啪一下到位」；quart 慢一档，过程看得见。

幅度为 88px + `scale(.92)` + `blur(9px)`，手机端收到 64px / `scale(.94)` / `blur(6px)`。

**可重复触发：** 元素滚出视口后回到未入场状态，滚回来重新播。

- 重置必须等元素**完全离开视口**，不能靠 `rootMargin` 判可见 —— 否则元素卡在视口顶部边缘时会被摘掉 `.in`，用户看着内容消失
- 另加 400ms 冷却，快速来回滚动不闪

**分页面覆盖（`motion.js` 里的 `AUTO_SELECTOR` 按页面类型分组）：**

| 分类 | 选择器 |
|---|---|
| 通用 | `section`、`.page-head`、`.card`、`.box`、`.item` |
| 商城 | `.pdp > .gallery`、`.pdp > .info`、`.filters`、`.chips` |
| 交易 | `.cart-*`、`.wrap > .left/.right`、`.methods`、`.step` |
| 订单 | `.ord-wrap`、`.od-wrap`、`.res-wrap`、`.order`、`#orderList` |
| 账户 | `.login-wrap`、`.fld`、`.addr-wrap` |
| 内容 | `.about-wrap`、`.co2`、`.help-body`、`.art-wrap`、`.list > *`、`.faq-item` |

**数字滚动：** 后台 `.stat .num` 和任何 `[data-count]` 元素，数字从 0 滚到目标值（easeOutCubic，900ms）。带子元素的数字格会跳过，避免破坏 `<small>` 这类内嵌标签。

**三条安全线（改之前务必读）：**
1. 没有 `IntersectionObserver` 就完全不加 `.reveal`，元素保持默认可见 —— 绝不出现"页面一片空白"
2. 兜底只在「3 秒后连一个元素都没入场过」时触发（判定观察器失效），**不是**无条件全显示 —— 无条件会把还没滚到的元素提前点亮，等于把动效废掉
3. `prefers-reduced-motion: reduce` 下全部退化为瞬时切换

**为什么动效单独成文件、不塞进 `base.css`：** 各页面都是自带完整内联样式的独立页，`base.css` 其实没被任何页面引用。动效放进去等于死代码。

#### 前端质量工具

放在 `D:\DeepSeek-Harness\WorkSpace\_tools\`（不在项目内，避免污染交付物）：

| 脚本 | 作用 |
|---|---|
| `check-interactions.cjs` | 静态扫按钮/链接，找未定义函数、DOM 引用失效、死链 |
| `cdp-deep-scan.cjs` | **严格扫描**：未捕获异常 / console.error / 4xx·5xx / 网络失败 / 空容器全收，不再只匹配三种字符串 |
| `cdp-click-audit.cjs` | 真点按钮并判定有无效应（网络请求·DOM 变化·弹窗·跳转），外加链接目标存在性与 `href="#"` 死链检查 |
| `cdp-handler-check.cjs` | 抓 inline onclick 引用了不存在的函数、带 id 的元素查不到监听器 |
| `cdp-flow.cjs` | 端到端流程：商城 → 详情 → 加购 → 购物袋 → 结算 → 搜索 → 花语，18 项断言 |
| `cdp-interact.cjs` | 逐页点按钮抓异常。**⚠ 它会把所有正常 href 的 `<a>` 直接跳过，每页实际只点 0～6 个，「22 页 OK」不等于交互都验过** |
| `cdp-motion-check.cjs` | 验证动效生效、排查卡在 opacity:0 的元素 |
| `check-encoding.ps1` | 校验脚本编码约定（ps1 带 BOM / bat 纯 ASCII） |
| `check-script-order.ps1` | 提示 api.js 与内联脚本的加载时序风险 |

**反证纪律（必读）：** 任何工具报「0 问题」都不能直接采信。先在 `frontend/` 放一个故意出错的页面（调用不存在的函数 + console.error + 请求 404），确认工具能把它抓出来，再相信全站扫描的结果。2026-10-22 就这么反证过一次：扫描器抓到 4 类问题，才证明「22 页 0 bad」是真的。测完记得删掉那个页面。

**已知坑（踩过的，别再踩）：**

- `api.js` **不能带 `defer`**。页面里裸 IIFE 第一行就调 `API.xxx`，defer 会晚一步执行 → `ReferenceError` → 整页白屏。`product.html` / `checkout.html` / `pay.html` 都栽过。
- 全站导航和页脚是复制的，改一处要全站改。`href="#"` 的死链曾经有 212 处。
- `TWL.toast` 原本不存在（toast 只在 `API` 上），已在 `TWL` 补转发。
- **`product.html` 加购后 600ms 会自动跳到 `cart.html`**（`setTimeout(() => location.href='cart.html')`）。任何"用户刚加购就进购物车"的测试都要考虑这一步。
- **`cart.html` 的演示数据只在「从没初始化过 **且** 购物袋为空」时才灌**。早期只判断 `twl_cart_init`，结果用户加购 → 自动跳过来 → 真实商品被两束演示花整体覆盖（加购「小满」，购物车里变成「晨光序曲 + 木星」）。已修，改动位于 `cart.html` 顶部初始化块，别退回去。

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

**全部可重复跑。** 脚本已处理验证码限流（60 秒 1 次）。

**注意限流对数字的影响：**

| 脚本 | 完整项数 | 限流时 |
|---|---|---|
| `full_test.py` | 62 | 有重试，仍是 62 |
| `security_test.py` | 18 | **会跳过依赖发码的 5 项，显示 13/13** |

`security_test.py` 的「管理员」和「Token 黑名单」两组需要重新发验证码，
60 秒内跑过 `full_test` 就会撞限流。**要看到完整 18/18，中间隔一分钟再跑。**

早期限流时两个脚本都会静默跳过，`full_test` 显示 50/50。
`full_test` 已加重试修掉，`security_test` 保持跳过行为（跳过时总数也一并减少，不会虚报通过）。

---

## 质量体检记录

### 2026-10-22 · 全流程体检（后端 + 前端 + 端到端）

| 项目 | 方法 | 结果 |
|---|---|---|
| 后端单元测试 | `pytest tests/` | 20 / 20 |
| 业务闭环 | `test_loop.py` | 21 / 21 |
| 退款 + 配送 | `test_refund_delivery.py` | 18 / 18 |
| 全流程 | `full_test.py` | 62 / 62 |
| 安全 | `security_test.py` | 18 / 18 |
| MCP 工具 | `test_mcp.py` | 13 / 13 |
| **合计** | | **152 / 152** |
| 22 页控制台 + 网络 | `cdp-deep-scan.cjs` | 0 异常 / 0 失败请求 / 0 空容器 |
| 按钮点击 | `cdp-click-audit.cjs` | 0 报错 / 0 坏链 / 0 死链 |
| 事件处理器 | `cdp-handler-check.cjs` | 0 个引用不存在的函数 |
| 端到端流程 | `cdp-flow.cjs` | 18 / 18 |
| 后台登录 | `cdp-admin-login.cjs` | 通过（数据看板 93 单渲染，0 报错） |

**本轮修掉的**

| 问题 | 根因 | 影响 |
|---|---|---|
| 加购的花被演示数据顶掉 | `cart.html` 只判 `twl_cart_init` 就无条件覆盖 `twl_cart` | **下单主链路**（加购「小满」变成「晨光序曲+木星」） |
| 购物车木星图错配 | `cart.html` 默认数据写 `02_xiaoman.webp` | 购物车显示错误的花 |
| README 数字自相矛盾 | 早期写 134、后期写 152 | 文档可信度 |

**未覆盖的部分（诚实版）**

- 后台的写操作按钮（保存 / 审核 / 推送 / 删除）只验证了「函数存在 + 事件已绑定」，**没有实点**——点了会改真实数据。这类逻辑由 `full_test.py` 在 API 层覆盖。
- `cdp-interact.cjs` 会把所有正常 href 的 `<a>` 跳过，别拿它的「22 页 OK」当交互验收依据。
- 手机真机未测，全部为 headless Chrome 1280×720 视口。

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
| [第三方接入说明](docs/02-技术/第三方接入说明.md) | **接真实微信/支付宝支付退款、顺丰/达达配送、短信、OSS、Redis 的完整步骤与工作量对照** |
| [任务书](docs/01-需求/任务书.md) | 需求定义（最权威） |
| [工程书](docs/02-技术/工程书.md) | 技术实现 |
| [首页改版说明](docs/02-技术/首页改版说明.md) | **首屏通栏化、导航合并的结构决策与踩坑** |
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
