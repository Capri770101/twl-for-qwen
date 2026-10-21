# -*- coding: utf-8 -*-
"""对齐：商城筛选、搜索、售后提交、后台工单"""

import os

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"


# ══════════════════════════════════════════════════════════
# 1. 商城筛选走真 API
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "shop.html")
html = open(p, encoding="utf-8").read()

new_js = '''<script>
(function(){
  let allProducts = [];
  let categories = [];
  let curCat = '';
  let sortIdx = 0;
  const SORTS = [
    { label: '推荐', val: '' },
    { label: '价格从低到高', val: 'price_asc' },
    { label: '价格从高到低', val: 'price_desc' },
  ];

  const grid = document.getElementById('grid');
  const totalCount = document.getElementById('totalCount');
  const errorBox = document.getElementById('errorBox');

  /* ── 渲染 ── */
  function render() {
    if (allProducts.length === 0) {
      grid.innerHTML = '<div style="grid-column:1/-1;padding:80px 0;text-align:center;color:#999;font-size:14px">这个分类下暂时没有花束</div>';
      totalCount.textContent = '0 件商品';
      return;
    }

    totalCount.textContent = allProducts.length + ' 件商品';

    grid.innerHTML = allProducts.map(p => {
      const price = API.money(p.price);
      const orig = p.original_price && parseFloat(p.original_price) > parseFloat(p.price)
        ? `<span class="was">¥${API.money(p.original_price)}</span>` : '';
      return `
        <a href="product.html?id=${encodeURIComponent(p.id)}" class="card">
          <div class="pic"><img src="${p.cover || ''}" alt="${p.name}" loading="lazy" onerror="this.style.background='#e8e6e2'"></div>
          <div class="info">
            <h3>${p.name}</h3>
            <div class="price">¥${price}${orig}</div>
          </div>
        </a>
      `;
    }).join('');
  }

  /* ── 加载（调真 API）── */
  async function load() {
    try {
      const params = { size: 100 };
      if (curCat) params.category = curCat;
      const sortVal = SORTS[sortIdx].val;
      if (sortVal) params.sort = sortVal;

      const data = await API.listProducts(params);
      allProducts = data.items || [];
      grid.innerHTML = '';
      render();
    } catch (e) {
      grid.innerHTML = '';
      errorBox.style.display = 'block';
      errorBox.innerHTML = `
        <div class="error-box">
          <h2>商品加载失败</h2>
          <p>${e.message}<br><br>确认后端：<code>http://127.0.0.1:8000/health</code></p>
          <button onclick="location.reload()">重新加载</button>
        </div>
      `;
      totalCount.textContent = '加载失败';
    }
  }

  /* ── 分类筛选（调真 API）── */
  const catEl = document.getElementById('catFilter');
  catEl.addEventListener('click', () => {
    const opts = [{ id: '', name: '全部' }, ...categories];
    let idx = opts.findIndex(c => c.id === curCat);
    idx = (idx + 1) % opts.length;
    curCat = opts[idx].id;
    catEl.innerHTML = opts[idx].name + ' <span class="caret">▾</span>';
    load();
  });

  /* ── 排序（调真 API）── */
  const sortEl = document.getElementById('sortBtn');
  sortEl.addEventListener('click', () => {
    sortIdx = (sortIdx + 1) % SORTS.length;
    sortEl.innerHTML = SORTS[sortIdx].label + ' <span class="caret">▾</span>';
    load();
  });

  /* ── 启动 ── */
  (async () => {
    try {
      const c = await API.getCategories();
      categories = (c.items || c || []).map(x =>
        typeof x === 'string' ? { id: x, name: x } : x
      );
    } catch (e) {
      categories = [];
    }
    load();
  })();
})();
</script>'''

# 替换最后一个 script 块
start = html.rfind('<script>')
end = html.rfind('</script>')
if start > 0 and end > start:
    html = html[:start] + new_js + html[end + len('</script>'):]
    open(p, "w", encoding="utf-8").write(html)
    print("  shop.html: 筛选走真 API")


# ══════════════════════════════════════════════════════════
# 2. 搜索页走真 API
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "search.html")
html = open(p, encoding="utf-8").read()

