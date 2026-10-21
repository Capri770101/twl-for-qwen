# 前端

跳舞兰 H5 的 21 个页面。

**纯 HTML + CSS + JS，零框架零构建。**

---

## 结构

```
frontend/
│
├── 【用户端 21 页】
│
├── index.html                  首页（品牌叙事 + 精选花束）
├── shop.html                   全部花束（4 列网格）
├── product.html                商品详情（左图右信息）
├── cart.html                   购物袋
├── checkout.html               确认订单
├── pay.html                    支付
├── order-success.html          下单成功
│
├── login.html                  登录
├── orders.html                 我的订单
├── order-detail.html           订单详情
├── address.html                地址簿
├── after-sale.html             申请售后
│
├── flower-language.html        花语百科（文章列表）
├── flower-language-detail.html 花语详情
├── about.html                  关于
├── contact.html                联系
├── search.html                 搜索
│
├── help-delivery.html          配送范围
├── help-returns.html           售后政策
├── help-faq.html               常见问题
│
├── 【管理后台】
│
├── admin.html                  后台（8 个功能页）
│
├── 【资源】
│
├── js/
│   └── api.js                  接口封装（所有页面共用）
│
├── css/
│   └── base.css                【未使用】样式已内联到各页面
│
├── images/                     商品图（WebP，8 张）
│
└── 【SEO / GEO 站点文件】
    ├── robots.txt              爬虫规则
    ├── sitemap.xml             31 个 URL
    └── llms.txt                给 AI 读的站点说明
```

---

## 技术方案

**不用框架，不用构建。**

- 纯 HTML + CSS + JS
- 样式内联在 `<style>` 里
- 图片外链 WebP（`/images/xx.webp`）
- 改完刷新就能看到，没有编译等待

**为什么这么做：**

1. 页面结构简单，React/Vue 是杀鸡用牛刀
2. 省掉 node_modules（363MB）和构建流程
3. 部署只要复制文件，Nginx 直接托管

---

## 管理后台（admin.html）

**8 个功能页面（左侧导航切换）：**

| 页面 | 功能 |
|---|---|
| **数据看板** | 今日订单、营收、待处理、工单数、在售商品数 |
| **订单** | 全部订单列表，可看详情 |
| **待处理** | 筛出 paid / preparing / delivering 状态的订单 |
| **工单** | 售后工单列表，可回复 |
| **花束** | 商品列表 |
| **分类** | 分类统计 |
| **内容** | 花语文章 |
| **设置** | 配送规则等配置 |

### 订单推进流程

**「待处理」页面是日常操作的主战场。**

```
订单进来（已支付）
  ↓ 点「推进」
配花中
  ↓ 点「推进」
配送中
  ↓ 点「推进」
已送达
  ↓ 点「推进」
已完成
```

**每次推进会弹确认框，显示「当前状态 → 目标状态」。**

**状态机在 `api.js` 和后端都有：**
- 前端 `NEXT_STATUS` 只用于 UI 提示
- 真正的校验在后端 `TRANSITIONS` 白名单

**非法流转（跳步、回退）后端返回 409，前端提示失败。**

### 工单处理

```
用户提工单（submitted）
  ↓ 后台点「回复」，输入内容
处理中 / 已解决
```

---

## 接口调用

所有页面通过 `js/api.js` 调后端：

```html
<script src="js/api.js" defer></script>
<script>
  // 拿商品列表
  const data = await API.listProducts({ category: 'love' });

  // 创建订单
  const order = await API.createOrder({ items, receiver });

  // 后台推进订单
  await API.updateOrderStatus(orderNo, 'preparing');

  // 提示
  API.toast('操作成功');
</script>
```

### 接口方法一览

| 方法 | 说明 |
|---|---|
| **商品** | |
| `API.listProducts()` | 商品列表（筛选/搜索/排序） |
| `API.getProduct(id)` | 商品详情 |
| `API.getCategories()` | 分类统计 |
| `API.checkAvailability(id, date)` | 配送可用性 |
| **订单** | |
| `API.createOrder()` | 创建订单 |
| `API.getOrder(no)` | 查订单 |
| `API.listOrders()` | 订单列表 |
| `API.cancelOrder(no)` | 取消订单 |
| **支付** | |
| `API.createPayment()` | 发起支付 |
| `API.getPayments(orderNo)` | 支付记录 |
| **售后** | |
| `API.createTicket()` | 提交售后 |
| `API.listTickets()` | 工单列表 |
| **后台** | |
| `API.stats()` | 数据统计 |
| `API.adminOrders()` | 后台订单列表 |
| `API.adminProducts()` | 后台商品列表 |
| `API.updateOrderStatus()` | **推进订单状态** |
| `API.request()` | 通用请求 |

