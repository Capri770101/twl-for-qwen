# -*- coding: utf-8 -*-
"""admin.html 接真实 API"""

import os

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"
p = os.path.join(PROTO, "admin.html")
html = open(p, encoding="utf-8").read()

# 1. 在 </head> 前加 api.js
if 'src="api.js"' not in html:
    html = html.replace("</head>", '<script src="api.js"></script>\n</head>')

# 2. 在最后的启动检查前插入 API 加载逻辑
API_JS = '''
/* ═══════════════════════════════════════════════════════════
   接真实 API
   ═══════════════════════════════════════════════════════════ */

/* 状态 → 药丸样式 */
function pillClass(status) {
  if (status === 'pending_payment') return 'wait';
  if (status === 'paid' || status === 'preparing' || status === 'delivering') return 'doing';
  if (status === 'delivered' || status === 'completed') return 'done';
  return 'cancel';
}

/* 加载数据看板 */
async function loadDashboard() {
  try {
    const s = await API.stats();

    // 数据卡片
    const stats = document.querySelectorAll('#page-dashboard .stat .num');
    if (stats.length >= 5) {
      stats[0].innerHTML = s.orders_today;
      stats[1].innerHTML = API.money(s.revenue) + '<small>元</small>';
      stats[2].innerHTML = s.by_status.find(x => x.status === 'paid')?.count
        ?? s.by_status.find(x => x.status === 'preparing')?.count ?? 0;
      stats[3].innerHTML = s.tickets_open;
      stats[4].innerHTML = s.products_on;
    }

    // 副标题
    const sub = document.querySelector('#page-dashboard .page-title p');
    if (sub) {
      const now = new Date();
      sub.textContent = `${now.getFullYear()} 年 ${now.getMonth()+1} 月 ${now.getDate()} 日 · 实时数据`;
    }
  } catch (e) {
    console.warn('看板加载失败', e);
    API.toast('看板数据加载失败：' + e.message);
  }
}

/* 加载全部订单 */
async function loadOrders() {
  try {
    const data = await API.adminOrders({ size: 100 });
    const list = data.items || [];

    // 渲染函数
    const rowHtml = (o, compact) => `
      <tr>
        <td><span class="mono">${o.order_no}</span></td>
        <td><div class="name">${(o.items || []).map(i => i.name).join('、') || '—'}</div>
            <div class="sub">${(o.items || []).map(i => i.name + '×' + i.qty).join(' / ')}</div></td>
        ${compact ? '' : `<td>${o.receiver}<br><span class="sub">${o.phone || ''}</span></td>`}
        <td><span class="price">¥${API.money(o.pay_amount)}</span></td>
        <td><span class="pill ${pillClass(o.status)}">${o.status_text || o.status}</span></td>
        <td><span class="act">详情</span></td>
      </tr>
    `;

    // 看板最新 3 条
    const dashTable = document.querySelector('#page-dashboard .box table');
    if (dashTable) {
      const rows = list.slice(0, 3).map(o => rowHtml(o, false)).join('');
      dashTable.innerHTML = `
        <tr><th>订单号</th><th>商品</th><th>收花人</th><th>金额</th><th>状态</th><th>操作</th></tr>
        ${rows}
      `;
    }

    // 全部订单页
    const ordersTable = document.querySelector('#page-orders .box table');
    if (ordersTable) {
      const rows = list.map(o => rowHtml(o, false)).join('');
      ordersTable.innerHTML = `
        <tr><th>订单号</th><th>商品</th><th>收花人</th><th>金额</th><th>状态</th><th>操作</th></tr>
        ${rows}
      `;
    }

    // 待处理（paid / preparing / delivering）
    const pendingTable = document.querySelector('#page-pending .box table');
    if (pendingTable) {
      const pending = list.filter(o => ['paid', 'preparing', 'delivering'].includes(o.status));
      const rows = pending.map(o => rowHtml(o, false)).join('');
      pendingTable.innerHTML = pending.length
        ? `<tr><th>订单号</th><th>商品</th><th>收花人</th><th>金额</th><th>状态</th><th>操作</th></tr>${rows}`
        : '<tr><td colspan="6" style="padding:40px;text-align:center;color:#999">没有待处理的订单</td></tr>';
    }

    // 订单数徽标
    document.querySelectorAll('.side-nav a[data-page="orders"] .badge').forEach(el => {
      el.textContent = list.length;
    });
    const pendingCount = list.filter(o => ['paid', 'preparing', 'delivering'].includes(o.status)).length;
    document.querySelectorAll('.side-nav a[data-page="pending"] .badge').forEach(el => {
      el.textContent = pendingCount;
    });

    // 页头副标题
    const oh = document.querySelector('#page-orders .page-title p');
    if (oh) oh.textContent = `共 ${list.length} 笔 · 按时间倒序`;

    return list;
  } catch (e) {
    console.warn('订单加载失败', e);
    API.toast('订单加载失败：' + e.message);
    return [];
  }
}

/* 加载花束列表 */
async function loadProducts() {
  try {
    const data = await API.adminProducts();
    const list = data.items || data || [];
    const table = document.querySelector('#page-products .box table');
    if (!table) return;

    const rows = list.map(p => `
      <tr>
        <td><span class="mono">${p.id}</span></td>
        <td>${p.name}</td>
        <td>¥${API.money(p.price)}</td>
        <td>${p.category || '—'}</td>
        <td><span class="pill ${p.is_active === false ? 'cancel' : 'done'}">${p.is_active === false ? '下架' : '在售'}</span></td>
        <td><span class="act">编辑</span></td>
      </tr>
    `).join('');

    table.innerHTML = `
      <tr><th>ID</th><th>名称</th><th>价格</th><th>分类</th><th>状态</th><th>操作</th></tr>
      ${rows}
    `;

    const ph = document.querySelector('#page-products .page-title p');
    if (ph) ph.textContent = `共 ${list.length} 件 · ${list.filter(p => p.is_active !== false).length} 件在售`;
  } catch (e) {
    console.warn('商品加载失败', e);
  }
}

/* 登录后加载数据 */
async function loadAll() {
  await Promise.all([loadDashboard(), loadOrders(), loadProducts()]);
}

/* 覆盖原来的 showApp，登录成功后拉数据 */
const _origShowApp = showApp;
showApp = function() {
  document.getElementById('gate').classList.add('hide');
  document.getElementById('app').classList.add('on');
  loadAll();
};

/* 登录状态下刷新页面 */
if (sessionStorage.getItem(KEY) === '1') {
  showApp();
}

'''

# 插到 "启动时检查登录状态" 之前
marker = "/* ═══ 启动时检查登录状态 ═══ */"
if marker in html:
    html = html.replace(marker, API_JS + marker, 1)
else:
    html = html.replace("</script>\n\n</body>", API_JS + "\n</script>\n\n</body>", 1)

open(p, "w", encoding="utf-8").write(html)
print("admin.html 已更新")
print("  有 api.js:", 'src="api.js"' in html)
print("  有 loadDashboard:", "loadDashboard" in html)
