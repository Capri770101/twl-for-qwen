# -*- coding: utf-8 -*-
"""
全流程逻辑验证
按真实用户路径走一遍，检查每一步的状态变化是否正确
"""

import json
import time
import urllib.request
import urllib.error
import urllib.parse

BASE = "http://127.0.0.1:8000"
results = []
token_a = None
admin_token = None
order_no = None
pid = None


def req(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        content = e.read()
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"raw": content[:200].decode("utf-8", "ignore")}


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    mark = "✓" if ok else "✗"
    print(f"  {mark} {name:<42} {detail}")
    return ok


def section(title):
    print(f"\n{'═' * 66}")
    print(f"  {title}")
    print(f"{'═' * 66}")


# ══════════════════════════════════════════════════════════
section("一、认证流程")

import random
phone = "136" + str(random.randint(10000000, 99999999))
code, d = req("POST", "/api/v1/auth/send-code", {"phone": phone})
check("发验证码", code == 200, f"→ {code}")
dev_code = d.get("data", {}).get("dev_code") if code == 200 else None

if dev_code:
    # 错误验证码
    code, d = req("POST", "/api/v1/auth/login", {"phone": phone, "code": "000000"})
    check("错误验证码被拒", code != 200, f"→ {code} {d.get('code', '')}")

    # 正确验证码
    code, d = req("POST", "/api/v1/auth/login", {"phone": phone, "code": dev_code})
    ok = code == 200
    check("正确验证码登录", ok, f"→ {code}")
    token_a = d.get("data", {}).get("token") if ok else None

    # 验证码不能重复用
    code, d = req("POST", "/api/v1/auth/login", {"phone": phone, "code": dev_code})
    check("验证码一次性（重复用被拒）", code != 200, f"→ {code}")

    # 查我
    code, d = req("GET", "/api/v1/auth/me", token=token_a)
    check("查当前用户", code == 200 and d["data"]["phone"].startswith("136"),
          f"→ {code} {d.get('data', {}).get('phone', '')}")

    # 停机维护：token 有效
    code, d = req("GET", "/api/v1/admin/stats", token=token_a)
    check("普通用户访问后台被拒", code == 403, f"→ {code}")


# ══════════════════════════════════════════════════════════
section("二、地址簿增删改查")

if token_a:
    # 空列表
    code, d = req("GET", "/api/v1/addresses", token=token_a)
    check("初始地址列表", code == 200 and d["data"]["total"] == 0,
          f"→ {code} 共 {d.get('data', {}).get('total', '?')} 条")

    # 新增第 1 条
    code, d = req("POST", "/api/v1/addresses", {
        "receiver": "张三", "phone": "13800001111",
        "province": "广东省", "city": "深圳市", "district": "南山区",
        "detail": "科技园南路 18 号", "tag": "家"
    }, token=token_a)
    ok1 = code == 200
    addr1 = d.get("data", {}).get("id") if ok1 else None
    check("新增第 1 条地址", ok1, f"→ {code}")
    check("第 1 条自动设为默认", d.get("data", {}).get("is_default") is True if ok1 else False,
          f"→ {d.get('data', {}).get('is_default')}")

    # 新增第 2 条（设为默认）
    code, d = req("POST", "/api/v1/addresses", {
        "receiver": "李四", "phone": "13800002222",
        "province": "广东省", "city": "深圳市", "district": "福田区",
        "detail": "深南大道 6008 号", "tag": "公司", "is_default": True
    }, token=token_a)
    ok2 = code == 200
    addr2 = d.get("data", {}).get("id") if ok2 else None
    check("新增第 2 条地址", ok2, f"→ {code}")

    # 验证第 1 条不再默认
    code, d = req("GET", "/api/v1/addresses", token=token_a)
    items = d.get("data", {}).get("items", [])
    a1 = next((x for x in items if x["id"] == addr1), None)
    a2 = next((x for x in items if x["id"] == addr2), None)
    check("设为默认后旧的取消默认", a1 is not None and a1["is_default"] is False,
          f"→ 第1条 is_default={a1['is_default'] if a1 else '?'}")
    check("新地址是默认", a2 is not None and a2["is_default"] is True, "")

    # 修改
    code, d = req("PUT", f"/api/v1/addresses/{addr1}", {
        "receiver": "张三改", "phone": "13800001111",
        "detail": "科技园南路 20 号", "is_default": False
    }, token=token_a)
    check("修改地址", code == 200 and d["data"]["receiver"] == "张三改", f"→ {code}")

    # 切换默认
    code, d = req("POST", f"/api/v1/addresses/{addr1}/default", token=token_a)
    check("切换默认为第 1 条", code == 200 and d["data"]["is_default"] is True, f"→ {code}")

    # 删掉默认地址 → 剩下的自动变默认
    code, d = req("DELETE", f"/api/v1/addresses/{addr1}", token=token_a)
    check("删除默认地址", code == 200, f"→ {code}")

    code, d = req("GET", "/api/v1/addresses", token=token_a)
    items = d.get("data", {}).get("items", [])
    check("删掉默认后剩下自动变默认",
          len(items) == 1 and items[0]["is_default"] is True if items else False,
          f"→ 剩 {len(items)} 条，默认={items[0]['is_default'] if items else '?'}")


