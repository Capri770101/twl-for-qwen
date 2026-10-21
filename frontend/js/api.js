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

    /* ── 后台：推进订单状态 ── */
    async updateOrderStatus(orderNo, toStatus, reason) {
      const qs = new URLSearchParams();
      qs.set('to_status', toStatus);
      if (reason) qs.set('reason', reason);
      return request(
        '/orders/' + encodeURIComponent(orderNo) + '/status?' + qs.toString(),
        { method: 'POST' }
      );
    },

    async adminOrders(params = {}) {
      const qs = new URLSearchParams(params).toString();
      return request('/admin/orders' + (qs ? '?' + qs : ''));
    },

    /* ── 后台：商品 CRUD ── */
    async createProduct(payload) {
      return request('/products/admin', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },

    async updateProduct(id, payload) {
      return request('/products/admin/' + encodeURIComponent(id), {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
    },

    async deleteProduct(id) {
      return request('/products/admin/' + encodeURIComponent(id), {
        method: 'DELETE',
      });
    },

    async adminProducts() {
      return request('/admin/products');
    },

    /* ── 后台：配送 ── */
    async listDeliveries(params = {}) {
      const qs = new URLSearchParams();
      if (params.status) qs.set('status', params.status);
      if (params.page) qs.set('page', params.page);
      if (params.size) qs.set('size', params.size);
      const q = qs.toString();
      return request('/deliveries' + (q ? '?' + q : ''));
    },

    async retryDelivery(orderNo) {
      return request('/deliveries/' + encodeURIComponent(orderNo) + '/retry', {
        method: 'POST',
      });
    },

    async getDelivery(orderNo) {
      return request('/deliveries/' + encodeURIComponent(orderNo));
    },

    /* ── 退款 ── */
    async createRefund(payload) {
      return request('/refunds', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },

    async listRefunds(params = {}) {
      const qs = new URLSearchParams();
      if (params.status) qs.set('status', params.status);
      if (params.page) qs.set('page', params.page);
      if (params.size) qs.set('size', params.size);
      const q = qs.toString();
      return request('/refunds' + (q ? '?' + q : ''));
    },

    async reviewRefund(refundNo, payload) {
      return request('/refunds/' + encodeURIComponent(refundNo) + '/review', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },

    async retryRefund(refundNo) {
      return request('/refunds/' + encodeURIComponent(refundNo) + '/retry', {
        method: 'POST',
      });
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


/* ═══════════════════════════════════════════════════════════
   系统配置 + 演示模式标识

   【干什么】
   页面加载时读一次 /api/v1/system/config，
   存到 window.APP_CONFIG，然后：
     1. 演示模式 → 顶部插一条提示
     2. 有公告 → 更新顶部公告栏
     3. 配送未配置 → 把写死的配送文案改掉

   【为什么要自动做】
   21 个页面不用各写一遍，引了 api.js 就自动生效。
   ═══════════════════════════════════════════════════════════ */

(function () {
  // ── 注入演示模式提示条 ──
  function injectDemoBanner() {
    if (document.getElementById("__demo-banner")) return;
    if (sessionStorage.getItem("twl_demo_dismissed") === "1") return;

    const bar = document.createElement("div");
    bar.id = "__demo-banner";
    bar.style.cssText = [
      "position:fixed",
      "left:0",
      "right:0",
      "top:0",
      "z-index:9998",
      "background:#fdf8ee",
      "border-bottom:1px solid #ddc9a0",
      "color:#8a6420",
      "font-size:12px",
      "line-height:1.6",
      "padding:8px 40px",
      "text-align:center",
      "font-family:-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif",
    ].join(";");

    bar.innerHTML =
      '演示环境 · 商品与配送信息为示例数据，下单不会真实扣款' +
      '<span id="__demo-close" style="margin-left:16px;cursor:pointer;text-decoration:underline;text-underline-offset:3px">知道了</span>';

    document.body.appendChild(bar);

    // 给 body 留出空间，避免遮挡
    document.body.style.paddingTop = "34px";

    document.getElementById("__demo-close").addEventListener("click", () => {
      bar.remove();
      document.body.style.paddingTop = "0";
      sessionStorage.setItem("twl_demo_dismissed", "1");
    });
  }

  // ── 更新公告栏 ──
  function updateAnnounce(text) {
    document.querySelectorAll(".announce").forEach(el => {
      el.innerHTML = text;
    });
  }

  // ── 配送文案降级 ──
  function neutralizeDelivery() {
    // 把页面里写死的「2 小时达」「满 199 免运费」这类替换掉
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null
    );

    const replacements = [
      [/深圳同城\s*2\s*小时达/g, "配送时效以实际为准"],
      [/满\s*¥?\s*199\s*免运费/g, "运费以结算页为准"],
      [/2\s*小时达/g, "当日达"],
      [/满\s*199\s*免运费/g, "运费以结算页为准"],
      [/16:00\s*前下单当日送达/g, "具体时效以客服确认为准"],
    ];

    const nodes = [];
    while (walker.nextNode()) {
      const n = walker.currentNode;
      if (n.parentElement && /^(SCRIPT|STYLE)$/.test(n.parentElement.tagName)) continue;
      nodes.push(n);
    }

    nodes.forEach(n => {
      let t = n.nodeValue;
      let changed = false;
      replacements.forEach(([re, to]) => {
        const nt = t.replace(re, to);
        if (nt !== t) {
          t = nt;
          changed = true;
        }
      });
      if (changed) n.nodeValue = t;
    });
  }

  // ── 主流程 ──
  async function init() {
    try {
      const r = await fetch("/api/v1/system/config");
      const j = await r.json();

      if (j.code !== 0 || !j.data) return;

      window.APP_CONFIG = j.data;

      const cfg = j.data;

      // 公告
      if (cfg.delivery && cfg.delivery.announcement) {
        updateAnnounce(cfg.delivery.announcement);
      } else if (cfg.demo_mode) {
        updateAnnounce("配送信息待配置");
      }

      // 演示模式
      if (cfg.demo_mode) {
        injectDemoBanner();
        neutralizeDelivery();
      }

      // 派发事件，页面可以监听
      window.dispatchEvent(new CustomEvent("twl:config", { detail: cfg }));

    } catch (e) {
      // 拿不到配置不影响页面使用
      console.warn("系统配置加载失败", e);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