# 找结果区，替换成动态渲染
new_search_body = '''<div class="search-wrap">

  <div class="search-box">
    <span class="icon">⌕</span>
    <input id="q" placeholder="搜花名、花材、场景" autocomplete="off">
  </div>

  <div class="hot">
    <div class="lbl">热门搜索</div>
    <div class="tags" id="tags">
      <a href="#">玫瑰</a>
      <a href="#">向日葵</a>
      <a href="#">郁金香</a>
      <a href="#">绣球</a>
      <a href="#">山茶</a>
      <a href="#">洋桔梗</a>
    </div>
  </div>

  <div class="result-head">
    <h2 id="resultTitle">全部商品</h2>
    <span class="n" id="resultCount"></span>
  </div>

  <div class="grid" id="grid">
    <div style="grid-column:1/-1;padding:60px 0;text-align:center;color:#999;font-size:14px">加载中…</div>
  </div>

</div>

<script src="api.js"></script>
<script>
(function(){
  const input = document.getElementById('q');
  const title = document.getElementById('resultTitle');
  const count = document.getElementById('resultCount');
  const grid = document.getElementById('grid');

  let timer = null;

  function render(list, keyword) {
    title.textContent = keyword ? `「${keyword}」的搜索结果` : '全部商品';
    count.textContent = list.length + ' 件';

    if (list.length === 0) {
      grid.innerHTML = '<div style="grid-column:1/-1;padding:80px 0;text-align:center;color:#999;font-size:14px">没有找到相关商品</div>';
      return;
    }

    grid.innerHTML = list.map(p => {
      const price = API.money(p.price);
      const orig = p.original_price && parseFloat(p.original_price) > parseFloat(p.price)
        ? `<span class="was" style="color:#999;text-decoration:line-through;margin-left:6px;font-size:12px">¥${API.money(p.original_price)}</span>` : '';
      return `
        <a href="product.html?id=${encodeURIComponent(p.id)}" class="card">
          <div class="pic"><img src="${p.cover || ''}" alt="${p.name}" loading="lazy"></div>
          <div class="info"><h3>${p.name}</h3><div class="p">¥${price}${orig}</div></div>
        </a>
      `;
    }).join('');
  }

  async function search(kw) {
    try {
      const params = { size: 100 };
      if (kw) params.keyword = kw;
      const data = await API.listProducts(params);
      render(data.items || [], kw);
    } catch (e) {
      grid.innerHTML = `<div style="grid-column:1/-1;padding:80px 0;text-align:center;color:#999;font-size:14px">搜索失败：${e.message}</div>`;
    }
  }

  // 输入防抖
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => search(input.value.trim()), 320);
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      clearTimeout(timer);
      search(input.value.trim());
    }
  });

  // 热门词
  document.querySelectorAll('#tags a').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      const kw = el.textContent.trim();
      input.value = kw;
      search(kw);
    });
  });

  // 初始：URL 带 q 就搜，否则显示全部
  const params = new URLSearchParams(location.search);
  const initQ = params.get('q') || '';
  input.value = initQ;
  search(initQ);
})();
</script>

'''

start = html.find('<div class="search-wrap">')
footer_start = html.find('<footer')
end_marker = '</body>'
end = html.find(end_marker)

if start > 0:
    if footer_start > start:
        html = html[:start] + new_search_body + html[footer_start:]
    else:
        html = html[:start] + new_search_body + html[end:]
    open(p, "w", encoding="utf-8").write(html)
    print("  search.html: 走真 API keyword")


# ══════════════════════════════════════════════════════════
# 3. 售后提交接真接口
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "after-sale.html")
html = open(p, encoding="utf-8").read()

new_as_js = '''<script src="api.js"></script>
<script>
(function(){
  const params = new URLSearchParams(location.search);
  const orderNo = params.get('order_no') || localStorage.getItem('twl_last_order');

  const types = document.querySelectorAll('.type');
  let curType = '花材不新鲜';

  types.forEach(el => {
    el.addEventListener('click', () => {
      types.forEach(x => x.classList.remove('on'));
      el.classList.add('on');
      curType = el.textContent.trim();
    });
  });

  // 自动选中第一个
  if (types.length > 0 && !document.querySelector('.type.on')) {
    types[0].classList.add('on');
    curType = types[0].textContent.trim();
  }

  // 关联订单
  const orderBox = document.querySelector('.as-right .box h2');
  const itemBox = document.querySelector('.as-right .item');
  if (orderNo && itemBox) {
    (async () => {
      try {
        const o = await API.getOrder(orderNo);
        itemBox.innerHTML = `
          <div class="t">
            <h3>${(o.items || []).map(i => i.product_name + '×' + i.qty).join('、')}</h3>
            <div class="s">${o.order_no}<br>${(o.created_at || '').slice(0,10)} ${o.status_text || ''}</div>
          </div>
        `;
        const phoneInput = document.querySelector('.phone-row input');
        if (phoneInput) phoneInput.value = o.phone || '';
      } catch (e) {
        itemBox.innerHTML = `<div class="t"><div class="s">订单加载失败：${e.message}</div></div>`;
      }
    })();
  } else if (itemBox && !orderNo) {
    itemBox.innerHTML = '<div class="t"><div class="s">没有关联订单（从订单详情页进入可自动关联）</div></div>';
  }

  // 上传提示
  const up = document.querySelector('.up-box');
  if (up) up.addEventListener('click', () => API.toast('演示环境不支持上传，图片字段会留空'));

  const x = document.querySelector('.up-thumb .x');
  if (x) x.addEventListener('click', () => { x.parentElement.remove(); API.toast('已移除图片'); });

  // 提交
  const submit = document.querySelector('.submit');
  submit.addEventListener('click', async () => {
    const reason = document.querySelector('textarea')?.value.trim();
    const phone = document.querySelector('.phone-row input')?.value.trim();

    if (!orderNo) { API.toast('没有关联订单，无法提交'); return; }
    if (!reason || reason.length < 5) { API.toast('请描述具体问题（至少 5 个字）'); return; }

    submit.disabled = true;
    submit.textContent = '提交中…';

    try {
      const r = await API.createTicket({
        order_no: orderNo,
        type: curType,
        reason: reason,
        images: [],
        contact_phone: phone || null,
      });
      API.toast('已提交，工单号 ' + (r.ticket_no || ''));
      submit.textContent = '已提交 · ' + (r.ticket_no || '');
      submit.style.background = '#3d6b47';
    } catch (e) {
      API.toast(e.message);
      submit.disabled = false;
      submit.textContent = '提交申请';
    }
  });
})();
</script>'''

start = html.rfind('<script>')
end = html.rfind('</script>')
if start > 0 and end > start:
    html = html[:start] + new_as_js + html[end + len('</script>'):]
    open(p, "w", encoding="utf-8").write(html)
    print("  after-sale.html: 接 POST /tickets")


print("\n完成")
