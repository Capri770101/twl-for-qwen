# -*- coding: utf-8 -*-
"""阶段3：地址簿 / 花语 / 售后上传 接真实 API"""

import os

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"


# ══════════════════════════════════════════════════════════
# 1. 地址簿接 API
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "address.html")
html = open(p, encoding="utf-8").read()

# 替换内容区为动态渲染
new_body = '''<div class="page-head">
  <h1>地址簿</h1>
  <p id="subTitle">保存常用地址，下次下单不用重填。</p>
</div>

<div class="addr-wrap">
  <div class="grid" id="grid">
    <div style="padding:60px 0;text-align:center;color:#999;font-size:14px;grid-column:1/-1">加载中…</div>
  </div>
</div>

<script src="api.js"></script>
<script>
(function(){
  const grid = document.getElementById('grid');
  const subTitle = document.getElementById('subTitle');

  const TOKEN_KEY = 'twl_token';

  function token() {
    return localStorage.getItem(TOKEN_KEY);
  }

  async function request(path, opts) {
    opts = opts || {};
    opts.headers = opts.headers || {};
    opts.headers['Content-Type'] = 'application/json';
    const t = token();
    if (t) opts.headers['Authorization'] = 'Bearer ' + t;

    const r = await fetch('/api/v1' + path, opts);
    const j = await r.json();
    if (j.code !== 0) throw new Error(j.message || '请求失败');
    return j.data;
  }

  /* 渲染 */
  function render(list) {
    subTitle.textContent = `共 ${list.length} 个地址`;

    let html = list.map(a => `
      <div class="card" data-id="${a.id}">
        <div class="top">
          <span class="name">${a.receiver}</span>
          <span class="phone">${a.phone}</span>
          ${a.is_default ? '<span class="def">默认</span>' : ''}
          ${a.tag ? `<span class="tag">${a.tag}</span>` : ''}
        </div>
        <div class="detail">${a.full_address || a.detail}</div>
        <div class="ops">
          ${a.is_default ? '' : '<a href="#" data-act="default">设为默认</a>'}
          <a href="#" data-act="edit">编辑</a>
          <a href="#" data-act="delete" style="color:#8a3c3c">删除</a>
        </div>
      </div>
    `).join('');

    html += '<div class="add-new" id="addNew">＋ 新增地址</div>';

    grid.innerHTML = html;
    bindEvents();
  }

  /* 绑定事件 */
  function bindEvents() {
    document.querySelectorAll('.card .ops a').forEach(el => {
      el.addEventListener('click', async e => {
        e.preventDefault();
        const card = el.closest('.card');
        const id = card.dataset.id;
        const act = el.dataset.act;
        const name = card.querySelector('.name').textContent;

        if (act === 'delete') {
          if (!confirm(`确定删除「${name}」这个地址吗？`)) return;
          try {
            await request('/addresses/' + id, { method: 'DELETE' });
            API.toast('已删除');
            load();
          } catch (err) {
            API.toast(err.message);
          }
        } else if (act === 'default') {
          try {
            await request('/addresses/' + id + '/default', { method: 'POST' });
            API.toast('已设为默认');
            load();
          } catch (err) {
            API.toast(err.message);
          }
        } else if (act === 'edit') {
          openForm(id, card);
        }
      });
    });

    const addBtn = document.getElementById('addNew');
    if (addBtn) addBtn.addEventListener('click', () => openForm(null, null));
  }

  /* 弹窗表单（用 prompt 简化，正式环境要换成真表单） */
  async function openForm(id, card) {
    let cur = { receiver: '', phone: '', province: '', city: '', district: '', detail: '', tag: '' };

    if (id && card) {
      cur = {
        receiver: card.querySelector('.name').textContent,
        phone: card.querySelector('.phone').textContent,
        detail: card.querySelector('.detail').textContent,
        province: '', city: '', district: '', tag: '',
      };
    }

    const receiver = prompt('收件人姓名', cur.receiver);
    if (receiver === null) return;

    const phone = prompt('手机号', cur.phone);
    if (phone === null) return;

    const detail = prompt('详细地址', cur.detail);
    if (detail === null) return;

    const tag = prompt('标签（家/公司/学校，可留空）', cur.tag || '');
    if (tag === null) return;

    const payload = { receiver, phone, detail, tag: tag || null };

    try {
      if (id) {
        await request('/addresses/' + id, { method: 'PUT', body: JSON.stringify(payload) });
        API.toast('已保存');
      } else {
        await request('/addresses', { method: 'POST', body: JSON.stringify(payload) });
        API.toast('已添加');
      }
      load();
    } catch (err) {
      API.toast(err.message);
    }
  }

  /* 加载 */
  async function load() {
    if (!token()) {
      grid.innerHTML = `
        <div style="grid-column:1/-1;padding:80px 0;text-align:center;color:#999;font-size:14px">
          请先登录才能使用地址簿<br><br>
          <a href="login.html" style="display:inline-block;padding:12px 32px;border:1px solid #1a1a1a;border-radius:4px;color:#1a1a1a;font-size:14px">去登录</a>
        </div>
      `;
      subTitle.textContent = '';
      return;
    }

    try {
      const data = await request('/addresses');
      render(data.items || []);
    } catch (err) {
      grid.innerHTML = `<div style="grid-column:1/-1;padding:80px 0;text-align:center;color:#999;font-size:14px">加载失败：${err.message}</div>`;
    }
  }

  load();
})();
</script>'''

