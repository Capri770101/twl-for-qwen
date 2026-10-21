# -*- coding: utf-8 -*-
"""阶段4：售后上传 + 登录页存 token"""

import os

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"


# ══════════════════════════════════════════════════════════
# 1. 售后页：图片上传接真实接口
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "after-sale.html")
html = open(p, encoding="utf-8").read()

old_js = '''  // 上传提示
  const up = document.querySelector('.up-box');
  if (up) up.addEventListener('click', () => API.toast('演示环境不支持上传，图片字段会留空'));

  const x = document.querySelector('.up-thumb .x');
  if (x) x.addEventListener('click', () => { x.parentElement.remove(); API.toast('已移除图片'); });'''

new_js = '''  // ═══ 图片上传（接真实接口）═══
  const uploadedImages = [];

  const up = document.querySelector('.up-box');
  if (up) {
    // 建一个隐藏的 file input
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput);

    up.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async () => {
      const file = fileInput.files[0];
      if (!file) return;

      // 大小检查
      if (file.size > 5 * 1024 * 1024) {
        API.toast('图片超过 5MB');
        fileInput.value = '';
        return;
      }

      const token = localStorage.getItem('twl_token');
      if (!token) {
        API.toast('请先登录才能上传图片');
        fileInput.value = '';
        return;
      }

      up.innerHTML = '<span style="font-size:12px;color:#999">上传中…</span>';

      try {
        const fd = new FormData();
        fd.append('file', file);

        const r = await fetch('/api/v1/uploads', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + token },
          body: fd,
        });
        const j = await r.json();

        if (j.code !== 0) throw new Error(j.message || '上传失败');

        uploadedImages.push(j.data.url);

        // 插入缩略图
        const thumb = document.createElement('div');
        thumb.className = 'up-thumb';
        thumb.innerHTML = `
          <img src="${j.data.url}" alt="上传的图片">
          <div class="x">×</div>
        `;
        thumb.querySelector('.x').addEventListener('click', () => {
          const idx = uploadedImages.indexOf(j.data.url);
          if (idx > -1) uploadedImages.splice(idx, 1);
          thumb.remove();
          API.toast('已移除');
        });
        up.parentElement.insertBefore(thumb, up);

        API.toast('已上传');
        up.innerHTML = '<span style="font-size:20px">＋</span><span>添加</span>';
      } catch (e) {
        API.toast(e.message);
        up.innerHTML = '<span style="font-size:20px">＋</span><span>添加</span>';
      }

      fileInput.value = '';
    });
  }

  // 已有的删除按钮
  const x = document.querySelector('.up-thumb .x');
  if (x) x.addEventListener('click', () => { x.parentElement.remove(); API.toast('已移除图片'); });'''

if old_js in html:
    html = html.replace(old_js, new_js, 1)
    print("  after-sale.html: 图片上传接真实接口")

# 提交时带图片
old_submit = '''      const r = await API.createTicket({
        order_no: orderNo,
        type: curType,
        reason: reason,
        images: [],
        contact_phone: phone || null,
      });'''

new_submit = '''      const r = await API.createTicket({
        order_no: orderNo,
        type: curType,
        reason: reason,
        images: uploadedImages,
        contact_phone: phone || null,
      });'''

if old_submit in html:
    html = html.replace(old_submit, new_submit, 1)
    print("  after-sale.html: 提交带图片")

open(p, "w", encoding="utf-8").write(html)


# ══════════════════════════════════════════════════════════
# 2. 登录页：存 token 到 localStorage
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "login.html")
html = open(p, encoding="utf-8").read()

old_login = '''  const loginBtn = document.querySelector('.login-btn');
  if (loginBtn) {
    loginBtn.addEventListener('click', () => {
      const phone = document.querySelector('input[type="tel"]')?.value.trim();
      const code = document.querySelector('.code-row input')?.value.trim();
      if (!/^1\\d{10}$/.test(phone || '')) { TWL.toast('请填写正确的手机号'); return; }
      if (!/^\\d{4,6}$/.test(code || '')) { TWL.toast('请填写验证码'); return; }
      localStorage.setItem('twl_user', JSON.stringify({ phone }));
      TWL.toast('登录成功');
      setTimeout(() => location.href = 'orders.html', 800);
    });
  }'''