**购物袋**用 localStorage，不经过后端（`window.TWL` 对象）。

---

## Demo 模式

**`DEMO_MODE=true` 时：**

`api.js` 在页面加载时调 `/api/v1/system/config`，然后：

1. 顶部插一条提示：「演示环境 · 商品与配送信息为示例数据，下单不会真实扣款」
2. 公告栏从配置读，未配置时显示「配送信息待配置」
3. 运行时替换页面里的假承诺（「2 小时达」→「配送信息待配置」）

**点「知道了」后本次会话不再显示**（sessionStorage 记住）。

**改 `DEMO_MODE=false` 重启 → 所有标识消失。**

---

## SSR（服务端渲染）

**4 个页面由后端渲染首屏：**

| 页面 | SSR 内容 |
|---|---|
| `shop.html` | 商品卡片列表 |
| `product.html` | 商品详情（名称/价格/花材/花语） |
| `flower-language.html` | 文章列表 |
| `flower-language-detail.html` | 文章正文 + FAQ |

**为什么：** 页面是静态 HTML + JS 渲染，搜索引擎爬虫不执行 JS，看到的是空壳。

**实测：** 改造前爬虫可读性 3/7，改造后 7/7。

**用户无感** —— JS 加载后接管交互，视觉一模一样。

**动态 meta：** 每篇文章的 title/description/canonical 各自不同（后端 SSR 时注入）。

---

## 设计规范

### 配色

```
白      #ffffff
浅米    #f1efeb
近黑    #1a1a1a
深灰    #6f6a61   ← --gray-a，WCAG AA 通过
中灰    #605c55   ← 页脚用
分割线  #e5e2dc
```

**没有品牌色。** 花本身已经是最艳的东西，页面再加颜色就抢戏了。

### 字体

**全部系统字体，零加载。**

| 用途 | 字体栈 |
|---|---|
| Logo 中文衬线 | `'Songti SC','STSong','SimSun',serif` |
| 英文装饰字 | `Georgia,'Times New Roman',serif` |
| 正文 | `-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',system-ui,sans-serif` |

**为什么去掉 Google Fonts：** 原来加载 495KB 字体 + 6 个外部请求。换成系统字体后 LCP 从 30.2s 降到 2.4s。

### 布局

| 断点 | 变化 |
|---|---|
| ≥1440px | 内容 1520px 居中，4 列网格 |
| 1100–1440px | 内容 1320px 居中，4 列网格 |
| 860–1100px | 3 列网格，左右分栏变窄 |
| <860px | 单列堆叠，2 列网格 |

### 形状

- 按钮 4px 圆角
- 尺寸按钮 50%（正圆）
- 包装按钮 100px（胶囊）
- **不用阴影**，只用 1px 细线分隔

---

## 页面访问

启动后端后：

```
http://127.0.0.1:8000/                 首页
http://127.0.0.1:8000/shop.html        商城
http://127.0.0.1:8000/admin.html       后台
```

**后端把 `frontend/` 挂载到 `/`，所以页面和 API 同源，没有跨域问题。**

---

## 性能

| 指标 | 值 |
|---|---|
| Lighthouse Performance | **98** |
| Lighthouse SEO | **100** |
| Lighthouse Accessibility | **100** |
| 首页 HTML（gzip 后） | 9 KB |
| 图片平均 | 39 KB |
| 阻塞资源 | 0 个 |

**关键优化：**
- 图片 WebP（6571KB → 315KB）
- 去掉 Google Fonts（省 495KB）
- `api.js` 加 `defer`
- 后端 GZip + 缓存头

---

## 改页面的注意事项

1. **加新图要压缩并转 WebP**
   ```bash
   cd scripts
   python compress_images.py
   ```

2. **不要直接在别处改** —— 页面以 `frontend/` 为准

3. **加新页面：**
   - 在 `frontend/` 建 HTML
   - 从现有页面复制页眉页脚（保持一致）
   - 加上 `<script src="js/api.js" defer>`
   - 在 `scripts/seo_config.py` 加 SEO 配置
   - 跑 `python apply_seo.py`
   - 在 `docs/04-原型/页面清单.html` 加链接

4. **改完跑检查**
   ```bash
   cd scripts
   python check_crawl.py    # 爬虫能不能读到
   python audit_seo.py      # SEO 有没有退步
   python check_perf.py     # 性能有没有变差
   ```