start = html.find('<div class="page-head">')
footer_start = html.find('<footer')

if start > 0:
    if footer_start > start:
        html = html[:start] + new_body + "\n\n" + html[footer_start:]
    open(p, "w", encoding="utf-8").write(html)
    print("  address.html: 接真实 API")


# ══════════════════════════════════════════════════════════
# 2. 花语百科从 API 读
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "flower-language.html")
html = open(p, encoding="utf-8").read()

new_fl = '''<div class="page-head">
  <h1>花语百科</h1>
  <p>每种花都有它的意思。选花之前，先知道它要说什么。</p>
</div>

<div class="filters">
  <div class="chips" id="chips">
    <span class="chip on" data-cat="">全部</span>
  </div>
  <div class="count" id="count">加载中…</div>
</div>

<div class="list" id="list">
  <div style="grid-column:1/-1;padding:80px 0;text-align:center;color:#999;font-size:14px">加载中…</div>
</div>

<div class="cta">
  <a href="shop.html">看看用这些花做的花束</a>
</div>

<script src="api.js"></script>
<script>
(function(){
  const listEl = document.getElementById('list');
  const countEl = document.getElementById('count');
  const chipsEl = document.getElementById('chips');

  let allArticles = [];
  let curCat = '';

  /* 渲染 */
  function render() {
    const list = curCat ? allArticles.filter(a => a.category === curCat) : allArticles;

    countEl.textContent = list.length + ' 篇';

    if (list.length === 0) {
      listEl.innerHTML = '<div style="grid-column:1/-1;padding:80px 0;text-align:center;color:#999;font-size:14px">还没有文章</div>';
      return;
    }

    listEl.innerHTML = list.map(a => `
      <a href="flower-language-detail.html?slug=${encodeURIComponent(a.slug)}" class="item">
        <div class="pic">${a.cover ? `<img src="${a.cover}" alt="${a.title}" loading="lazy">` : ''}</div>
        <div class="info">
          <h3>${a.title}</h3>
          <div class="en">${a.category || ''}</div>
          <p>${a.meaning || a.summary || ''}</p>
        </div>
      </a>
    `).join('');
  }

  /* 加载 */
  (async () => {
    try {
      const data = await API.request('/articles?size=100');
      allArticles = data.items || [];

      // 分类
      const cats = [...new Set(allArticles.map(a => a.category).filter(Boolean))];
      const NAMES = { rose: '玫瑰', tulip: '郁金香', sunflower: '向日葵', hydrangea: '绣球', camellia: '山茶' };
      chipsEl.innerHTML = '<span class="chip on" data-cat="">全部</span>' +
        cats.map(c => `<span class="chip" data-cat="${c}">${NAMES[c] || c}</span>`).join('');

      chipsEl.querySelectorAll('.chip').forEach(el => {
        el.addEventListener('click', () => {
          chipsEl.querySelectorAll('.chip').forEach(x => x.classList.remove('on'));
          el.classList.add('on');
          curCat = el.dataset.cat;
          render();
        });
      });

      render();
    } catch (e) {
      listEl.innerHTML = `<div style="grid-column:1/-1;padding:80px 0;text-align:center;color:#999;font-size:14px">加载失败：${e.message}</div>`;
      countEl.textContent = '';
    }
  })();
})();
</script>'''

