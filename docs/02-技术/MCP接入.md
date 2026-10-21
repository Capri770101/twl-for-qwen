# MCP Server · AI 接入

让 AI 智能体（千问、Claude、Cursor 等）直接查询商品、下单、查订单、提售后。

---

## 这是什么

**MCP = Model Context Protocol**，AI 客户端调用外部工具的通用协议。

**两层 GEO 的区别：**

| 方式 | AI 能做什么 |
|---|---|
| `llms.txt` | **读**到你的内容（被动） |
| **MCP Server** | **操作**你的系统（主动） |

有了 MCP，用户问 AI「帮我订一束香槟玫瑰送深圳」，AI 能直接搜花、下单、查单 —— 不用跳转网站。

---

## 启动

```bash
cd backend
.venv\Scripts\python.exe -m app.mcp_server
```

**stdio 模式**：通过标准输入输出通信，不需要端口。

---

## 接入 AI 客户端

### Claude Desktop

配置在 `%APPDATA%\Claude\claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "tiaowulan": {
      "command": "D:\\DeepSeek-Harness\\WorkSpace\\跳舞兰\\backend\\.venv\\Scripts\\python.exe",
      "args": ["-m", "app.mcp_server"],
      "cwd": "D:\\DeepSeek-Harness\\WorkSpace\\跳舞兰\\backend"
    }
  }
}
```

### Cursor

配置在 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "tiaowulan": {
      "command": "D:\\DeepSeek-Harness\\WorkSpace\\跳舞兰\\backend\\.venv\\Scripts\\python.exe",
      "args": ["-m", "app.mcp_server"],
      "cwd": "D:\\DeepSeek-Harness\\WorkSpace\\跳舞兰\\backend"
    }
  }
}
```

### DSH（DeepSeek Harness）

`~/.dsh/profiles/desktop/cordis.patch.yml`：

```yaml
- insert:
    - id: mcp-tiaowulan
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: tiaowulan
        transport: stdio
        command: 'D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend\.venv\Scripts\python.exe'
        args:
          - '-m'
          - 'app.mcp_server'
        cwd: 'D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend'
```

### 千问 / 通义

千问支持 MCP 的入口在「智能体 → 工具 → 自定义 MCP」，填：
- 类型：stdio
- 命令：`D:\...\backend\.venv\Scripts\python.exe`
- 参数：`-m app.mcp_server`
- 工作目录：`D:\...\backend`

**注意：** 千问的 MCP 支持情况随版本变化，以官方文档为准。

---

## 提供的 9 个工具

### 商品查询

| 工具 | 参数 | 返回 |
|---|---|---|
| `search_flowers` | `keyword` `category` `max_price` `limit` | 花束列表 |
| `get_product` | `product_id` | 花材、花语、价格、库存 |
| `check_delivery` | `product_id` `delivery_date` | 是否可送、运费、时段 |
| `list_categories` | — | 分类和数量 |

**示例：**
```
用户：有什么 300 块以内的香槟色花束？
AI 调用：search_flowers(keyword="香槟", max_price=300)
返回：晨光序曲 ¥299（香槟玫瑰 20 枝 · 满天星）
```

### 交易

| 工具 | 参数 | 返回 |
|---|---|---|
| `create_order` | `product_id` `quantity` `receiver_name` `receiver_phone` `receiver_address` `card_message` `remark` | 订单号、金额 |
| `query_order` | `order_no` | 状态、明细、时间 |
| `create_ticket` | `order_no` `reason` `ticket_type` `contact_phone` | 工单号 |

**⚠ 注意：** `create_order` **会真实占用库存**。生产环境接 AI 时，应该加一层「用户确认」再提交。

### 内容

| 工具 | 参数 | 返回 |
|---|---|---|
| `get_flower_meaning` | `flower` | 花语、文章、FAQ |
| `list_articles` | `limit` | 花语文章列表 |

**示例：**
```
用户：白玫瑰的花语是什么？
AI 调用：get_flower_meaning(flower="白玫瑰")
返回：{
  "title": "白玫瑰的花语是什么？和红玫瑰有什么区别",
  "meaning": "纯洁与尊敬，也有「你是我的唯一」",
  "faq": [
    {"question": "白玫瑰适合送什么人？", "answer": "..."},
    ...
  ]
}
```

---

## 完整对话示例

```
用户：帮我订一束香槟玫瑰，明天送我女朋友，深圳南山区

