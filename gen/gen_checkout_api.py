# -*- coding: utf-8 -*-
"""重写下单三页，接真实 API"""

import os

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

HEAD = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root{{--white:#fff;--paper:#f1efeb;--ink:#1a1a1a;--gray-7:#666;--gray-a:#999;--line:#e5e5e5;--line-light:#ebe9e5}}
  *{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
  body{{background:var(--white);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue","PingFang SC",sans-serif;font-weight:400;line-height:1.6;-webkit-font-smoothing:antialiased}}
  a{{color:inherit;text-decoration:none}}
  img{{display:block;width:100%}}
  button{{font-family:inherit;cursor:pointer}}

  .hd-top{{padding:13px 40px 0;display:flex;justify-content:flex-end;gap:24px;font-size:12px;color:#666}}
  .hd-top a:hover{{color:#1a1a1a}}
  .hd-brand{{padding:20px 24px 26px;text-align:center}}
  .hd-brand h1{{font-family:'Noto Serif SC',serif;font-size:22px;font-weight:400;letter-spacing:.5em;text-indent:.5em;line-height:1;color:#1a1a1a}}
  .hd-brand .en{{display:block;margin-top:9px;font-size:10px;letter-spacing:.42em;text-transform:uppercase;color:#999}}
  .hd-nav{{border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:0 10px}}
  .hd-nav ul{{display:flex;justify-content:center;list-style:none}}
  .hd-nav a{{display:block;padding:15px 18px;font-size:13px;color:#666;white-space:nowrap}}
  .hd-nav a:hover{{color:#1a1a1a}}

  .wrap{{display:grid;grid-template-columns:1.35fr 1fr;gap:80px;max-width:1320px;margin:0 auto;padding:64px 40px 100px;align-items:start}}
  .left h1{{font-size:48px;font-weight:400;letter-spacing:-.015em;margin-bottom:10px}}
  .left .step{{font-size:12px;color:#999;letter-spacing:.1em;margin-bottom:40px}}
  .right{{position:sticky;top:40px}}

  .guest{{border:1px solid var(--line);background:var(--paper);padding:22px 24px;margin-bottom:44px}}
  .guest .t{{font-size:14px;margin-bottom:12px;display:flex;align-items:center;gap:8px}}
  .guest .t .dot{{width:18px;height:18px;border:1px solid #1a1a1a;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;flex:0 0 18px}}
  .guest ul{{margin:0 0 14px 26px;font-size:13px;line-height:2;color:#555}}
  .guest .why{{font-size:12px;color:#888;padding-top:12px;border-top:1px solid var(--line);margin-bottom:14px}}
  .guest .act{{display:flex;gap:10px}}
  .guest .act a{{padding:9px 20px;font-size:12px;border-radius:4px}}
  .guest .act .go{{background:#1a1a1a;color:#fff}}
  .guest .act .skip{{border:1px solid var(--line);background:#fff;color:#666}}

  .form-sec{{margin-bottom:40px}}
  .form-sec .lbl{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#999;margin-bottom:6px}}
  .row{{display:flex;align-items:center;gap:16px;padding:16px 0;border-bottom:1px solid var(--line-light)}}
  .row .k{{flex:0 0 80px;font-size:14px;color:#666}}
  .row .v{{flex:1}}
  .row input{{width:100%;border:0;background:none;font-size:15px;color:#1a1a1a;outline:none;font-family:inherit}}
  .row input::placeholder{{color:#bbb}}

  .summary{{border:1px solid var(--line);padding:28px;background:#fff}}
  .summary h2{{font-size:14px;font-weight:400;letter-spacing:.06em;padding-bottom:16px;border-bottom:1px solid var(--line);margin-bottom:20px}}
  .sum-item{{display:flex;gap:16px;padding-bottom:16px;border-bottom:1px solid var(--line-light);margin-bottom:16px}}
  .sum-item .pic{{width:56px;height:70px;flex:0 0 56px;background:#e8e6e2;overflow:hidden}}
  .sum-item .pic img{{width:100%;height:100%;object-fit:cover}}
  .sum-item .txt{{flex:1;min-width:0}}
  .sum-item .txt h3{{font-size:14px;font-weight:400;margin-bottom:2px}}
  .sum-item .txt .spec{{font-size:12px;color:#999;line-height:1.6}}
  .sum-item .q{{font-size:12px;color:#999}}
  .sum-item .p{{font-size:14px;white-space:nowrap}}
  .fee{{display:flex;justify-content:space-between;padding:7px 0;font-size:14px}}
  .fee .k{{color:#666}}
  .fee.total{{border-top:1px solid var(--line);margin-top:16px;padding-top:18px;font-size:16px}}
  .fee.total .k{{color:#1a1a1a}}
  .fee.total .v{{font-size:22px}}
  .pay-btn{{display:block;width:100%;margin-top:26px;padding:17px;background:#1a1a1a;color:#fff;border:0;border-radius:4px;font-size:15px;letter-spacing:.02em;text-align:center;transition:opacity .18s}}
  .pay-btn:hover{{opacity:.85}}
  .pay-btn:disabled{{background:#ccc;cursor:not-allowed}}
  .agree{{margin-top:18px;font-size:11px;color:#999;line-height:1.9;text-align:center}}

  .site-footer{{background:#f1efeb;border-top:1px solid var(--line);padding:56px 0 0}}
  .ft-row{{display:flex;padding:0 40px 44px;max-width:1560px;margin:0 auto;overflow-x:auto}}
  .ft-brand{{flex:0 0 auto;padding-right:48px;margin-right:48px;border-right:1px solid #ddd9d2;min-width:200px}}
  .ft-brand h4{{font-family:'Noto Serif SC',serif;font-size:15px;font-weight:400;letter-spacing:.4em;text-indent:.4em;line-height:1;margin-bottom:10px}}
  .ft-brand .en{{font-size:9px;letter-spacing:.34em;text-transform:uppercase;color:#999}}
  .ft-brand .slogan{{margin-top:20px;font-size:11px;line-height:2;color:#888}}
  .ft-col{{flex:0 0 auto;padding-right:48px;min-width:110px}}
  .ft-col:last-child{{padding-right:0}}
  .ft-col h5{{font-size:10px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:#999;margin-bottom:14px}}
  .ft-col a{{display:block;font-size:12px;line-height:2.4;color:#555;white-space:nowrap}}
  .ft-bottom{{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:22px 40px;border-top:1px solid #ddd9d2;max-width:1560px;margin:0 auto;flex-wrap:wrap}}
  .ft-bottom .cr{{font-size:10px;color:#999}}
  .social{{display:flex;gap:9px}}
  .social a{{width:28px;height:28px;border:1px solid #ddd9d2;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;color:#777}}

  @media (max-width:1024px){{.wrap{{grid-template-columns:1fr 380px;gap:48px;padding:48px 24px 80px}}.left h1{{font-size:38px}}}}
  @media (max-width:860px){{
    .wrap{{grid-template-columns:1fr;gap:0;padding:0 0 60px}}
    .left{{padding:40px 20px 0}}
    .left h1{{font-size:32px}}
    .right{{position:static;padding:0 20px}}
    .summary{{border-left:0;border-right:0;padding:24px 0;border-bottom:0}}
    .hd-top{{padding:10px 16px 0;font-size:10px}}
    .hd-brand{{padding:14px 16px 18px}}
    .hd-brand h1{{font-size:18px;letter-spacing:.4em;text-indent:.4em}}
    .hd-nav{{overflow-x:auto;scrollbar-width:none}}
    .hd-nav ul{{justify-content:flex-start}}
    .hd-nav a{{padding:12px 14px;font-size:11.5px}}
    .row .k{{flex:0 0 56px;font-size:13px}}
    .ft-row{{flex-wrap:wrap;padding:0 20px 32px;gap:28px}}
    .ft-brand{{border-right:0;padding-right:0;margin-right:0;width:100%}}
    .ft-brand .slogan{{display:none}}
    .ft-col{{padding-right:0;min-width:calc(50% - 14px)}}
    .ft-bottom{{padding:18px 20px;flex-direction:column;align-items:flex-start;gap:12px}}
  }}
  {extra_css}
</style>
</head>
<body>

<header>
  <div class="hd-top"><a href="#">Contact</a><a href="login.html">Login</a></div>
  <div class="hd-brand">
    <a href="index.html"><h1>跳舞兰</h1><span class="en">Tiao Wu Lan</span></a>
  </div>
  <nav class="hd-nav">
    <ul>
      <li><a href="shop.html">全部花束</a></li>
      <li><a href="#">日常</a></li>
      <li><a href="#">告白</a></li>
      <li><a href="#">生日</a></li>
      <li><a href="flower-language.html">花语</a></li>
      <li><a href="about.html">关于</a></li>
    </ul>
  </nav>
</header>
'''

FOOT = '''
<footer class="site-footer">
  <div class="ft-row">
    <div class="ft-brand">
      <h4>跳舞兰</h4>
      <div class="en">Tiao Wu Lan</div>
      <div class="slogan">Living With<br>Flowers Every Day</div>
    </div>
    <div class="ft-col">
      <h5>Shop</h5>
      <a href="shop.html">全部花束</a>
      <a href="#">日常</a>
      <a href="#">告白</a>
      <a href="#">生日</a>
    </div>
    <div class="ft-col">
      <h5>Help</h5>
      <a href="help-delivery.html">配送范围</a>
      <a href="help-returns.html">售后政策</a>
      <a href="help-faq.html">常见问题</a>
    </div>
    <div class="ft-col">
      <h5>About</h5>
      <a href="about.html">品牌故事</a>
      <a href="flower-language.html">花语百科</a>
      <a href="#">企业合作</a>
    </div>
    <div class="ft-col">
      <h5>Contact</h5>
      <a href="mailto:hello@tiaowulan.com">hello@tiaowulan.com</a>
      <a href="contact.html">400-000-0000</a>
      <a href="#">9:00 – 21:00</a>
    </div>
  </div>
  <div class="ft-bottom">
    <div class="cr">© 深圳市跳舞兰科技有限公司 &nbsp;·&nbsp; 粤ICP备 00000000 号</div>
    <div class="social"><a href="#">ig</a><a href="#">wx</a><a href="#">xhs</a><a href="#">dy</a></div>
  </div>
</footer>

<script src="api.js"></script>
</body>
</html>
'''


# ══════════════════════════════════════════════════════════
# 确认订单
# ══════════════════════════════════════════════════════════
checkout_body = '''
<div class="wrap">

  <div class="left">
    <h1>确认订单</h1>
    <div class="step">STEP 1 / 2</div>

    <div class="guest" id="guestTip">
      <div class="t"><span class="dot">!</span>你正在以「游客」身份下单</div>
      <ul>
        <li>只能在当前浏览器查看订单，换设备或清缓存后看不到</li>
        <li>无法在线申请售后（需要账号）</li>
        <li>无法保存地址，下次要重填</li>
      </ul>
      <div class="why">登录只要 10 秒，订单会自动归档到你的账户。</div>
      <div class="act">
        <a href="login.html" class="go">先登录</a>
        <a href="#" class="skip" id="skipTip">继续以游客下单</a>
      </div>
    </div>

    <div class="form-sec">
      <div class="lbl">收花人</div>
      <div class="row"><span class="k">姓名</span><span class="v"><input id="rName" placeholder="收花人姓名"></span></div>
      <div class="row"><span class="k">电话</span><span class="v"><input id="rPhone" placeholder="手机号" inputmode="tel" maxlength="11"></span></div>
      <div class="row"><span class="k">地址</span><span class="v"><input id="rAddr" placeholder="省市区 + 详细地址"></span></div>
    </div>

    <div class="form-sec">
      <div class="lbl">配送</div>
      <div class="row">
        <span class="k">日期</span>
        <span class="v"><input id="dDate" type="date"></span>
      </div>
      <div class="row">
        <span class="k">时段</span>
        <span class="v"><input id="dSlot" placeholder="如 18:00-20:00"></span>
      </div>
    </div>

    <div class="form-sec">
      <div class="lbl">贺卡（选填）</div>
      <div class="row"><span class="k">留言</span><span class="v"><input id="cardMsg" placeholder="想对她说的话" maxlength="200"></span></div>
    </div>
  </div>

  <div class="right">
    <div class="summary">
      <h2>订单摘要</h2>
      <div id="sumItems"></div>
      <div class="fee"><span class="k">商品小计</span><span class="v" id="subtotal">¥0</span></div>
      <div class="fee"><span class="k">配送费</span><span class="v" id="shipping">免运费</span></div>
      <div class="fee total"><span class="k">应付</span><span class="v" id="total">¥0</span></div>
      <button class="pay-btn" id="submitBtn">去支付</button>
      <div class="agree">下单即表示同意《用户协议》与《退换政策》</div>
    </div>
  </div>

</div>

<script>
(function(){
  const cart = TWL.getCart();

  // 购物袋空了就回去
  if (cart.length === 0) {
    alert('购物袋是空的');
    location.href = 'shop.html';
    return;
  }

  // 渲染摘要
  document.getElementById('sumItems').innerHTML = cart.map(it => `
    <div class="sum-item">
      <div class="pic"><img src="${it.img || ''}" alt="${it.name}"></div>
      <div class="txt">
        <h3>${it.name}</h3>
        <div class="spec">${it.spec || ''}</div>
        <div class="q">×${it.qty}</div>
      </div>
      <div class="p">¥${API.money(it.price * it.qty)}</div>
    </div>
  `).join('');

  const sub = TWL.subtotal();
  const ship = sub >= 199 ? 0 : 15;
  document.getElementById('subtotal').textContent = '¥' + API.money(sub);
  document.getElementById('shipping').textContent = ship === 0 ? '免运费' : '¥' + ship;
  document.getElementById('total').textContent = '¥' + API.money(sub + ship);

  // 默认明天
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  document.getElementById('dDate').value = tomorrow.toISOString().slice(0, 10);
  document.getElementById('dSlot').value = '18:00-20:00';

  // 关闭游客提示
  document.getElementById('skipTip').addEventListener('click', e => {
    e.preventDefault();
    document.getElementById('guestTip').style.display = 'none';
  });

  // 提交
  const btn = document.getElementById('submitBtn');
  btn.addEventListener('click', async () => {
    const name = document.getElementById('rName').value.trim();
    const phone = document.getElementById('rPhone').value.trim();
    const addr = document.getElementById('rAddr').value.trim();
    const date = document.getElementById('dDate').value;
    const slot = document.getElementById('dSlot').value.trim();
    const msg = document.getElementById('cardMsg').value.trim();

    if (!name) { API.toast('请填写收花人姓名'); return; }
    if (!/^1\\d{10}$/.test(phone)) { API.toast('请填写正确的手机号'); return; }
    if (!addr) { API.toast('请填写收花地址'); return; }

    btn.disabled = true;
    btn.textContent = '提交中…';

    try {
      const result = await API.createOrder({
        items: cart.map(it => ({ product_id: it.id, qty: it.qty })),
        receiver: {
          name: name,
          phone: phone,
          detail: addr,
        },
        delivery_date: date || null,
        delivery_slot: slot || null,
        card_message: msg || null,
        anonymous: false,
      });

      // 存订单号
      localStorage.setItem('twl_last_order', result.order_no);
      localStorage.setItem('twl_guest_token', result.guest_token || '');

      // 订单已创建，清空购物袋
      TWL.clear();

      location.href = 'pay.html?order_no=' + encodeURIComponent(result.order_no);
    } catch (e) {
      API.toast(e.message);
      btn.disabled = false;
      btn.textContent = '去支付';
    }
  });
})();
</script>
'''

# ══════════════════════════════════════════════════════════
# 支付
# ══════════════════════════════════════════════════════════
pay_extra_css = '''
  .methods-title{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#999;margin-bottom:4px}
  .method{display:flex;align-items:center;gap:18px;padding:22px 0;border-bottom:1px solid var(--line-light);cursor:pointer;transition:all .15s}
  .method:hover{padding-left:6px}
  .method .ico{width:40px;height:40px;flex:0 0 40px;border:1px solid var(--line);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;color:#999}
  .method.on .ico{border-color:#1a1a1a;color:#1a1a1a}
  .method .txt{flex:1}
  .method .txt .t{font-size:16px;margin-bottom:3px}
  .method .txt .d{font-size:12px;color:#999}
  .method .radio{width:18px;height:18px;flex:0 0 18px;border:1px solid var(--line);border-radius:50%;position:relative}
  .method.on .radio{border-color:#1a1a1a}
  .method.on .radio::after{content:"";position:absolute;inset:4px;border-radius:50%;background:#1a1a1a}
  .secure{margin-top:36px;padding:18px 20px;background:var(--paper);font-size:12px;color:#888;line-height:1.9}
  .amount-box{border:1px solid var(--line);padding:32px 28px}
  .amount-box .lbl{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#999;margin-bottom:10px}
  .amount-box .amt{font-size:56px;font-weight:400;letter-spacing:-.02em;line-height:1;margin-bottom:6px}
  .amount-box .amt .cur{font-size:26px;margin-right:2px}
  .amount-box .no{font-size:12px;color:#999;font-family:monospace;margin-bottom:24px}
  .timer{display:flex;align-items:center;gap:8px;padding:12px 16px;background:var(--paper);font-size:13px;color:#666;margin-bottom:24px}
  .timer .t{font-family:monospace;font-size:15px;color:#1a1a1a}
  .divider{height:1px;background:var(--line);margin:0 0 24px}
  .confirm-btn{display:block;width:100%;margin-top:28px;padding:18px;background:#1a1a1a;color:#fff;border:0;border-radius:4px;font-size:16px;letter-spacing:.02em;text-align:center;transition:opacity .18s}
  .confirm-btn:hover{opacity:.85}
  .confirm-btn:disabled{background:#ccc;cursor:not-allowed}
  .back{display:block;text-align:center;margin-top:18px;font-size:13px;color:#999}
'''

pay_body = '''
<div class="wrap">

  <div class="left">
    <h1>支付</h1>
    <div class="step">STEP 2 / 2</div>

    <div class="methods-title">支付方式</div>

    <div class="method" data-ch="wechat">
      <div class="ico">微</div>
      <div class="txt"><div class="t">微信支付</div><div class="d">推荐 · 微信内自动唤起</div></div>
      <div class="radio"></div>
    </div>

    <div class="method" data-ch="alipay">
      <div class="ico">支</div>
      <div class="txt"><div class="t">支付宝</div><div class="d">跳转支付宝 App 完成支付</div></div>
      <div class="radio"></div>
    </div>

    <div class="method on" data-ch="mock">
      <div class="ico">测</div>
      <div class="txt"><div class="t">模拟支付（开发环境）</div><div class="d">后端 mock 网关，立即到账</div></div>
      <div class="radio"></div>
    </div>

    <div class="secure">
      支付由第三方支付机构处理，我们不存储你的银行卡信息。<br>
      支付成功后，订单会立即进入配花流程。
    </div>
  </div>

  <div class="right">
    <div class="amount-box">
      <div class="lbl">应付金额</div>
      <div class="amt"><span class="cur">¥</span><span id="amt">—</span></div>
      <div class="no" id="orderNo">—</div>

      <div class="timer"><span>剩余</span><span class="t" id="timer">30:00</span></div>

      <div class="divider"></div>

      <div class="fee"><span class="k">商品小计</span><span class="v" id="sub">—</span></div>
      <div class="fee"><span class="k">配送费</span><span class="v" id="ship">—</span></div>

      <button class="confirm-btn" id="payBtn">确认支付</button>
      <a href="checkout.html" class="back">返回修改订单</a>
    </div>
  </div>

</div>

<script>
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

  // 加载订单
  (async () => {
    try {
      const o = await API.getOrder(orderNo);
      amount = parseFloat(o.total || o.pay_amount || 0);
      document.getElementById('amt').textContent = API.money(amount);
      document.getElementById('sub').textContent = '¥' + API.money(o.amount?.product ?? amount);
      const shipFee = parseFloat(o.amount?.delivery_fee ?? 0);
      document.getElementById('ship').textContent = shipFee > 0 ? '¥' + API.money(shipFee) : '免运费';
    } catch (e) {
      API.toast('订单加载失败：' + e.message);
    }
  })();

  // 选渠道
  document.querySelectorAll('.method').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.method').forEach(x => x.classList.remove('on'));
      el.classList.add('on');
      channel = el.dataset.ch;
    });
  });

  // 倒计时
  let total = 30 * 60;
  const timerEl = document.getElementById('timer');
  const t = setInterval(() => {
    total--;
    if (total <= 0) { clearInterval(t); timerEl.textContent = '00:00'; return; }
    const m = String(Math.floor(total / 60)).padStart(2, '0');
    const s = String(total % 60).padStart(2, '0');
    timerEl.textContent = m + ':' + s;
  }, 1000);

  // 支付
  const btn = document.getElementById('payBtn');
  btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.textContent = '支付中…';

    try {
      const r = await API.createPayment(orderNo, channel);

      if (channel === 'mock') {
        // mock 渠道：后端会立即回调，直接查订单状态
        await new Promise(res => setTimeout(res, 800));
        const o = await API.getOrder(orderNo);
        if (o.status === 'paid' || o.status === 'preparing') {
          location.href = 'order-success.html?order_no=' + encodeURIComponent(orderNo);
          return;
        }
        API.toast('支付已提交，当前状态：' + (o.status_text || o.status));
        btn.disabled = false;
        btn.textContent = '确认支付';
      } else {
        // 真实渠道：跳转收银台（现在没有）
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
</script>
'''

# ══════════════════════════════════════════════════════════
# 写文件
# ══════════════════════════════════════════════════════════

# checkout
checkout_html = (
    HEAD.format(title="确认订单 | 跳舞兰", extra_css="")
    + checkout_body
    + FOOT
)
with open(os.path.join(PROTO, "checkout.html"), "w", encoding="utf-8") as f:
    f.write(checkout_html)
print("  checkout.html")

# pay
pay_html = (
    HEAD.format(title="支付 | 跳舞兰", extra_css=pay_extra_css)
    + pay_body
    + FOOT
)
with open(os.path.join(PROTO, "pay.html"), "w", encoding="utf-8") as f:
    f.write(pay_html)
print("  pay.html")

print("\n完成")
