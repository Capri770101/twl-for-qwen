# -*- coding: utf-8 -*-
"""安全整改完整验收"""

import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"


def req(method, path, body=None, token=None, raw=False):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            content = resp.read()
            return resp.status, (content if raw else json.loads(content))
    except urllib.error.HTTPError as e:
        content = e.read()
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, content[:200]


print("╔" + "═" * 60 + "╗")
print("║" + " 生产级安全整改 · 完整验收".center(56) + "║")
print("╚" + "═" * 60 + "╝\n")

results = []


def check(name, ok, detail=""):
    mark = "✓" if ok else "✗"
    results.append(ok)
    print(f"  {mark} {name:<38} {detail}")


# ── 1. 未登录访问后台 ──
print("【1. 后台接口鉴权】")
for path in ["/api/v1/admin/stats", "/api/v1/admin/orders", "/api/v1/admin/products", "/api/v1/admin/logs"]:
    code, _ = req("GET", path)
    check(f"{path} 未登录", code == 401, f"→ {code}")

# ── 2. 未登录访问文章管理 ──
print("\n【2. 文章管理鉴权】")
code, _ = req("GET", "/api/v1/articles/admin")
check("GET /articles/admin 未登录", code == 401, f"→ {code}")

code, _ = req("POST", "/api/v1/articles/admin", {
    "slug": "test", "title": "测试"
})
check("POST /articles/admin 未登录", code == 401, f"→ {code}")

# ── 3. 未登录改配置 ──
print("\n【3. 配置鉴权】")
code, _ = req("PUT", "/api/v1/settings/delivery", {
    "free_shipping_threshold": 1, "base_shipping_fee": 0,
    "remote_shipping_fee": 0, "same_city_hours": 1,
    "cutoff_hour": 23, "delivery_slots": [], "payment_timeout_minutes": 30,
    "service_hours": "x"
})
check("PUT /settings/delivery 未登录", code == 401, f"→ {code}")

# ── 4. 未登录上传 ──
print("\n【4. 上传鉴权】")
import urllib.request as ur
import uuid
boundary = uuid.uuid4().hex
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="t.png"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode() + b"\x89PNG\r\n\x1a\n" + f"\r\n--{boundary}--\r\n".encode()

r = ur.Request(BASE + "/api/v1/uploads", data=body, method="POST")
r.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
try:
    with ur.urlopen(r, timeout=10) as resp:
        check("POST /uploads 未登录", False, f"→ {resp.status}（不应该）")
except urllib.error.HTTPError as e:
    check("POST /uploads 未登录", e.code == 401, f"→ {e.code}")

# ── 5. 限流 ──
print("\n【5. 限流】")
import random as _r
_rate_phone = "137" + str(_r.randint(10000000, 99999999))
code1, d1 = req("POST", "/api/v1/auth/send-code", {"phone": _rate_phone})
check("第 1 次发码", code1 == 200, f"→ {code1}")

code2, d2 = req("POST", "/api/v1/auth/send-code", {"phone": _rate_phone})
blocked = code2 != 200 or (isinstance(d2, dict) and d2.get("code") == "SMS_TOO_FREQUENT")
check("第 2 次发码被拦截", blocked, f"→ {code2} {d2.get('code') if isinstance(d2, dict) else ''}")

dev_code = d1["data"]["dev_code"] if code1 == 200 else None

# ── 6. 登录 ──
print("\n【6. 登录】")
if dev_code:
    code3, d3 = req("POST", "/api/v1/auth/login", {"phone": _rate_phone, "code": dev_code})
    check("登录成功", code3 == 200, f"→ {code3}")
    token_user = d3["data"]["token"] if code3 == 200 else None
    is_admin_user = d3["data"]["user"]["is_admin"] if code3 == 200 else None
    check("普通用户 is_admin=False", is_admin_user is False, f"→ {is_admin_user}")

    # 普通用户访问后台应 403
    code4, _ = req("GET", "/api/v1/admin/stats", token=token_user)
    check("普通用户访问后台", code4 == 403, f"→ {code4}")

# ── 7. 管理员登录 ──
print("\n【7. 管理员】")
code5, d5 = req("POST", "/api/v1/auth/send-code", {"phone": "13800001234"})
if code5 == 200:
    admin_code = d5["data"]["dev_code"]
    code6, d6 = req("POST", "/api/v1/auth/login", {"phone": "13800001234", "code": admin_code})
    if code6 == 200:
        admin_token = d6["data"]["token"]
        check("管理员 is_admin=True", d6["data"]["user"]["is_admin"] is True)

        code7, _ = req("GET", "/api/v1/admin/stats", token=admin_token)
        check("管理员访问后台", code7 == 200, f"→ {code7}")

        code8, _ = req("GET", "/api/v1/articles/admin", token=admin_token)
        check("管理员访问文章管理", code8 == 200, f"→ {code8}")

        # ── 8. 退出登录 ──
        print("\n【8. Token 黑名单】")
        code9, _ = req("POST", "/api/v1/auth/logout", token=admin_token)
        check("退出登录", code9 == 200, f"→ {code9}")

        import time
        time.sleep(0.3)
        code10, _ = req("GET", "/api/v1/auth/me", token=admin_token)
        check("退出后 token 失效", code10 == 401, f"→ {code10}")
    else:
        print(f"  管理员登录失败: {code6}")
else:
    print(f"  管理员发码被限流（60秒内已发过）")

# ── 汇总 ──
print()
print("═" * 62)
total = len(results)
passed = sum(results)
print(f"  通过 {passed} / {total}")
if passed == total:
    print("  全部通过")
else:
    print(f"  {total - passed} 项未通过")
print("═" * 62)
