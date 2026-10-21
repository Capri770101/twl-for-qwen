# 前端

跳舞兰 H5 的 21 个页面。

---

## 结构

```
frontend/
├── index.html                  首页（品牌叙事）
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
├── flower-language.html        花语百科
├── flower-language-detail.html 花语详情
├── about.html                  关于
├── contact.html                联系
├── search.html                 搜索
│
├── help-delivery.html          配送范围
├── help-returns.html           售后政策
├── help-faq.html               常见问题
│
├── admin.html                  管理后台
│
├── js/
│   └── api.js                  接口封装（所有页面共用）
│
├── css/
│   └── base.css                【未使用】样式已内联到各页面
│
└── images/                     商品图（7 张）
```

---

## 技术方案

**不用框架，不用构建。**

- 纯 HTML + CSS + JS
- 样式内联在 `<style>` 里
- 图片部分 base64 内嵌，部分从 `/images/` 加载
- 改完刷新就能看到，没有编译等待

**为什么这么做：**

1. 页面结构简单，React/Vue 是杀鸡用牛刀
2. 省掉 node_modules（363MB）和构建流程
3. 部署只要复制文件，Nginx 直接托管

---

## 接口调用

所有页面通过 `js/api.js` 调后端：

```html
<script src="js/api.js"></script>
<script>
  // 拿商品列表
  const data = await API.listProducts({ category: 'love' });

  // 创建订单
  const order = await API.createOrder({ items, receiver });

  // 提示
  API.toast('操作成功');
</script>
```

**接口封装了什么：**

| 方法 | 说明 |
|---|---|
| `API.listProducts()` | 商品列表（支持筛选/搜索/排序） |
| `API.getProduct(id)` | 商品详情 |
| `API.getCategories()` | 分类统计 |
| `API.createOrder()` | 创建订单 |
| `API.getOrder(no)` | 查订单 |
| `API.listOrders()` | 订单列表 |
| `API.createPayment()` | 发起支付 |
| `API.createTicket()` | 提交售后 |
| `API.listTickets()` | 工单列表 |
| `API.request()` | 通用请求 |

**购物袋**用 localStorage，不经过后端（`window.TWL` 对象）。

---

## 设计规范

### 配色

```
白      #ffffff
浅米    #f1efeb
近黑    #1a1a1a
深灰    #666666
浅灰    #999999
分割线  #e5e5e5
```

**没有品牌色。** 花本身已经是最艳的东西，页面再加颜色就抢戏了。

### 字体

- **Logo「跳舞兰」** → Noto Serif SC（唯一用衬线的地方）
- **其他所有文字** → 系统无衬线（Helvetica / PingFang）

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

## 改页面的注意事项

1. **改完要内嵌图片**（如果加了新图）：
   ```bash
   cd scripts
   python embed_luxe.py
   ```

2. **不要直接在 `backend/storage/` 改** —— 那里只有 uploads，页面以 `frontend/` 为准

3. **加新页面**：
   - 在 `frontend/` 建 HTML
   - 头部页脚从现有页面复制（保持一致）
   - 加上 `<script src="js/api.js">`
   - 在 `docs/04-原型/页面清单.html` 加链接
