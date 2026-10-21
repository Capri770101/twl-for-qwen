# -*- coding: utf-8 -*-
"""阶段2：前端接入真实 API（后台登录 / 地址簿 / 花语 / 售后上传）"""

import os

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"


# ══════════════════════════════════════════════════════════
# 1. 后台登录接真实 API
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "admin.html")
html = open(p, encoding="utf-8").read()

# 替换登录逻辑
old_login = '''  /* ═══ 登录逻辑 ═══ */
  const ACC = 'admin';
  const PWD = 'twl2026';
  const KEY = 'twl_admin_auth';

  function doLogin() {
    const a = document.getElementById('acc').value.trim();
    const p = document.getElementById('pwd').value;
    const err = document.getElementById('err');

    if (a === ACC && p === PWD) {
      sessionStorage.setItem(KEY, '1');
      err.classList.remove('on');
      showApp();
    } else {
      err.classList.add('on');
      document.getElementById('pwd').value = '';
    }
  }

  function doLogout() {
    sessionStorage.removeItem(KEY);
    location.reload();
  }'''

new_login = '''  /* ═══════════════════════════════════════════════
     登录逻辑（接真实后端）
     ═══════════════════════════════════════════════ */
  const KEY = 'twl_admin_token';
  const USER_KEY = 'twl_admin_user';

  let _smsCooldown = false;

  /* 获取验证码 */
  async function sendCode() {
    const phone = document.getElementById('acc').value.trim();

    if (!/^1\\d{10}$/.test(phone)) {
      showErr('请填写正确的手机号');
      return;
    }
    if (_smsCooldown) return;

    const btn = document.getElementById('codeBtn');
    btn.disabled = true;
    btn.textContent = '发送中…';

    try {
      const r = await fetch('/api/v1/auth/send-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone }),
      });
      const j = await r.json();

      if (j.code !== 0) {
        showErr(j.message || '发送失败');
        btn.disabled = false;
        btn.textContent = '获取验证码';
        return;
      }

      // 开发环境：直接显示验证码
      if (j.data.dev_code) {
        document.getElementById('pwd').value = j.data.dev_code;
        showErr('开发环境：验证码已自动填入（' + j.data.dev_code + '）', true);
      } else {
        showErr('验证码已发送，请查收短信', true);
      }

      // 倒计时
      _smsCooldown = true;
      let n = 60;
      btn.textContent = n + 's';
      const t = setInterval(() => {
        n--;
        btn.textContent = n + 's';
        if (n <= 0) {
          clearInterval(t);
          _smsCooldown = false;
          btn.textContent = '获取验证码';
          btn.disabled = false;
        }
      }, 1000);

    } catch (e) {
      showErr('网络错误：' + e.message);
      btn.disabled = false;
      btn.textContent = '获取验证码';
    }
  }

  /* 登录 */
  async function doLogin() {
    const phone = document.getElementById('acc').value.trim();
    const code = document.getElementById('pwd').value.trim();

    if (!/^1\\d{10}$/.test(phone)) {
      showErr('请填写正确的手机号');
      return;
    }
    if (!code) {
      showErr('请填写验证码');
      return;
    }

    const btn = document.getElementById('loginBtn');
    btn.disabled = true;
    btn.textContent = '登录中…';

    try {
      const r = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code }),
      });
      const j = await r.json();

      if (j.code !== 0) {
        showErr(j.message || '登录失败');
        btn.disabled = false;
        btn.textContent = '登 录';
        return;
      }

      // 检查是不是管理员
      if (!j.data.user.is_admin) {
        showErr('这个账号不是管理员，无法进入后台');
        btn.disabled = false;
        btn.textContent = '登 录';
        return;
      }

      // 存 token
      sessionStorage.setItem(KEY, j.data.token);
      sessionStorage.setItem(USER_KEY, JSON.stringify(j.data.user));

      hideErr();
      showApp();

    } catch (e) {
      showErr('网络错误：' + e.message);
      btn.disabled = false;
      btn.textContent = '登 录';
    }
  }

  /* 退出 */
  async function doLogout() {
    const token = sessionStorage.getItem(KEY);

    if (token) {
      try {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + token },
        });
      } catch (e) { /* 忽略 */ }
    }

    sessionStorage.removeItem(KEY);
    sessionStorage.removeItem(USER_KEY);
    location.reload();
  }

  /* 错误提示 */
  function showErr(msg, ok) {
    const el = document.getElementById('err');
    el.textContent = msg;
    el.classList.add('on');
    el.style.background = ok ? '#f0f7f1' : '#faf0f0';
    el.style.borderColor = ok ? '#b5cbb9' : '#d5b0b0';
    el.style.color = ok ? '#3d6b47' : '#8a3c3c';
  }

  function hideErr() {
    document.getElementById('err').classList.remove('on');
  }'''

