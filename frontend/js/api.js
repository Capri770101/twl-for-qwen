/* ═══════════════════════════════════════════════════════════
   跳舞兰 · 前端 API 层（api.js）
   所有页面共用，挂到 window.API
   ═══════════════════════════════════════════════════════════ */

const API = (() => {
  const BASE = '/api/v1';

  /* 统一请求：把 {code,message,data} 拆开 */
  async function request(path, options = {}) {
    const url = BASE + path;

    const config = {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    };

    let res;
    try {
      res = await fetch(url, config);
    } catch (e) {
      throw new Error('网络不通，检查后端是否启动');
    }

    let json;
    try {
      json = await res.json();
    } catch (e) {
      throw new Error(`返回不是 JSON（HTTP ${res.status}）`);
    }

    // 后端统一格式：{code:0, message:"ok", data:{...}}
    if (json.code !== 0) {
      throw new Error(json.message || '接口返回错误');
    }

    return json.data;
  }

  return {
    /* ── 通用请求（公开） ── */
    request,

    /* ── 商品 ── */
    async listProducts(params = {}) {
      const qs = new URLSearchParams();
      if (params.category) qs.set('category', params.category);
      if (params.keyword) qs.set('keyword', params.keyword);
      if (params.page) qs.set('page', params.page);
      if (params.size) qs.set('size', params.size);
      const q = qs.toString();
      return request('/products' + (q ? '?' + q : ''));
    },

    async getProduct(id) {
      return request('/products/' + encodeURIComponent(id));
    },

    async getCategories() {
      return request('/products/meta/categories');
    },

    async checkAvailability(id, date) {
      const q = date ? '?delivery_date=' + date : '';
      return request('/products/' + encodeURIComponent(id) + '/availability' + q);
    },

    /* ── 订单 ── */
    async createOrder(payload) {
      return request('/orders', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },

    async getOrder(orderNo) {
      return request('/orders/' + encodeURIComponent(orderNo));
    },

    async listOrders(params = {}) {
      const qs = new URLSearchParams();
      if (params.phone) qs.set('phone', params.phone);
      if (params.guest_token) qs.set('guest_token', params.guest_token);
      if (params.page) qs.set('page', params.page);
      if (params.size) qs.set('size', params.size);
      const q = qs.toString();
      return request('/orders' + (q ? '?' + q : ''));
    },

    async cancelOrder(orderNo, reason) {
      return request('/orders/' + encodeURIComponent(orderNo) + '/cancel', {
        method: 'POST',
        body: JSON.stringify({ reason: reason || '用户取消' }),
      });
    },

    /* ── 支付 ── */
    async createPayment(orderNo, channel) {
      return request('/payments/create', {
        method: 'POST',
        body: JSON.stringify({ order_no: orderNo, channel: channel || 'mock' }),
      });
    },

    async getPayments(orderNo) {
      return request('/payments/records/' + encodeURIComponent(orderNo));
    },

    /* ── 售后 ── */
    async createTicket(payload) {
      return request('/tickets', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },

    async listTickets(params = {}) {
      const qs = new URLSearchParams(params).toString();
      return request('/tickets' + (qs ? '?' + qs : ''));
    },

    /* ── 配送 ── */
    async getDelivery(orderNo) {
      return request('/deliveries/' + encodeURIComponent(orderNo));
    },

    /* ── 后台 ── */
    async stats() {
      return request('/admin/stats');
    },

    async adminOrders(params = {}) {
      const qs = new URLSearchParams(params).toString();
      return request('/admin/orders' + (qs ? '?' + qs : ''));
    },

    async adminProducts() {
      return request('/admin/products');
    },

    /* ── 工具 ── */
    money(v) {
      const n = typeof v === 'string' ? parseFloat(v) : v;
      return isNaN(n) ? '0' : n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    },

    toast(msg, ms) {
      let el = document.getElementById('__toast');
      if (!el) {
        el = document.createElement('div');
        el.id = '__toast';
        el.style.cssText = 'position:fixed;left:50%;bottom:80px;transform:translateX(-50%);background:rgba(26,26,26,.92);color:#fff;padding:12px 24px;font-size:14px;border-radius:4px;z-index:99999;opacity:0;transition:opacity .25s;white-space:nowrap;max-width:80vw;overflow:hidden;text-overflow:ellipsis;';
        document.body.appendChild(el);
      }
      el.textContent = msg;
      el.style.opacity = '1';
      clearTimeout(el.__t);
      el.__t = setTimeout(() => { el.style.opacity = '0'; }, ms || 2200);
    },
  };
})();

window.API = API;

/* ═══════════════════════════════════════════════════════════
   购物袋（全站共用，存 localStorage）
   ═══════════════════════════════════════════════════════════ */
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
    API.toast('已加入购物袋');
  },
  updateQty(id, qty) {
    const items = this.getCart();
    const it = items.find(i => i.id === id);
    if (!it) return;
    it.qty = Math.max(1, Math.min(99, qty));
    this.setCart(items);
  },
  remove(id) {
    this.setCart(this.getCart().filter(i => i.id !== id));
  },
  clear() {
    this.setCart([]);
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
  }
};
