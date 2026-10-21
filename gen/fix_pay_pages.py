# -*- coding: utf-8 -*-
"""修正支付页和成功页，适配真实 API 字段"""

import os, re

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

# ══════════════════════════════════════════════════════════
# 1. 修 pay.html
# ══════════════════════════════════════════════════════════
pay_path = os.path.join(PROTO, "pay.html")
html = open(pay_path, encoding="utf-8").read()

# 把整个 <script> 段替换掉
new_script = '''<script>
(function(){
  const params = new URLSearchParams(location.search);
  const orderNo = params.get('order_no') || localStorage.getItem('twl_last_order');

  if (!orderNo) {
    alert('没有找到订单，请重新下单');
    location.href = 'shop.html';
    return;
  }

  document.getElementById('orderNo').textContent = orderNo;

  let channel = 'mock';
  let amount = 0;

  /* 加载订单信息 */
  (async () => {
    try {
      const o = await API.getOrder(orderNo);
      amount = parseFloat(o.pay_amount || 0);
      document.getElementById('amt').textContent = API.money(amount);
      document.getElementById('sub').textContent = '¥' + API.money(o.total_amount);
      const shipFee = parseFloat(o.delivery_fee || 0);
      document.getElementById('ship').textContent = shipFee > 0 ? '¥' + API.money(shipFee) : '免运费';
    } catch (e) {
      API.toast('订单加载失败：' + e.message);
    }
  })();

  /* 选渠道 */
  document.querySelectorAll('.method').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.method').forEach(x => x.classList.remove('on'));
      el.classList.add('on');
      channel = el.dataset.ch;
    });
  });

  /* 倒计时 */
  let total = 30 * 60;
  const timerEl = document.getElementById('timer');
  const timer = setInterval(() => {
    total--;
    if (total <= 0) { clearInterval(timer); timerEl.textContent = '00:00'; return; }
    const m = String(Math.floor(total / 60)).padStart(2, '0');
    const s = String(total % 60).padStart(2, '0');
    timerEl.textContent = m + ':' + s;
  }, 1000);

  /* 支付 */
  const btn = document.getElementById('payBtn');
  btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.textContent = '支付中…';

    try {
      // 1. 创建支付单
      const r = await API.createPayment(orderNo, channel);

      if (channel === 'mock') {
        // 2. mock 渠道：直接触发后端"支付成功"端点
        //    （后端处理完会更新订单状态，但返回 404，所以用 catch 吞掉）
        await fetch(r.mock_pay_url.replace('/mock/pay', '/mock/success'), {
          mode: 'no-cors',
        }).catch(() => {});

        // 3. 等后端处理完
        await new Promise(res => setTimeout(res, 900));

        // 4. 查订单确认状态
        const o = await API.getOrder(orderNo);
        if (o.status === 'paid' || o.status === 'preparing' || o.status === 'delivering') {
          location.href = 'order-success.html?order_no=' + encodeURIComponent(orderNo);
        } else {
          API.toast('支付未完成，当前状态：' + (o.status_text || o.status));
          btn.disabled = false;
          btn.textContent = '确认支付';
        }
      } else {
        API.toast('该渠道未接入，请用模拟支付');
        btn.disabled = false;
        btn.textContent = '确认支付';
      }
    } catch (e) {
      API.toast(e.message);
      btn.disabled = false;
      btn.textContent = '确认支付';
    }
  });
})();
</script>'''

# 替换最后一个 <script> 块
pattern = r'<script>\s*\(function\(\)\{\s*const params = new URLSearchParams[\s\S]*?</script>'
html_new = re.sub(pattern, new_script, html, count=1)

if html_new == html:
    print("  pay.html: 未匹配到脚本，尝试直接替换")
else:
    html = html_new

# 补一个渠道字段
html = html.replace('data-ch="mock"', 'data-ch="mock"')

open(pay_path, "w", encoding="utf-8").write(html)
print("  pay.html 已更新")


# ══════════════════════════════════════════════════════════
# 2. 修 order-success.html
# ══════════════════════════════════════════════════════════
ok_path = os.path.join(PROTO, "order-success.html")
html = open(ok_path, encoding="utf-8").read()