if old_login in html:
    html = html.replace(old_login, new_login, 1)
    print("  admin.html: 登录接真实 API")
else:
    print("  admin.html: 未匹配登录逻辑，跳过")


# 更新登录表单的 HTML（手机号 + 验证码）
old_form = '''    <div class="gate-field">
      <label>账号</label>
      <input type="text" id="acc" placeholder="admin" autocomplete="username">
    </div>

    <div class="gate-field">
      <label>密码</label>
      <input type="password" id="pwd" placeholder="请输入密码" autocomplete="current-password">
    </div>

    <button class="gate-btn" onclick="doLogin()">登 录</button>

    <div class="gate-err" id="err">账号或密码不对</div>

    <div class="gate-hint">
      演示账号 <code>admin</code> / 密码 <code>twl2026</code><br>
      正式环境需接入后端鉴权
    </div>'''

new_form = '''    <div class="gate-field">
      <label>手机号</label>
      <input type="tel" id="acc" placeholder="管理员手机号" inputmode="numeric" maxlength="11" autocomplete="username">
    </div>

    <div class="gate-field" style="display:flex;gap:12px;align-items:flex-end">
      <div style="flex:1">
        <label>验证码</label>
        <input type="text" id="pwd" placeholder="6 位数字" inputmode="numeric" maxlength="6" autocomplete="one-time-code">
      </div>
      <button id="codeBtn" onclick="sendCode()" style="flex:0 0 auto;padding:0 0 12px;background:none;border:0;font-size:13px;color:#666;text-decoration:underline;text-underline-offset:3px;cursor:pointer;font-family:inherit;white-space:nowrap">获取验证码</button>
    </div>

    <button class="gate-btn" id="loginBtn" onclick="doLogin()">登 录</button>

    <div class="gate-err" id="err"></div>

    <div class="gate-hint">
      需要管理员账号。开发环境验证码会自动填入。<br>
      把手机号设成管理员：<br>
      <code>UPDATE users SET is_admin = TRUE WHERE phone = '...'</code>
    </div>'''

if old_form in html:
    html = html.replace(old_form, new_form, 1)
    print("  admin.html: 登录表单改为手机号+验证码")

# 更新启动检查
old_startup = '''  /* ═══ 启动时检查登录状态 ═══ */
  if (sessionStorage.getItem(KEY) === '1') {
    showApp();
  } else {
    document.getElementById('acc').focus();
  }'''

new_startup = '''  /* ═══ 启动时检查登录状态 ═══ */
  if (sessionStorage.getItem(KEY)) {
    showApp();
  } else {
    document.getElementById('acc').focus();
  }'''

if old_startup in html:
    html = html.replace(old_startup, new_startup, 1)
    print("  admin.html: 启动检查更新")

# 让所有 API 请求带 token
if "API_TOKEN_PATCH" not in html:
    token_patch = '''
<script>
/* ═══ 给所有 fetch 加 token ═══ */
(function(){
  const _origFetch = window.fetch;
  window.fetch = function(url, opts) {
    opts = opts || {};
    const token = sessionStorage.getItem('twl_admin_token');

    if (token && typeof url === 'string' && url.startsWith('/api/v1')) {
      opts.headers = opts.headers || {};
      if (opts.headers instanceof Headers) {
        opts.headers.set('Authorization', 'Bearer ' + token);
      } else {
        opts.headers['Authorization'] = 'Bearer ' + token;
      }
    }

    return _origFetch(url, opts);
  };
})();
</script>
'''
    if '</body>' in html:
        html = html.replace('</body>', token_patch + '\n</body>')
        print("  admin.html: 加 token 自动注入")

open(p, "w", encoding="utf-8").write(html)

print("\n完成")
