# -*- coding: utf-8 -*-
"""退款 + 配送 完整实测"""
import json, urllib.request, urllib.error, time

BASE = "http://127.0.0.1:8000/api/v1"
ok = fail = 0

def call(method, path, body=None, token=None):
    req = urllib.request.Request(BASE+path, method=method,
        headers={"Content-Type":"application/json"},
        data=json.dumps(body).encode() if body else None)
    if token: req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        except: return e.code, {"raw":"?"}

def check(l, c, d=""):
    global ok, fail
    if c: ok += 1
    else: fail += 1
    print(f"  {'✓' if c else '✗'} {l:<30} {d}")

def login():
    s, r = call("POST","/auth/send-code",{"phone":"13800001234"})
    if r.get("code")=="SMS_TOO_FREQUENT":
        print("     （限流，等 61 秒）")
        time.sleep(61)
        s, r = call("POST","/auth/send-code",{"phone":"13800001234"})
    code = r.get("data",{}).get("dev_code")
    s, r = call("POST","/auth/login",{"phone":"13800001234","code":code or "000000"})
    return r.get("data",{}).get("token")

def paid_order(pid, name, phone, detail):
    s, r = call("POST","/orders",{
        "items":[{"product_id":pid,"qty":1}],
        "receiver":{"name":name,"phone":phone,"province":"广东省",
                    "city":"深圳市","district":"南山区","detail":detail},
    })
    no = r.get("data",{}).get("order_no")
    s, r = call("GET", f"/orders/{no}")
    amt = r.get("data",{}).get("pay_amount")
    s, r = call("POST","/payments/create",{"order_no":no,"channel":"mock"})
    pay_id = r.get("data",{}).get("payment_id")
    call("POST","/payments/callback",{
        "order_no":no,"trade_no":pay_id,"channel":"mock","amount":str(amt),"success":True})
    return no

print("=" * 70)
print("  退款 + 配送 完整实测")
print("=" * 70)
print()

token = login()
check("管理员登录", bool(token))

# ══ 退款 ══
print()
print("── 退款 ──")
print()

o1 = paid_order("TW-005", "退款测试", "13911110001", "退款路1号")
check("订单1支付", bool(o1), o1 or "")

s, r = call("POST","/refunds",{"order_no":o1,"amount":"259.00","reason":"花材不新鲜，申请全额退款"})
rf = r.get("data",{})
rn = rf.get("refund_no")
check("申请退款", bool(rn), f"{rn}")

s, r = call("POST","/refunds",{"order_no":o1,"amount":"10","reason":"重复申请测试用例"})
check("重复申请被拒", s==409, f"HTTP {s}")

s, r = call("GET","/refunds?size=20", token=token)
check("后台列表", s==200 and len(r.get("data",{}).get("items",[]))>0,
      f"{len(r.get('data',{}).get('items',[]))} 条")

s, r = call("POST",f"/refunds/{rn}/review",{"approve":True}, token)
d = r.get("data",{})
check("审核通过", s==200 and d.get("status")=="refunded",
      f"{d.get('status_text')} {d.get('external_ref','')}")

s, r = call("POST",f"/refunds/{rn}/review",{"approve":True}, token)
check("重复审核被拒", s==409, f"HTTP {s}")

o2 = paid_order("TW-006", "拒绝测试", "13911110002", "退款路2号")
s, r = call("POST","/refunds",{"order_no":o2,"amount":"100","reason":"部分退款测试用例"})
rn2 = r.get("data",{}).get("refund_no")
s, r = call("POST",f"/refunds/{rn2}/review",{"approve":False,"reject_reason":"不符合条件"}, token)
check("审核拒绝", s==200 and r.get("data",{}).get("status")=="rejected",
      r.get("data",{}).get("status_text",""))

s, r = call("POST","/refunds",{"order_no":o2,"amount":"99999","reason":"超额测试用例"})
check("超额被拒", s==422, f"HTTP {s}")

# ══ 配送 ══
print()
print("── 配送 ──")
print()

o3 = paid_order("TW-007", "配送测试", "13911110003", "配送路3号")
check("订单3支付", bool(o3), o3 or "")

s, r = call("POST", f"/deliveries/notify?order_no={o3}")
d = r.get("data",{})
check("推送履约", s==200 and d.get("delivery_id"), f"{d.get('status')}")

s, r = call("GET", f"/orders/{o3}")
check("订单变配花中", r.get("data",{}).get("status")=="preparing",
      r.get("data",{}).get("status",""))

s, r = call("GET","/deliveries?size=20", token=token)
check("后台配送列表", s==200, f"{len(r.get('data',{}).get('items',[]))} 条")

s, r = call("POST", f"/deliveries/callback?order_no={o3}&status=delivering")
check("回调→配送中", s==200, f"HTTP {s}")

s, r = call("GET", f"/orders/{o3}")
check("订单变配送中", r.get("data",{}).get("status")=="delivering",
      r.get("data",{}).get("status",""))

s, r = call("POST", f"/deliveries/callback?order_no={o3}&status=delivered")
check("回调→已送达", s==200, f"HTTP {s}")

s, r = call("GET", f"/orders/{o3}")
check("订单变已送达", r.get("data",{}).get("status")=="delivered",
      r.get("data",{}).get("status",""))

s, r = call("GET","/deliveries", )
check("未登录不能看配送", s==401, f"HTTP {s}")

print()
print("=" * 70)
print(f"  通过 {ok} / {ok + fail}")
print("=" * 70)