new_login = '''  const loginBtn = document.querySelector('.login-btn');
  if (loginBtn) {
    loginBtn.addEventListener('click', async () => {
      const phone = document.querySelector('input[type="tel"]')?.value.trim();
      const code = document.querySelector('.code-row input')?.value.trim();

      if (!/^1\\d{10}$/.test(phone || '')) { TWL.toast('请填写正确的手机号'); return; }
      if (!/^\\d{4,6}$/.test(code || '')) { TWL.toast('请填写验证码'); return; }

      loginBtn.disabled = true;
      loginBtn.textContent = '登录中…';

      try {
        const r = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone, code }),
        });
        const j = await r.json();

        if (j.code !== 0) {
          TWL.toast(j.message || '登录失败');
          loginBtn.disabled = false;
          loginBtn.textContent = '登 录';
          return;
        }

        // 存 token 和用户信息
        localStorage.setItem('twl_token', j.data.token);
        localStorage.setItem('twl_user', JSON.stringify(j.data.user));

        TWL.toast(j.data.is_new ? '注册成功' : '登录成功');
        setTimeout(() => location.href = 'orders.html', 700);

      } catch (e) {
        TWL.toast('网络错误：' + e.message);
        loginBtn.disabled = false;
        loginBtn.textContent = '登 录';
      }
    });
  }'''

if old_login in html:
    html = html.replace(old_login, new_login, 1)
    print("  login.html: 接真实登录")

# 验证码按钮也走真实接口
old_code = '''  const codeBtn = document.querySelector('.code-btn');
  if (codeBtn) {
    let counting = false;
    codeBtn.addEventListener('click', () => {
      const phone = document.querySelector('input[type="tel"]')?.value.trim();
      if (!/^1\\d{10}$/.test(phone || '')) {
        TWL.toast('请先填写正确的手机号');
        return;
      }
      if (counting) return;
      counting = true;
      let n = 60;
      codeBtn.textContent = n + 's';
      codeBtn.disabled = true;
      const t = setInterval(() => {
        n--;
        codeBtn.textContent = n + 's';
        if (n <= 0) {
          clearInterval(t);
          counting = false;
          codeBtn.textContent = '获取验证码';
          codeBtn.disabled = false;
        }
      }, 1000);
      TWL.toast('验证码已发送（演示环境）');
    });
  }'''

new_code = '''  const codeBtn = document.querySelector('.code-btn');
  if (codeBtn) {
    let counting = false;
    codeBtn.addEventListener('click', async () => {
      const phone = document.querySelector('input[type="tel"]')?.value.trim();
      if (!/^1\\d{10}$/.test(phone || '')) {
        TWL.toast('请先填写正确的手机号');
        return;
      }
      if (counting) return;

      counting = true;
      codeBtn.textContent = '发送中…';
      codeBtn.disabled = true;

      try {
        const r = await fetch('/api/v1/auth/send-code', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone }),
        });
        const j = await r.json();

        if (j.code !== 0) {
          TWL.toast(j.message || '发送失败');
          counting = false;
          codeBtn.textContent = '获取验证码';
          codeBtn.disabled = false;
          return;
        }

        // 开发环境自动填
        if (j.data.dev_code) {
          document.querySelector('.code-row input').value = j.data.dev_code;
          TWL.toast('开发环境：验证码已自动填入');
        } else {
          TWL.toast('验证码已发送');
        }

        let n = 60;
        codeBtn.textContent = n + 's';
        const t = setInterval(() => {
          n--;
          codeBtn.textContent = n + 's';
          if (n <= 0) {
            clearInterval(t);
            counting = false;
            codeBtn.textContent = '获取验证码';
            codeBtn.disabled = false;
          }
        }, 1000);

      } catch (e) {
        TWL.toast('网络错误：' + e.message);
        counting = false;
        codeBtn.textContent = '获取验证码';
        codeBtn.disabled = false;
      }
    });
  }'''

if old_code in html:
    html = html.replace(old_code, new_code, 1)
    print("  login.html: 验证码接真实接口")

open(p, "w", encoding="utf-8").write(html)


# ══════════════════════════════════════════════════════════
# 3. api.js 加 request 方法
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "api.js")
html = open(p, encoding="utf-8").read()

if "async request(" not in html:
    # 在 return { 后面加 request 方法
    html = html.replace(
        "  return {\n    /* ── 商品 ── */",
        "  return {\n    /* ── 通用请求（公开） ── */\n    request,\n\n    /* ── 商品 ── */"
    )
    open(p, "w", encoding="utf-8").write(html)
    print("  api.js: 暴露 request 方法")
else:
    print("  api.js: 已有 request")


print("\n完成")
