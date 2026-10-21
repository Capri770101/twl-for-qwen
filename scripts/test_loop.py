# -*- coding: utf-8 -*-
"""
业务闭环实测（参数按真实 schema 修正）

用户视角：选商品 → 下单 → 支付 → 查单 → 提工单
后台视角：登录 → 看订单 → 推进状态 → 回复工单 → 看统计
"""

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"
PHONE = "13800001234"  # 管理员


def call(method, path, body=None, token=None):
    req = urllib.request.Request(
        BASE + path,
        method=method,
        headers={"Content-Type": "application/json"},
        data=json.dumps(body).encode() if body else None,
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {"raw": e.read().decode(errors="replace")}


ok_count = 0
fail_count = 0


def check(n, label, cond, detail=""):
    global ok_count, fail_count
    mark = "✓" if cond else "✗"
    if cond:
        ok_count += 1
    else:
        fail_count += 1
    print(f"  {mark} {n:>2}. {label:<24} {detail}")


print("=" * 70)
print("  业务闭环实测")
print("=" * 70)
print()
print("── 用户侧 ──")
print()

# 1. 浏览商品
s, r = call("GET", "/products?size=100")
n_products = len(r.get("data", {}).get("items", []))
check(1, "浏览商品", s == 200 and n_products > 0, f"{n_products} 个")

# 2. 看商品详情
s, r = call("GET", "/products/TW-001")
p = r.get("data", {})
check(2, "商品详情", s == 200 and p.get("name"), f"{p.get('name')} ¥{p.get('price')}")

# 3. 查配送可用性
s, r = call("GET", "/products/TW-001/availability")
check(3, "配送可用性", s == 200, str(r.get("data", {}))[:40])

# 4. 下单（游客）
s, r = call("POST", "/orders", {
    "items": [{"product_id": "TW-001", "qty": 1}],
    "receiver": {
        "name": "闭环测试",
        "phone": "13900001111",
        "province": "广东省",
        "city": "深圳市",
        "district": "南山区",
        "detail": "测试路 1 号",
    },
    "card_message": "闭环测试",
})
order_no = r.get("data", {}).get("order_no")
check(4, "创建订单", bool(order_no), order_no or str(r)[:60])

if not order_no:
    print("\n下单失败，后续跳过")
    raise SystemExit(1)

# 5. 查订单（应为待支付）
s, r = call("GET", f"/orders/{order_no}")
d = r.get("data", {})
check(5, "查订单", d.get("status") == "pending_payment", f"状态 {d.get('status')}")

# 6. 发起支付
s, r = call("POST", "/payments/create", {"order_no": order_no, "channel": "mock"})
pay = r.get("data", {})
check(6, "发起支付", bool(pay.get("payment_id")), f"payment_id {pay.get('payment_id')}")

# 7. 支付回调
s, r = call("POST", "/payments/callback", {
    "order_no": order_no,
    "trade_no": pay.get("payment_id"),
    "channel": "mock",
    "amount": str(p.get("price", "299")),
    "success": True,
})
check(7, "支付回调", s == 200, f"HTTP {s}")

# 8. 支付后查单
s, r = call("GET", f"/orders/{order_no}")
d = r.get("data", {})
check(8, "支付后状态", d.get("status") == "paid", f"状态 {d.get('status')}")

# 9. 重复支付回调（幂等）
s, r = call("POST", "/payments/callback", {
    "order_no": order_no, "trade_no": pay.get("payment_id"),
    "channel": "mock", "amount": "299", "success": True,
})
check(9, "重复回调幂等", s in (200, 409), f"HTTP {s}")

print()
print("── 后台侧 ──")
print()

# 10. 管理员登录（遇限流等 61 秒重试）
import time as _t

s, r = call("POST", "/auth/send-code", {"phone": PHONE})

if r.get("code") == "SMS_TOO_FREQUENT":
    print("     （验证码限流，等 61 秒…）")
    _t.sleep(61)
    s, r = call("POST", "/auth/send-code", {"phone": PHONE})

code = r.get("data", {}).get("dev_code")
s, r = call("POST", "/auth/login", {"phone": PHONE, "code": code or "000000"})
token = r.get("data", {}).get("token")
check(10, "管理员登录", bool(token), "token 已获取" if token else str(r)[:70])

if not token:
    raise SystemExit(1)

# 11. 看后台订单列表
s, r = call("GET", "/admin/orders?size=100", token=token)
orders = r.get("data", {}).get("items", [])
found = any(o.get("order_no") == order_no for o in orders)
check(11, "后台看到订单", s == 200 and found, f"列表 {len(orders)} 笔，含本单 {found}")

# 12. 后台统计
s, r = call("GET", "/admin/stats", token=token)
st = r.get("data", {})
check(12, "后台统计", s == 200, f"今日 {st.get('orders_today')} 单，¥{st.get('revenue')}")

# 13. 推进订单状态（4 步）
print()
print("── 订单状态推进 ──")
print()
chain = [
    ("preparing", "配花中"),
    ("delivering", "配送中"),
    ("delivered", "已送达"),
    ("completed", "已完成"),
]
all_ok = True
for target, cn in chain:
    s, r = call("POST", f"/orders/{order_no}/status?to_status={target}", token=token)
    cur = r.get("data", {}).get("status") if s == 200 else None
    good = cur == target
    all_ok = all_ok and good
    check(13, f"推进 → {cn}", good, f"{cur or str(r)[:40]}")

# 14. 非法流转（跳步）
s, r = call("POST", f"/orders/{order_no}/status?to_status=paid", token=token)
check(14, "非法流转被拒", s == 409, f"HTTP {s}（预期 409）")

print()
print("── 售后 ──")
print()

# 15. 用户提工单
s, r = call("POST", "/tickets", {
    "order_no": order_no,
    "type": "quality",
    "reason": "闭环测试：花材不新鲜，申请售后",
    "contact_phone": "13900001111",
})
ticket_no = r.get("data", {}).get("ticket_no")
check(15, "用户提工单", bool(ticket_no), ticket_no or str(r)[:60])

if ticket_no:
    # 16. 后台看到工单
    s, r = call("GET", "/tickets?size=50", token=token)
    tickets = r.get("data", {}).get("items", [])
    found_t = any(t.get("ticket_no") == ticket_no for t in tickets)
    check(16, "后台看到工单", found_t, f"列表 {len(tickets)} 条")

    # 17. 后台回复
    s, r = call("POST", f"/tickets/{ticket_no}/reply", {
        "reply": "非常抱歉，我们安排补送一束。",
    }, token=token)
    check(17, "后台回复工单", s == 200, f"HTTP {s}")

    # 18. 查工单状态
    s, r = call("GET", f"/tickets/{ticket_no}")
    d = r.get("data", {})
    check(18, "工单状态变更", d.get("status") in ("replied", "processing", "resolved"),
          f"状态 {d.get('status')}")

print()
print("=" * 70)
print(f"  通过 {ok_count} / {ok_count + fail_count}")
print("=" * 70)