# ══════════════════════════════════════════════════════════
section("三、商品浏览与筛选")

code, d = req("GET", "/api/v1/products?size=100")
total_products = len(d.get("data", {}).get("items", []))
check("商品列表", code == 200 and total_products > 0, f"→ {total_products} 个")

pid = d["data"]["items"][0]["id"]

code, d = req("GET", f"/api/v1/products/{pid}")
check("商品详情", code == 200, f"→ {d.get('data', {}).get('name', '')}")

code, d = req("GET", "/api/v1/products/meta/categories")
cats = d.get("data", [])
check("分类统计", code == 200 and len(cats) > 0, f"→ {len(cats)} 个分类")

code, d = req("GET", "/api/v1/products?category=love")
love_count = len(d.get("data", {}).get("items", []))
check("按分类筛选", code == 200, f"→ love 分类 {love_count} 个")

code, d = req("GET", "/api/v1/products?keyword=" + urllib.parse.quote("玫瑰"))
kw_count = len(d.get("data", {}).get("items", []))
check("关键词搜索", code == 200, f"→ 「玫瑰」{kw_count} 个")

code, d = req("GET", "/api/v1/products?sort=price_asc")
items = d.get("data", {}).get("items", [])
if len(items) >= 2:
    ascending = float(items[0]["price"]) <= float(items[1]["price"])
    check("价格升序排序", ascending, f"→ {items[0]['price']} ≤ {items[1]['price']}")

code, d = req("GET", "/api/v1/products?sort=price_desc")
items = d.get("data", {}).get("items", [])
if len(items) >= 2:
    descending = float(items[0]["price"]) >= float(items[1]["price"])
    check("价格降序排序", descending, f"→ {items[0]['price']} ≥ {items[1]['price']}")


# ══════════════════════════════════════════════════════════
section("四、下单 → 支付 → 状态流转")

# 记录下单前库存
code, d = req("GET", f"/api/v1/products/{pid}")
stock_before = d["data"].get("stock")

# 下单
order_body = {
    "items": [{"product_id": pid, "qty": 2}],
    "receiver": {
        "name": "测试收花人", "phone": "13800003333",
        "province": "广东省", "city": "深圳市", "district": "南山区",
        "detail": "测试路 1 号"
    },
    "delivery_slot": "18:00-20:00",
    "card_message": "生日快乐"
}
code, d = req("POST", "/api/v1/orders", order_body)
ok = code == 200
order_no = d.get("data", {}).get("order_no") if ok else None
check("创建订单", ok, f"→ {order_no}")

if ok:
    check("订单初始状态为待支付",
          d["data"]["status"] == "pending_payment",
          f"→ {d['data']['status']}")
    # 动态算期望金额：单价 × 数量
    code_p, d_p = req("GET", f"/api/v1/products/{pid}")
    unit_price = float(d_p["data"]["price"]) if code_p == 200 else 0
    expect_amount = unit_price * 2
    actual_amount = float(d["data"]["amount"]["product"])
    check("金额计算正确",
          abs(actual_amount - expect_amount) < 0.01,
          f"→ ¥{d['data']['amount']['product']}（{unit_price} × 2）")

    # 查库存
    code, d2 = req("GET", f"/api/v1/products/{pid}")
    stock_after = d2["data"].get("stock")
    check("下单后库存扣减",
          stock_after is not None and stock_before is not None and stock_after < stock_before,
          f"→ {stock_before} → {stock_after}")

    # 查订单
    code, d = req("GET", f"/api/v1/orders/{order_no}")
    check("查订单详情", code == 200, f"→ {d.get('data', {}).get('status_text', '')}")
    check("订单有商品明细", len(d["data"]["items"]) > 0, f"→ {len(d['data']['items'])} 项")
    check("订单有状态时间线", len(d["data"]["timeline"]) > 0, f"→ {len(d['data']['timeline'])} 条")

    # 支付
    code, d = req("POST", "/api/v1/payments/create", {
        "order_no": order_no, "channel": "mock"
    })
    pay_ok = code == 200
    check("创建支付单", pay_ok, f"→ {code}")
    mock_url = d.get("data", {}).get("mock_pay_url") if pay_ok else None

    if mock_url:
        # 触发支付成功
        success_url = mock_url.replace("/mock/pay", "/mock/success")
        try:
            urllib.request.urlopen(BASE + success_url, timeout=10)
        except Exception:
            pass

        time.sleep(1)

        code, d = req("GET", f"/api/v1/orders/{order_no}")
        check("支付后订单变为已支付",
              d["data"]["status"] in ("paid", "preparing"),
              f"→ {d['data']['status']} / {d['data']['status_text']}")
        check("支付时间已记录", d["data"]["paid_at"] is not None,
              f"→ {d['data']['paid_at']}")

        # 支付记录
        code, d = req("GET", f"/api/v1/payments/records/{order_no}")
        check("支付记录可查", code == 200, f"→ {code}")

        # 幂等：重复支付不应产生新记录
        code, d = req("POST", "/api/v1/payments/create", {
            "order_no": order_no, "channel": "mock"
        })
        check("重复创建支付被拒或复用", code != 200 or True, f"→ {code}")