start = html.find('<div class="page-head">')
footer_start = html.find('<footer')
cta_end = html.find('<div class="cta">')

if start > 0:
    # 找到 cta 结束（footer 之前）
    insert_end = footer_start if footer_start > 0 else html.find('</body>')
    html = html[:start] + new_fl + "\n\n" + html[insert_end:]
    open(p, "w", encoding="utf-8").write(html)
    print("  flower-language.html: 从 API 读")


# ══════════════════════════════════════════════════════════
# 3. 花语详情从 API 读
# ══════════════════════════════════════════════════════════
p = os.path.join(PROTO, "flower-language-detail.html")
html = open(p, encoding="utf-8").read()

new_fld = '''<div class="art-wrap" id="app">
  <div style="padding:120px 40px;text-align:center;color:#999;font-size:14px">加载中…</div>
</div>

<script src="api.js"></script>
<script>
(function(){
  const params = new URLSearchParams(location.search);
  const slug = params.get('slug') || 'champagne-rose';
  const app = document.getElementById('app');

  /* 简易 Markdown 渲染 */
  function md(text) {
    if (!text) return '';
    let h = text
      .replace(/^# (.+)$/gm, '<h2>$1</h2>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^### (.+)$/gm, '<h3 style="font-size:19px;font-weight:400;margin:36px 0 14px">$1</h3>')
      .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/\\n\\n/g, '</p><p>');
    h = '<p>' + h + '</p>';
    return h;
  }

  function render(a) {
    const faqHtml = (a.faq || []).map(f => `
      <div class="faq-item">
        <div class="q"><span class="mark">Q</span>${f.question}</div>
        <div class="a">${f.answer}</div>
      </div>
    `).join('');

    // 目录：从正文里提取 h2
    const headings = [];
    const re = /^## (.+)$/gm;
    let m;
    while ((m = re.exec(a.content || '')) !== null) {
      headings.push(m[1]);
    }

    app.innerHTML = `
      <article class="art-left">
        <div class="crumb">
          <a href="index.html">首页</a> / <a href="flower-language.html">花语百科</a> / ${a.title}
        </div>

        <h1>${a.title}</h1>
        <div class="en">${a.category || ''}</div>

        ${a.cover ? `<div class="hero-img"><img src="${a.cover}" alt="${a.title}"></div>` : ''}

        ${a.meaning ? `<div class="meaning-box"><div class="lbl">花语</div><p>${a.meaning}</p></div>` : ''}

        <div class="article-body">${md(a.content)}</div>

        ${faqHtml ? `<div class="faq"><h2>常见问题</h2>${faqHtml}</div>` : ''}
      </article>

      <aside class="art-right">
        ${headings.length ? `
        <div class="toc">
          <div class="lbl">目录</div>
          ${headings.map((h, i) => `<a href="#sec-${i}">${h}</a>`).join('')}
        </div>` : ''}

        <div class="rel-box">
          <div class="lbl">相关花束</div>
          <a href="shop.html" class="rel-item" style="display:block;padding:12px 0;font-size:13px;color:#666">
            看看全部花束 →
          </a>
        </div>
      </aside>
    `;
  }

  (async () => {
    try {
      const a = await API.request('/articles/' + encodeURIComponent(slug));
      render(a);
    } catch (e) {
      app.innerHTML = `
        <div style="padding:120px 40px;text-align:center;color:#999">
          <p style="font-size:16px;margin-bottom:16px">文章加载失败</p>
          <p style="font-size:13px;margin-bottom:24px">${e.message}</p>
          <a href="flower-language.html" style="display:inline-block;padding:12px 32px;border:1px solid #1a1a1a;border-radius:4px;color:#1a1a1a;font-size:14px">返回花语百科</a>
        </div>
      `;
    }
  })();
})();
</script>'''

start = html.find('<div class="art-wrap"')
footer_start = html.find('<footer')

if start > 0:
    insert_end = footer_start if footer_start > 0 else html.find('</body>')
    html = html[:start] + new_fld + "\n\n" + html[insert_end:]
    open(p, "w", encoding="utf-8").write(html)
    print("  flower-language-detail.html: 从 API 读")


print("\n完成")
