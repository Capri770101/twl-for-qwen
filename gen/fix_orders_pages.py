# -*- coding: utf-8 -*-
"""订单列表 / 订单详情 / 后台 接真实 API"""

import os, re

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"


# ══════════════════════════════════════════════════════════
# 1. orders.html —— 订单列表
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "orders.html")
html = open(p, encoding="utf-8").read()

new_orders = '''<div class="page-head">
  <h1>我的订单</h1>
  <p id="subTitle">全部订单</p>
</div>

<div class="ord-wrap">

  <div class="tabs" id="tabs">
    <a href="#" data-st="all" class="on">全部</a>
    <a href="#" data-st="pending_payment">待支付</a>
    <a href="#" data-st="preparing">配花中</a>
    <a href="#" data-st="delivering">配送中</a>
    <a href="#" data-st="delivered">已送达</a>
  </div>

  <div id="orderList">
    <div style="padding:60px 0;text-align:center;color:#999;font-size:14px">加载中…</div>
  </div>

</div>

<script src="api.js"></script>
<script>
(function(){
  let allOrders = [];
  let curStatus = 'all';

  const listEl = document.getElementById('orderList');
  const subTitle = document.getElementById('subTitle');

  function render() {
    let list = allOrders;
    if (curStatus !== 'all') {
      list = list.filter(o => o.status === curStatus);
    }

    subTitle.textContent = curStatus === 'all' ? '全部订单' : (list.length + ' 笔订单');

    if (list.length === 0) {
      listEl.innerHTML = '<div style="padding:80px 0;text-align:center;color:#999;font-size:14px">还没有订单</div>';
      return;
    }

    listEl.innerHTML = list.map(o => {
      const phone = (o.receiver || '');
      const date = (o.created_at || '').slice(0, 10);
      return `
        <a href="order-detail.html?order_no=${encodeURIComponent(o.order_no)}" class="order">
          <div class="no">${o.order_no}</div>
          <div class="pic" style="display:flex;align-items:center;justify-content:center;background:#e8e6e2;font-size:11px;color:#999">${(o.items_summary || '').slice(0,4)}</div>
          <div>
            <div class="name">${o.items_summary || '—'}</div>
            <div class="spec">${o.status_text || o.status}</div>
          </div>
          <div class="meta">${date}<br>${o.receiver || ''}</div>
          <div class="price">¥${API.money(o.pay_amount)}</div>
          <div class="go">详情 →</div>
        </a>
      `;
    }).join('');
  }

  // 筛选
  document.querySelectorAll('#tabs a').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      document.querySelectorAll('#tabs a').forEach(x => x.classList.remove('on'));
      el.classList.add('on');
      curStatus = el.dataset.st;
      render();
    });
  });

  // 加载
  (async () => {
    try {
      const data = await API.listOrders({ size: 50 });
      allOrders = data.items || [];
      render();
    } catch (e) {
      listEl.innerHTML = `<div style="padding:80px 0;text-align:center;color:#999;font-size:14px">加载失败：${e.message}</div>`;
    }
  })();
})();
</script>'''

# 替换 page-head + ord-wrap 整块
start = html.find('<div class="page-head">')
# 找到 </body> 前的位置
end = html.find('</body>')

# 保留 footer（如果有）
footer_start = html.find('<footer')

if start > 0 and end > start:
    if footer_start > start and footer_start < end:
        # 有 footer，插在 footer 前
        html = html[:start] + new_orders + "\n\n" + html[footer_start:]
    else:
        html = html[:start] + new_orders + "\n" + html[end:]
    open(p, "w", encoding="utf-8").write(html)
    print("  orders.html 已更新")


# ══════════════════════════════════════════════════════════
# 2. order-detail.html —— 订单详情
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "order-detail.html")
html = open(p, encoding="utf-8").read()