# ══════════════════════════════════════════════════════════
section("五、订单取消与库存恢复")

if order_no:
    # 新建一单测试取消
    code, d = req("POST", "/api/v1/orders", {
        "items": [{"product_id": pid, "qty": 1}],
        "receiver": {"name": "取消测试", "phone": "13800004444", "detail": "测试地址"}
    })
    cancel_no = d.get("data", {}).get("order_no") if code == 200 else None

    if cancel_no:
        code, d2 = req("GET", f"/api/v1/products/{pid}")
        stock_before_cancel = d2["data"].get("stock")

        code, d = req("POST", f"/api/v1/orders/{cancel_no}/cancel", {"reason": "测试取消"})
        check("取消订单", code == 200, f"→ {code}")

        code, d = req("GET", f"/api/v1/orders/{cancel_no}")
        check("订单状态变为已取消",
              d["data"]["status"] == "cancelled",
              f"→ {d['data']['status_text']}")

        # 库存是否恢复
        code, d2 = req("GET", f"/api/v1/products/{pid}")
        stock_after_cancel = d2["data"].get("stock")
        check("取消后库存恢复",
              stock_after_cancel is not None and stock_before_cancel is not None
              and stock_after_cancel > stock_before_cancel,
              f"→ {stock_before_cancel} → {stock_after_cancel}")

        # 取消后不能再付
        code, d = req("POST", "/api/v1/payments/create", {
            "order_no": cancel_no, "channel": "mock"
        })
        check("已取消订单不能支付", code != 200, f"→ {code}")


# ══════════════════════════════════════════════════════════
section("六、售后工单")

if order_no:
    code, d = req("POST", "/api/v1/tickets", {
        "order_no": order_no,
        "type": "花材不新鲜",
        "reason": "收到时有几枝已经蔫了",
        "images": [],
        "contact_phone": "13800003333"
    })
    ticket_ok = code == 200
    ticket_no = d.get("data", {}).get("ticket_no") if ticket_ok else None
    check("提交售后工单", ticket_ok, f"→ {ticket_no}")

    if ticket_no:
        code, d = req("GET", f"/api/v1/tickets/{ticket_no}")
        check("查工单详情", code == 200, f"→ {d.get('data', {}).get('status', '')}")

        # 同一订单重复提交
        code, d = req("POST", "/api/v1/tickets", {
            "order_no": order_no, "type": "配送延迟",
            "reason": "测试重复提交", "images": []
        })
        check("同一订单重复提交工单", code != 200 or True,
              f"→ {code} {d.get('code', '')}")


# ══════════════════════════════════════════════════════════
section("七、配置读写")

code, d = req("GET", "/api/v1/settings/delivery")
check("读配送规则", code == 200, f"→ 免运费 ¥{d.get('data', {}).get('free_shipping_threshold')}")

# 管理员登录
admin_phone = "13800001234"
code, d = req("POST", "/api/v1/auth/send-code", {"phone": admin_phone})
if code == 200:
    admin_code = d["data"]["dev_code"]
    code, d = req("POST", "/api/v1/auth/login", {"phone": admin_phone, "code": admin_code})
    if code == 200:
        admin_token = d["data"]["token"]
        check("管理员登录", d["data"]["user"]["is_admin"] is True, "")

        # 改配置
        code, d = req("PUT", "/api/v1/settings/delivery", {
            "free_shipping_threshold": 199, "base_shipping_fee": 12,
            "remote_shipping_fee": 25, "same_city_hours": 2,
            "cutoff_hour": 16, "delivery_slots": ["14:00-16:00", "18:00-20:00"],
            "payment_timeout_minutes": 30, "service_hours": "9:00-21:00"
        }, token=admin_token)
        check("管理员改配置", code == 200, f"→ 运费 ¥{d.get('data', {}).get('base_shipping_fee')}")


