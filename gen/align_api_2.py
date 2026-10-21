# -*- coding: utf-8 -*-
"""后台工单/分类接真 API + 订单详情加取消"""

import os

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"


# ══════════════════════════════════════════════════════════
# 1. 后台：工单 + 分类
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "admin.html")
html = open(p, encoding="utf-8").read()

# 在 loadAll 前追加两个加载函数
new_funcs = '''
/* 加载工单 */
async function loadTickets() {
  try {
    const data = await API.listTickets({ size: 100 });
    const list = data.items || [];
    const table = document.querySelector('#page-tickets .box table');
    if (!table) return;

    if (list.length === 0) {
      table.innerHTML = '<tr><td colspan="5" style="padding:40px;text-align:center;color:#999">暂无工单</td></tr>';
    } else {
      const rows = list.map(t => `
        <tr>
          <td><span class="mono">${t.ticket_no}</span></td>
          <td><span class="mono">${t.order_no}</span></td>
          <td>${t.type}</td>
          <td><span class="pill ${t.status === 'submitted' ? 'wait' : t.status === 'resolved' ? 'done' : 'doing'}">${t.status}</span></td>
          <td><span class="act" onclick="replyTicket('${t.ticket_no}')">回复</span></td>
        </tr>
      `).join('');
      table.innerHTML = `
        <tr><th>工单号</th><th>订单号</th><th>类型</th><th>状态</th><th>操作</th></tr>
        ${rows}
      `;
    }

    const ph = document.querySelector('#page-tickets .page-title p');
    if (ph) ph.textContent = `${list.length} 条工单`;

    document.querySelectorAll('.side-nav a[data-page="tickets"] .badge').forEach(el => {
      el.textContent = list.length;
    });
  } catch (e) {
    console.warn('工单加载失败', e);
  }
}

/* 回复工单 */
window.replyTicket = async function(ticketNo) {
  const msg = prompt('回复内容：');
  if (!msg || !msg.trim()) return;
  try {
    await API.request('/tickets/' + encodeURIComponent(ticketNo) + '/reply', {
      method: 'POST',
      body: JSON.stringify({ reply: msg.trim() }),
    });
    API.toast('已回复');
    loadTickets();
  } catch (e) {
    API.toast('回复失败：' + e.message);
  }
};

/* 加载分类 */
async function loadCategories() {
  try {
    const data = await API.getCategories();
    const list = data.items || data || [];
    const table = document.querySelector('#page-categories .box table');
    if (!table) return;

    const NAME = { daily: '日常', love: '告白', birthday: '生日', sympathy: '探望', business: '商务' };
    const rows = list.map(c => `
      <tr>
        <td><span class="mono">${c.key}</span></td>
        <td>${NAME[c.key] || c.key}</td>
        <td>${c.count}</td>
        <td><span class="act">编辑</span></td>
      </tr>
    `).join('');

    table.innerHTML = `
      <tr><th>分类</th><th>中文</th><th>商品数</th><th>操作</th></tr>
      ${rows}
    `;

    const ph = document.querySelector('#page-categories .page-title p');
    if (ph) ph.textContent = `${list.length} 个分类`;
  } catch (e) {
    console.warn('分类加载失败', e);
  }
}

'''

# 插到 loadAll 定义前
marker = "/* 登录后加载数据 */"
if marker in html:
    html = html.replace(marker, new_funcs + marker, 1)

# 更新 loadAll
html = html.replace(
    "async function loadAll() {\n  await Promise.all([loadDashboard(), loadOrders(), loadProducts()]);\n}",
    "async function loadAll() {\n  await Promise.all([loadDashboard(), loadOrders(), loadProducts(), loadTickets(), loadCategories()]);\n}"
)

open(p, "w", encoding="utf-8").write(html)
print("  admin.html: 工单 + 分类接 API")


# ══════════════════════════════════════════════════════════
# 2. 订单详情：加取消按钮
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "order-detail.html")
html = open(p, encoding="utf-8").read()

# 在 actions 里加取消按钮（待支付/已支付可取消）
old_actions = """          <div class="actions">
            ${o.status === 'pending_payment' ? `<a href="pay.html?order_no=${encodeURIComponent(o.order_no)}" class="primary">去支付</a>` : ''}
            ${['delivered','completed'].includes(o.status) ? `<a href="after-sale.html?order_no=${encodeURIComponent(o.order_no)}" class="ghost">申请售后</a>` : ''}
            <a href="contact.html" class="ghost">联系客服</a>
          </div>"""

new_actions = """          <div class="actions">
            ${o.status === 'pending_payment' ? `<a href="pay.html?order_no=${encodeURIComponent(o.order_no)}" class="primary">去支付</a>` : ''}
            ${['pending_payment', 'paid'].includes(o.status) ? `<button class="ghost" id="cancelBtn" style="border:1px solid #e5e5e5;background:#fff;color:#8a3c3c;border-radius:4px;padding:14px;font-size:14px;font-family:inherit;cursor:pointer">取消订单</button>` : ''}
            ${['delivered','completed'].includes(o.status) ? `<a href="after-sale.html?order_no=${encodeURIComponent(o.order_no)}" class="ghost">申请售后</a>` : ''}
            <a href="contact.html" class="ghost">联系客服</a>
          </div>"""

if old_actions in html:
    html = html.replace(old_actions, new_actions, 1)

# 在 render 函数末尾加取消逻辑
old_render_end = """  (async () => {
    try {
      const o = await API.getOrder(orderNo);
      render(o);
    } catch (e) {
      app.innerHTML = `<div style="padding:120px 40px;text-align:center;color:#999">订单加载失败：${e.message}</div>`;
    }
  })();"""

new_render_end = """  async function refresh() {
    try {
      const o = await API.getOrder(orderNo);
      render(o);
      bindCancel(o);
    } catch (e) {
      app.innerHTML = `<div style="padding:120px 40px;text-align:center;color:#999">订单加载失败：${e.message}</div>`;
    }
  }

  function bindCancel(o) {
    const btn = document.getElementById('cancelBtn');
    if (!btn) return;
    btn.addEventListener('click', async () => {
      if (!confirm('确定要取消这笔订单吗？')) return;
      btn.disabled = true;
      btn.textContent = '取消中…';
      try {
        await API.cancelOrder(o.order_no, '用户主动取消');
        API.toast('订单已取消');
        setTimeout(refresh, 500);
      } catch (e) {
        API.toast('取消失败：' + e.message);
        btn.disabled = false;
        btn.textContent = '取消订单';
      }
    });
  }

  refresh();"""

if old_render_end in html:
    html = html.replace(old_render_end, new_render_end, 1)

open(p, "w", encoding="utf-8").write(html)
print("  order-detail.html: 加取消订单")

print("\n完成")