new_detail = '''<div class="od-wrap" id="app">
  <div style="padding:120px 40px;text-align:center;color:#999;font-size:14px">加载订单…</div>
</div>

<script src="api.js"></script>
<script>
(function(){
  const params = new URLSearchParams(location.search);
  const orderNo = params.get('order_no') || localStorage.getItem('twl_last_order');
  const app = document.getElementById('app');

  if (!orderNo) {
    app.innerHTML = '<div style="padding:120px 40px;text-align:center;color:#999">没有找到订单号</div>';
    return;
  }

  const STATUS_ORDER = ['pending_payment', 'paid', 'preparing', 'delivering', 'delivered', 'completed'];
  const STATUS_LABEL = {
    pending_payment: '待支付', paid: '已支付', preparing: '配花中',
    delivering: '配送中', delivered: '已送达', completed: '已完成', cancelled: '已取消'
  };

  function fmt(t) {
    if (!t) return '—';
    return String(t).replace('T', ' ').slice(0, 16);
  }

  function render(o) {
    const curIdx = STATUS_ORDER.indexOf(o.status);

    const steps = STATUS_ORDER.slice(0, 6).map((s, i) => {
      let cls = '';
      if (i < curIdx) cls = 'done';
      else if (i === curIdx) cls = 'now';
      const tl = (o.timeline || []).find(t => t.status === s);
      return `
        <div class="step ${cls}">
          <div class="dot"></div>
          <div class="txt">
            <div class="t">${STATUS_LABEL[s]}</div>
            <div class="d">${tl ? fmt(tl.time) : '—'}</div>
          </div>
        </div>
      `;
    }).join('');

    const items = (o.items || []).map(it => `
      <div class="item">
        <div class="pic"><img src="${it.product_cover || ''}" alt="${it.product_name}"></div>
        <div class="t">
          <h3>${it.product_name}</h3>
          <div class="s">¥${API.money(it.price)} × ${it.qty}</div>
        </div>
      </div>
    `).join('');

    app.innerHTML = `
      <div class="od-left">
        <h1>${o.status_text || STATUS_LABEL[o.status] || o.status}</h1>
        <div class="no">${o.order_no}</div>

        <div class="timeline-title">订单进度</div>
        ${steps}
      </div>

      <div class="od-right">
        <div class="box">
          <h2>商品</h2>
          ${items}
          <div class="drow"><span class="k">收花人</span><span class="v">${o.receiver} ${String(o.phone || '').replace(/(\\d{3})\\d{4}(\\d{4})/, '$1****$2')}</span></div>
          <div class="drow"><span class="k">地址</span><span class="v">${o.address_detail || '—'}</span></div>
          <div class="drow"><span class="k">送达</span><span class="v">${o.delivery_date || '今日'} ${o.delivery_slot || ''}</span></div>
          ${o.card_message ? `<div class="drow"><span class="k">贺卡</span><span class="v">${o.card_message}</span></div>` : ''}
          <div class="drow"><span class="k">实付</span><span class="v price">¥${API.money(o.pay_amount)}</span></div>

          <div class="actions">
            ${o.status === 'pending_payment' ? `<a href="pay.html?order_no=${encodeURIComponent(o.order_no)}" class="primary">去支付</a>` : ''}
            ${['delivered','completed'].includes(o.status) ? `<a href="after-sale.html?order_no=${encodeURIComponent(o.order_no)}" class="ghost">申请售后</a>` : ''}
            <a href="contact.html" class="ghost">联系客服</a>
          </div>
        </div>
      </div>
    `;
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

start = html.find('<div class="od-wrap"')
footer_start = html.find('<footer')
end = html.find('</body>')

if start > 0 and end > start:
    if footer_start > start and footer_start < end:
        html = html[:start] + new_detail + "\n\n" + html[footer_start:]
    else:
        html = html[:start] + new_detail + "\n" + html[end:]
    open(p, "w", encoding="utf-8").write(html)
    print("  order-detail.html 已更新")

print("\n完成")
