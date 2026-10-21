# -*- coding: utf-8 -*-
"""给所有页面注入交互 JS（购物袋、筛选、选择等）"""

import os, glob

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

# 通用购物袋 JS（所有页面都需要）
CART_JS = '''
<script>
/* ═══════════════════════════════════════════════
   购物袋（全站共用）
   ═══════════════════════════════════════════════ */
(function(){
  const FREE = 199;

  window.TWL = {
    getCart() {
      try { return JSON.parse(localStorage.getItem('twl_cart') || '[]'); }
      catch { return []; }
    },
    setCart(items) {
      localStorage.setItem('twl_cart', JSON.stringify(items));
      this.updateBadge();
    },
    addToCart(item) {
      const items = this.getCart();
      const exist = items.find(i => i.id === item.id);
      if (exist) exist.qty += item.qty || 1;
      else items.push({ ...item, qty: item.qty || 1 });
      this.setCart(items);
      this.toast('已加入购物袋');
    },
    count() {
      return this.getCart().reduce((s, i) => s + i.qty, 0);
    },
    subtotal() {
      return this.getCart().reduce((s, i) => s + i.price * i.qty, 0);
    },
    updateBadge() {
      const n = this.count();
      document.querySelectorAll('.bag-count').forEach(el => {
        el.textContent = n;
        el.style.display = n > 0 ? 'inline' : 'none';
      });
    },
    toast(msg, ms) {
      let el = document.getElementById('__toast');
      if (!el) {
        el = document.createElement('div');
        el.id = '__toast';
        el.style.cssText = 'position:fixed;left:50%;bottom:80px;transform:translateX(-50%);background:rgba(26,26,26,.92);color:#fff;padding:12px 24px;font-size:14px;border-radius:4px;z-index:99999;opacity:0;transition:opacity .25s;white-space:nowrap;';
        document.body.appendChild(el);
      }
      el.textContent = msg;
      el.style.opacity = '1';
      clearTimeout(el.__t);
      el.__t = setTimeout(() => { el.style.opacity = '0'; }, ms || 2000);
    }
  };

  /* 初始化默认购物袋 */
  if (!localStorage.getItem('twl_cart_init')) {
    localStorage.setItem('twl_cart', JSON.stringify([
      { id: 'TW-001', name: '晨光序曲', spec: '香槟玫瑰 20 枝 · 满天星', price: 299, qty: 1, img: '' },
      { id: 'TW-004', name: '木星', spec: '向日葵 6 枝 · 尤加利叶', price: 219, qty: 1, img: '' }
    ]));
    localStorage.setItem('twl_cart_init', '1');
  }

  /* 页面加载后更新角标 */
  document.addEventListener('DOMContentLoaded', () => TWL.updateBadge());
  if (document.readyState !== 'loading') TWL.updateBadge();
})();
</script>
'''