AI 思考：
  1. 先搜花
  2. 查配送
  3. 下单

AI 调用 1：search_flowers(keyword="香槟玫瑰")
  → 晨光序曲 ¥299（香槟玫瑰 20 枝 · 满天星）

AI 调用 2：check_delivery(product_id="TW-001", delivery_date="2026-10-22")
  → available: true, delivery_slots: ["14:00-16:00", "18:00-20:00"]

AI 回复用户：
  「找到一束香槟玫瑰：晨光序曲 ¥299，20 枝配满天星。
   明天可以送，有两个时段可选：14:00-16:00 或 18:00-20:00。
   需要收花人的姓名、电话和详细地址。」

用户：李女士，13900001234，南山区科技园南路 18 号

AI 调用 3：create_order(
  product_id="TW-001",
  quantity=1,
  receiver_name="李女士",
  receiver_phone="13900001234",
  receiver_address="深圳市南山区科技园南路 18 号",
  card_message="明天见。"
)
  → order_no: TWL20261021140552C475, total: ¥299

AI 回复：
  「订单已创建：TWL20261021140552C475，¥299。
   还需要完成支付，30 分钟内有效。」
```

---

## 自测

**不需要 AI 客户端，直接测工具逻辑：**

```bash
cd scripts
python test_mcp.py
```

**输出：**
```
✓  1. search_flowers           5 个
✓  2.   按关键词「玫瑰」          2 个
✓  3.   按分类 love             3 个
✓  4.   按价格 ≤260             2 个
✓  5. get_product              晨光序曲 ¥299.0
✓  6.   不存在商品               商品 NOT-EXIST 不存在
✓  7. check_delivery           available=True
✓  8. list_categories          4 个分类
✓  9. get_flower_meaning       3 篇
✓ 10. list_articles            5 篇
✓ 11. create_order             TWL20261021140552C475
✓ 12. query_order              待支付 ¥259.0
✓ 13. create_ticket            TK20261021140552BC8

通过 13 / 13
```

---

## 一件事必须注意

**MCP 里没有 `get_db` 依赖，写操作必须手动 `commit`。**

```python
async with AsyncSessionLocal() as db:
    svc = order_service.OrderService(db)
    order = await svc.create_order(payload)

    await db.commit()   # ← 必须，否则数据不落库
```

**为什么：** service 层只 `flush` 不 `commit`，commit 是 `get_db` 依赖做的（FastAPI 请求结束时）。MCP 不走 FastAPI，所以要自己提交。

**踩过这个坑：** 第一次跑测试，订单号返回了、日志也打了，但数据库里查不到。

---

## 和 llms.txt 的关系

**两个都要有，作用不同：**

| | llms.txt | MCP Server |
|---|---|---|
| **AI 能做什么** | 读内容 | 执行操作 |
| **谁主动** | AI 主动抓 | 用户要求 AI 调用 |
| **覆盖场景** | 「跳舞兰是什么」 | 「帮我订一束花」 |
| **技术门槛** | 一个文本文件 | 部署一个进程 |

**优先级：** 先 llms.txt（成本低、覆盖广），再 MCP（成本高、转化强）。

---

## 后续扩展方向

**现在有的：**
- 查询（商品、分类、花语）
- 下单
- 查单
- 提售后

**可以加的：**
- `cancel_order` —— 取消订单
- `list_orders` —— 我的订单（需要用户身份）
- `track_delivery` —— 物流轨迹（需履约系统）
- `apply_refund` —— 申请退款（需退款流程）

**加工具的方式：**

在 `backend/app/mcp_server.py` 里加一个 `@mcp.tool()` 函数就行，SDK 自动注册。