# 找主内容区替换
new_main = '''<div class="res-wrap" id="app">
  <div class="loading">加载订单…</div>
</div>

<script>
(function(){
  const params = new URLSearchParams(location.search);
  const orderNo = params.get('order_no') || localStorage.getItem('twl_last_order');
  const app = document.getElementById('app');

  if (!orderNo) {
    app.innerHTML = '<div style="padding:120px 40px;text-align:center;color:#999">没有找到订单</div>';
    return;
  }

  const STATUS_ORDER = ['pending_payment', 'paid', 'preparing', 'delivering', 'delivered', 'completed'];
  const STATUS_LABEL = {
    pending_payment: '待支付',
    paid: '已支付',
    preparing: '配花中',
    delivering: '配送中',
    delivered: '已送达',
    completed: '已完成',
    cancelled: '已取消',
  };

  function fmtTime(t) {
    if (!t) return '—';
    return String(t).replace('T', ' ').slice(0, 16);
  }

  function render(o) {
    const curIdx = STATUS_ORDER.indexOf(o.status);

    // 时间线
    const steps = STATUS_ORDER.slice(1, 6).map((s, i) => {
      const idx = i + 1;
      let cls = '';
      if (idx < curIdx) cls = 'done';
      else if (idx === curIdx) cls = 'now';
      const tl = (o.timeline || []).find(t => t.status === s);
      const time = tl ? fmtTime(tl.time) : '—';
      return `
        <div class="step ${cls}">
          <div class="dot"></div>
          <div class="txt">
            <div class="t">${STATUS_LABEL[s] || s}</div>
            <div class="d">${time}</div>
          </div>
        </div>
      `;
    }).join('');

    // 商品
    const items = (o.items || []).map(it => `
      <div class="drow"><span class="k">${it.product_name}</span><span class="v">×${it.qty}</span></div>
    `).join('');

    app.innerHTML = `
      <div class="res-left">
        <h1><span class="mark">✓</span>下单成功</h1>
        <div class="no">${o.order_no}</div>

        <div class="timeline-title">订单进度</div>
        ${steps}
      </div>

      <div class="res-right">

        <div class="guest-card">
          <div class="t"><span class="dot">!</span>请保存好订单号</div>
          <p>这是你查询订单的唯一凭据。换设备或清缓存后无法再看到。</p>
          <div class="code">
            <span class="v">${o.order_no}</span>
            <span class="c" id="copyBtn">复制</span>
          </div>
          <div class="act">
            <a href="login.html" class="go">登录并绑定</a>
            <a href="#" class="skip" id="skipBtn">我已截图</a>
          </div>
        </div>

        <div class="detail-card">
          <h2>订单详情</h2>
          ${items}
          <div class="drow"><span class="k">收花人</span><span class="v">${o.receiver} ${String(o.phone || '').replace(/(\\d{3})\\d{4}(\\d{4})/, '$1****$2')}</span></div>
          <div class="drow"><span class="k">地址</span><span class="v">${o.address_detail || '—'}</span></div>
          <div class="drow"><span class="k">送达</span><span class="v">${o.delivery_date || '今日'} ${o.delivery_slot || ''}</span></div>
          ${o.card_message ? `<div class="drow"><span class="k">贺卡</span><span class="v">${o.card_message}</span></div>` : ''}
          <div class="drow"><span class="k">实付</span><span class="v price">¥${API.money(o.pay_amount)}</span></div>

          <div class="actions">
            <a href="order-detail.html?order_no=${encodeURIComponent(o.order_no)}" class="primary">查看订单</a>
            <a href="shop.html" class="ghost">继续逛逛</a>
          </div>
        </div>

      </div>
    `;

    // 复制
    document.getElementById('copyBtn').addEventListener('click', () => {
      navigator.clipboard?.writeText(o.order_no).then(() => API.toast('订单号已复制'));
    });

    document.getElementById('skipBtn').addEventListener('click', e => {
      e.preventDefault();
      document.querySelector('.guest-card').style.display = 'none';
      API.toast('已确认保存');
    });
  }

  (async () => {
    try {
      const o = await API.getOrder(orderNo);
      render(o);
    } catch (e) {
      app.innerHTML = `<div style="padding:120px 40px;text-align:center;color:#999">订单加载失败：${e.message}</div>`;
    }
  })();
})();
</script>'''

# 替换从 <div class="res-wrap"> 到最后一个 </script>
start = html.find('<div class="res-wrap"')
end = html.rfind('</script>') + len('</script>')

if start > 0 and end > start:
    html = html[:start] + new_main + html[end:]
    open(ok_path, "w", encoding="utf-8").write(html)
    print("  order-success.html 已更新")
else:
    print("  order-success.html: 未找到替换位置")

print("\n完成")