# ══════════════════════════════════════════════════════════
# 每个页面的专属交互 JS
# ══════════════════════════════════════════════════════════
PAGE_JS = {

# ── 商品详情：尺寸/包装/数量/加购 ──
"product.html": '''
<script>
(function(){
  // 尺寸切换
  document.querySelectorAll('.size').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.size').forEach(x => x.classList.remove('on'));
      el.classList.add('on');
      const pick = document.querySelector('.opt .lbl .pick');
      const labels = { L: '标准款', M: '中款', S: '小款', XS: '迷你款' };
      if (pick) pick.textContent = labels[el.textContent.trim()] || el.textContent.trim();
      const badge = document.querySelector('.size-preview .badge');
      if (badge) badge.textContent = el.textContent.trim();
    });
  });

  // 包装切换
  document.querySelectorAll('.wrap-btn').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.wrap-btn').forEach(x => x.classList.remove('on'));
      el.classList.add('on');
    });
  });

  // 数量
  let qty = 1;
  const qtyN = document.querySelector('.qty .n');
  const qtyBtns = document.querySelectorAll('.qty button');
  if (qtyBtns.length === 2) {
    qtyBtns[0].addEventListener('click', () => {
      qty = Math.max(1, qty - 1);
      qtyN.textContent = qty;
      qtyBtns[0].disabled = qty <= 1;
    });
    qtyBtns[1].addEventListener('click', () => {
      qty = Math.min(99, qty + 1);
      qtyN.textContent = qty;
      qtyBtns[0].disabled = false;
    });
    qtyBtns[0].disabled = true;
  }

  // 加入购物袋
  const addBtn = document.querySelector('.btn-add');
  if (addBtn) {
    addBtn.addEventListener('click', () => {
      const priceText = document.querySelector('.price-row .p').textContent;
      const price = parseInt(priceText.replace(/[^0-9]/g, ''));
      const img = document.querySelector('.gallery .main img')?.src || '';
      TWL.addToCart({
        id: 'TW-001',
        name: '晨光序曲',
        spec: '香槟玫瑰 20 枝 · 满天星',
        price: price,
        qty: qty,
        img: img
      });
      setTimeout(() => location.href = 'cart.html', 600);
    });
  }

  // 立即购买
  const buyBtn = document.querySelector('.btn-buy');
  if (buyBtn) {
    buyBtn.addEventListener('click', () => location.href = 'checkout.html');
  }
})();
</script>
''',

# ── 商城：筛选/排序 ──
"shop.html": '''
<script>
(function(){
  // 分类筛选
  document.querySelectorAll('.chip').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.chip').forEach(x => x.classList.remove('on'));
      el.classList.add('on');
      const cat = el.textContent.trim();
      const cards = document.querySelectorAll('.grid .card');
      let shown = 0;
      cards.forEach(c => {
        const name = c.querySelector('h3')?.textContent || '';
        const match = cat === '全部' || cat === 'Flower' || Math.random() > 0.4;
        c.style.display = 'block';
        shown++;
      });
      TWL.toast('筛选：' + cat);
    });
  });

  // 排序
  const sortEl = document.querySelector('.sorts .s');
  if (sortEl) {
    const opts = ['推荐', '价格从低到高', '价格从高到低', '最新'];
    let idx = 0;
    sortEl.addEventListener('click', () => {
      idx = (idx + 1) % opts.length;
      sortEl.innerHTML = opts[idx] + ' <span class="caret">▾</span>';
      const grid = document.querySelector('.grid');
      const cards = [...grid.querySelectorAll('.card')];
      const priceOf = c => parseInt((c.querySelector('.price')?.textContent || '0').replace(/[^0-9]/g, '')) || 0;
      if (opts[idx] === '价格从低到高') cards.sort((a,b) => priceOf(a) - priceOf(b));
      else if (opts[idx] === '价格从高到低') cards.sort((a,b) => priceOf(b) - priceOf(a));
      cards.forEach(c => grid.appendChild(c));
      TWL.toast('排序：' + opts[idx]);
    });
  }

  // 筛选按钮
  document.querySelectorAll('.filters .f').forEach(el => {
    el.addEventListener('click', () => TWL.toast('筛选面板开发中'));
  });
})();
</script>
''',

# ── 我的订单：状态筛选 ──
"orders.html": '''
<script>
(function(){
  const tabs = document.querySelectorAll('.tabs a');
  tabs.forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      tabs.forEach(x => x.classList.remove('on'));
      el.classList.add('on');
      TWL.toast('筛选：' + el.textContent.trim());
    });
  });
})();
</script>
''',

# ── 申请售后：类型选择 ──
"after-sale.html": '''
<script>
(function(){
  document.querySelectorAll('.type').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.type').forEach(x => x.classList.remove('on'));
      el.classList.add('on');
    });
  });

  const submit = document.querySelector('.submit');
  if (submit) {
    submit.addEventListener('click', () => {
      const desc = document.querySelector('textarea')?.value.trim();
      if (!desc || desc.length < 5) {
        TWL.toast('请先描述具体问题');
        return;
      }
      TWL.toast('售后申请已提交，客服 2 小时内联系你');
      submit.textContent = '已提交';
      submit.disabled = true;
      submit.style.background = '#ccc';
    });
  }

  // 删除图片
  const x = document.querySelector('.up-thumb .x');
  if (x) {
    x.addEventListener('click', () => {
      x.parentElement.remove();
      TWL.toast('已移除图片');
    });
  }

  // 上传
  const up = document.querySelector('.up-box');
  if (up) {
    up.addEventListener('click', () => TWL.toast('请选择图片（演示环境未实现上传）'));
  }
})();
</script>
''',

# ── 登录 ──
"login.html": '''
<script>
(function(){
  const codeBtn = document.querySelector('.code-btn');
  if (codeBtn) {
    let counting = false;
    codeBtn.addEventListener('click', () => {
      const phone = document.querySelector('input[type="tel"]')?.value.trim();
      if (!/^1\d{10}$/.test(phone || '')) {
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
  }

  const loginBtn = document.querySelector('.login-btn');
  if (loginBtn) {
    loginBtn.addEventListener('click', () => {
      const phone = document.querySelector('input[type="tel"]')?.value.trim();
      const code = document.querySelector('.code-row input')?.value.trim();
      if (!/^1\d{10}$/.test(phone || '')) { TWL.toast('请填写正确的手机号'); return; }
      if (!/^\d{4,6}$/.test(code || '')) { TWL.toast('请填写验证码'); return; }
      localStorage.setItem('twl_user', JSON.stringify({ phone }));
      TWL.toast('登录成功');
      setTimeout(() => location.href = 'orders.html', 800);
    });
  }
})();
</script>
''',

# ── 搜索 ──
"search.html": '''
<script>
(function(){
  const input = document.querySelector('.search-box input');
  const head = document.querySelector('.result-head h2');
  if (input) {
    input.addEventListener('input', () => {
      const q = input.value.trim();
      head.textContent = q ? `「${q}」的搜索结果` : '全部商品';
    });
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        TWL.toast('搜索：' + input.value.trim());
      }
    });
  }

  document.querySelectorAll('.tags a').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      if (input) { input.value = el.textContent.trim(); input.dispatchEvent(new Event('input')); }
      TWL.toast('搜索：' + el.textContent.trim());
    });
  });
})();
</script>
''',

# ── 花语百科：分类筛选 ──
"flower-language.html": '''
<script>
(function(){
  document.querySelectorAll('.chip').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.chip').forEach(x => x.classList.remove('on'));
      el.classList.add('on');
      TWL.toast('筛选：' + el.textContent.trim());
    });
  });
})();
</script>
''',

# ── 地址簿 ──
"address.html": '''
<script>
(function(){
  document.querySelectorAll('.card .ops a').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      const action = el.textContent.trim();
      const card = el.closest('.card');
      const name = card.querySelector('.name')?.textContent || '';
      if (action === '删除') {
        if (confirm(`确定删除「${name}」这个地址吗？`)) {
          card.remove();
          TWL.toast('已删除');
        }
      } else {
        TWL.toast('编辑：' + name);
      }
    });
  });

  const addNew = document.querySelector('.add-new');
  if (addNew) {
    addNew.addEventListener('click', () => TWL.toast('新增地址（演示环境未实现表单）'));
  }
})();
</script>
''',

# ── 确认订单：下单 ──
"checkout.html": '''
<script>
(function(){
  const btn = document.querySelector('.pay-btn');
  if (btn) {
    btn.addEventListener('click', e => {
      e.preventDefault();
      const inputs = document.querySelectorAll('.row input');
      const name = inputs[0]?.value.trim();
      const phone = inputs[1]?.value.trim();
      const addr = inputs[2]?.value.trim();

      if (!name) { TWL.toast('请填写收花人姓名'); return; }
      if (!/^1\d{10}$/.test(phone || '')) { TWL.toast('请填写正确的手机号'); return; }
      if (!addr) { TWL.toast('请填写收花地址'); return; }

      location.href = 'pay.html';
    });
  }

  // 游客提示的按钮
  const skip = document.querySelector('.guest .act .skip');
  if (skip) {
    skip.addEventListener('click', e => {
      e.preventDefault();
      document.querySelector('.guest').style.display = 'none';
    });
  }
})();
</script>
''',

# ── 支付：方式选择 ──
"pay.html": '''
<script>
(function(){
  document.querySelectorAll('.method').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.method').forEach(x => x.classList.remove('on'));
      el.classList.add('on');
    });
  });

  const btn = document.querySelector('.confirm-btn');
  if (btn) {
    btn.addEventListener('click', e => {
      e.preventDefault();
      btn.textContent = '支付中…';
      btn.style.background = '#666';
      setTimeout(() => location.href = 'order-success.html', 900);
    });
  }

  // 倒计时
  const timer = document.querySelector('.timer .t');
  if (timer) {
    let [m, s] = timer.textContent.split(':').map(Number);
    let total = m * 60 + s;
    const t = setInterval(() => {
      total--;
      if (total <= 0) { clearInterval(t); timer.textContent = '00:00'; return; }
      const mm = String(Math.floor(total / 60)).padStart(2, '0');
      const ss = String(total % 60).padStart(2, '0');
      timer.textContent = `${mm}:${ss}`;
    }, 1000);
  }
})();
</script>
''',

# ── 下单成功：复制订单号 ──
"order-success.html": '''
<script>
(function(){
  const copy = document.querySelector('.guest-card .code .c');
  if (copy) {
    copy.addEventListener('click', () => {
      const text = document.querySelector('.guest-card .code .v').textContent.trim();
      navigator.clipboard?.writeText(text).then(() => TWL.toast('订单号已复制'));
    });
  }

  const skip = document.querySelector('.guest-card .act .skip');
  if (skip) {
    skip.addEventListener('click', e => {
      e.preventDefault();
      document.querySelector('.guest-card').style.display = 'none';
      TWL.toast('已确认保存');
    });
  }

  const go = document.querySelector('.guest-card .act .go');
  if (go) {
    go.addEventListener('click', () => location.href = 'login.html');
  }
})();
</script>
''',

# ── 订单详情 ──
"order-detail.html": '''
<script>
(function(){
  document.querySelectorAll('.actions a').forEach(el => {
    el.addEventListener('click', () => {
      TWL.toast(el.textContent.trim());
    });
  });
})();
</script>
''',

# ── 花语详情：目录跳转 ──
"flower-language-detail.html": '''
<script>
(function(){
  document.querySelectorAll('.toc a').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      const target = document.querySelector(el.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
})();
</script>
''',
}


# ══════════════════════════════════════════════════════════
# 注入
# ══════════════════════════════════════════════════════════
print("=== 注入交互 JS ===\n")

for p in sorted(glob.glob(os.path.join(PROTO, "*.html"))):
    fn = os.path.basename(p)
    if fn.startswith("_") or fn == "admin.html":
        continue

    html = open(p, encoding="utf-8").read()

    # 跳过已有交互的页面（cart.html 自己实现了）
    if "TWL.getCart" in html or "Cart.get()" in html:
        print(f"  {fn}: 已有交互，跳过")
        continue

    # 组装 JS：通用 + 专属
    js = CART_JS
    if fn in PAGE_JS:
        js += "\n" + PAGE_JS[fn]

    # 插入到 </body> 前
    html = html.replace("</body>", js + "\n</body>")
    open(p, "w", encoding="utf-8").write(html)

    has_page_js = "✓" if fn in PAGE_JS else "-"
    print(f"  {fn:32} 通用JS {has_page_js} 专属JS")

print(f"\n完成")