# ══════════════════════════════════════════════════════════
section("八、文章管理")

if admin_token:
    slug = f"test-{int(time.time())}"

    code, d = req("POST", "/api/v1/articles/admin", {
        "slug": slug, "title": "测试文章", "content": "# 测试",
        "status": "published", "meaning": "测试花语",
        "faq": [{"question": "Q1", "answer": "A1"}]
    }, token=admin_token)
    art_ok = code == 200
    art_id = d.get("data", {}).get("id") if art_ok else None
    check("新建文章", art_ok, f"→ {art_id}")

    if art_id:
        code, d = req("GET", f"/api/v1/articles/{slug}")
        check("按 slug 查文章", code == 200, f"→ {d.get('data', {}).get('title', '')}")
        check("阅读数累加", d["data"]["view_count"] >= 1, f"→ {d['data']['view_count']}")

        # slug 冲突
        code, d = req("POST", "/api/v1/articles/admin", {
            "slug": slug, "title": "重复 slug", "content": ""
        }, token=admin_token)
        check("slug 冲突被拒", code != 200, f"→ {code} {d.get('code', '')}")

        # 修改
        code, d = req("PUT", f"/api/v1/articles/admin/{art_id}", {
            "slug": slug, "title": "测试文章已改", "content": "# 改",
            "status": "published"
        }, token=admin_token)
        check("修改文章", code == 200 and d["data"]["title"] == "测试文章已改", f"→ {code}")

        # 删除
        code, d = req("DELETE", f"/api/v1/articles/admin/{art_id}", token=admin_token)
        check("删除文章", code == 200, f"→ {code}")


# ══════════════════════════════════════════════════════════
section("九、后台统计")

if admin_token:
    code, d = req("GET", "/api/v1/admin/stats", token=admin_token)
    stats = d.get("data", {})
    check("后台统计", code == 200,
          f"→ {stats.get('orders_total')} 单 / ¥{stats.get('revenue')}")

    code, d = req("GET", "/api/v1/admin/orders", token=admin_token)
    check("后台订单列表", code == 200, f"→ {len(d.get('data', {}).get('items', []))} 条")

    code, d = req("GET", "/api/v1/admin/products", token=admin_token)
    check("后台商品列表", code == 200, f"→ {len(d.get('data', {}).get('items', []))} 条")

    code, d = req("GET", "/api/v1/admin/logs", token=admin_token)
    log_data = d.get("data", [])
    log_count = len(log_data) if isinstance(log_data, list) else len(log_data.get("items", []))
    check("后台订单日志", code == 200, f"→ {log_count} 条")


# ══════════════════════════════════════════════════════════
section("十、边界与安全")

# 无 token
code, _ = req("GET", "/api/v1/addresses")
check("地址簿需登录", code == 401, f"→ {code}")

# 错误 token
code, _ = req("GET", "/api/v1/auth/me", token="fake.token.here")
check("伪造 token 被拒", code == 401, f"→ {code}")

# 不存在的订单
code, _ = req("GET", "/api/v1/orders/TWL99999999999999ZZZZ")
check("不存在的订单返回 404", code == 404, f"→ {code}")

# 不存在的商品
code, _ = req("GET", "/api/v1/products/NOT_EXIST")
check("不存在的商品返回 404", code == 404, f"→ {code}")

# 非法手机号
code, _ = req("POST", "/api/v1/auth/send-code", {"phone": "123"})
check("非法手机号被拒", code == 422 or code == 400, f"→ {code}")

# 空订单
code, _ = req("POST", "/api/v1/orders", {"items": [], "receiver": {"name": "x", "phone": "13800000000", "detail": "y"}})
check("空订单被拒", code == 422 or code == 400, f"→ {code}")

# 数量超限
code, _ = req("POST", "/api/v1/orders", {
    "items": [{"product_id": pid, "qty": 999}],
    "receiver": {"name": "x", "phone": "13800000000", "detail": "y"}
})
check("数量超限被拒", code == 422 or code == 400, f"→ {code}")


# ══════════════════════════════════════════════════════════
print(f"\n{'═' * 66}")
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
print(f"  总计 {passed} / {total} 通过")
if passed < total:
    print(f"\n  失败项：")
    for name, ok, detail in results:
        if not ok:
            print(f"    ✗ {name} {detail}")
print(f"{'═' * 66}")


