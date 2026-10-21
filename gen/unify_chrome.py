# -*- coding: utf-8 -*-
"""统一全套页面的页眉页脚，字体改无衬线（Logo 保留衬线）"""

import os, glob, re

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

# ══════════════════════════════════════════════════════════
# 统一页眉
# ══════════════════════════════════════════════════════════
HEADER_HTML = '''<header class="site-header">
  <div class="hd-top">
    <a href="#">Contact</a>
    <a href="#">Login</a>
  </div>
  <div class="hd-brand">
    <a href="index.html">
      <h1>跳舞兰</h1>
      <span class="en">Tiao Wu Lan</span>
    </a>
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
</header>'''

# ══════════════════════════════════════════════════════════
# 统一页脚
# ══════════════════════════════════════════════════════════
FOOTER_HTML = '''<footer class="site-footer">
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
    <div class="social">
      <a href="#">ig</a><a href="#">wx</a><a href="#">xhs</a><a href="#">dy</a>
    </div>
  </div>
</footer>'''

# ══════════════════════════════════════════════════════════
# 统一 CSS
# ══════════════════════════════════════════════════════════
CHROME_CSS = '''
<style>
/* ═══ 统一页眉 ═══ */
.site-header{background:#fff}

.hd-top{
  padding:13px 40px 0;
  display:flex;justify-content:flex-end;gap:24px;
  font-size:12px;color:#666;
  letter-spacing:.02em;
}
.hd-top a{transition:color .2s}
.hd-top a:hover{color:#1a1a1a}

.hd-brand{padding:20px 24px 26px;text-align:center}
.hd-brand a{display:block}
.hd-brand h1{
  font-family:'Noto Serif SC',-apple-system,sans-serif;
  font-size:22px;font-weight:400;
  letter-spacing:.5em;text-indent:.5em;
  line-height:1;color:#1a1a1a;
}
.hd-brand .en{
  display:block;margin-top:9px;
  font-size:10px;letter-spacing:.42em;
  text-transform:uppercase;color:#999;
}

.hd-nav{border-top:1px solid #e5e5e5;border-bottom:1px solid #e5e5e5;padding:0 10px}
.hd-nav ul{display:flex;justify-content:center;list-style:none;min-width:max-content}
.hd-nav a{
  display:block;padding:15px 18px;
  font-size:13px;color:#666;
  white-space:nowrap;transition:color .2s;
}
.hd-nav a:hover{color:#1a1a1a}

/* ═══ 统一页脚 ═══ */
.site-footer{background:#f1efeb;border-top:1px solid #e5e5e5;padding:56px 0 0}

.ft-row{
  display:flex;gap:0;padding:0 40px 44px;
  overflow-x:auto;scrollbar-width:none;
  max-width:1560px;margin:0 auto;
}
.ft-row::-webkit-scrollbar{display:none}

.ft-brand{
  flex:0 0 auto;padding-right:48px;margin-right:48px;
  border-right:1px solid #ddd9d2;min-width:200px;
}
.ft-brand h4{
  font-family:'Noto Serif SC',-apple-system,sans-serif;
  font-size:15px;font-weight:400;
  letter-spacing:.4em;text-indent:.4em;
  color:#1a1a1a;line-height:1;margin-bottom:10px;
}
.ft-brand .en{
  font-size:9px;letter-spacing:.34em;
  text-transform:uppercase;color:#999;
}
.ft-brand .slogan{
  margin-top:20px;font-size:11px;line-height:2;color:#888;
}

.ft-col{flex:0 0 auto;padding-right:48px;min-width:110px}
.ft-col:last-child{padding-right:0}
.ft-col h5{
  font-size:10px;font-weight:500;
  letter-spacing:.22em;text-transform:uppercase;
  color:#999;margin-bottom:14px;
}
.ft-col a{
  display:block;font-size:12px;line-height:2.4;
  color:#555;white-space:nowrap;transition:color .2s;
}
.ft-col a:hover{color:#1a1a1a}

.ft-bottom{
  display:flex;justify-content:space-between;align-items:center;gap:20px;
  padding:22px 40px;
  border-top:1px solid #ddd9d2;
  max-width:1560px;margin:0 auto;
  flex-wrap:wrap;
}
.ft-bottom .cr{font-size:10px;color:#999;letter-spacing:.02em}
.social{display:flex;gap:9px}
.social a{
  width:28px;height:28px;border:1px solid #ddd9d2;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:9px;color:#777;transition:all .25s;
}
.social a:hover{background:#1a1a1a;color:#fff;border-color:#1a1a1a}

/* ═══ 全站无衬线（除 Logo）═══ */
body{
  font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue","Segoe UI","PingFang SC","Microsoft YaHei",sans-serif !important;
}
h1,h2,h3,h4,h5,h6,
.page-head h2,.info h1,.coll-head h1,.art-head h1,
.hero h2,.duo .txt h3,.card .info h3,.rel-card h4,
.empty h3,.cart-head h2,.result h2,.acc-head h2,
.addr-head h2,.as-head h2,.od-head h2,.as-head h2,
.ft-brand h4,.login-head h1{
  font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue","Segoe UI","PingFang SC","Microsoft YaHei",sans-serif !important;
  font-weight:400;
  letter-spacing:-.01em;
}
/* Logo 与页脚品牌名保留衬线 */
.hd-brand h1,.ft-brand h4,.brand h1{
  font-family:'Noto Serif SC',serif !important;
  letter-spacing:.5em !important;
}

/* 英文小标题也改无衬线 */
.en,.en-sub,.eyebrow,.kicker,.vendor{
  font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif !important;
  letter-spacing:.14em !important;
}

/* ═══ 响应式 ═══ */
@media (max-width:768px){
  .hd-top{padding:10px 16px 0;gap:16px;font-size:10px}
  .hd-brand{padding:14px 16px 18px}
  .hd-brand h1{font-size:18px;letter-spacing:.4em;text-indent:.4em}
  .hd-brand .en{font-size:8.5px}
  .hd-nav{overflow-x:auto;scrollbar-width:none}
  .hd-nav::-webkit-scrollbar{display:none}
  .hd-nav ul{justify-content:flex-start;margin:0 auto}
  .hd-nav a{padding:12px 14px;font-size:11.5px}

  .ft-row{flex-wrap:wrap;padding:0 20px 32px;gap:28px}
  .ft-brand{border-right:0;padding-right:0;margin-right:0;width:100%}
  .ft-brand .slogan{display:none}
  .ft-col{padding-right:0;min-width:calc(50% - 14px)}
  .ft-bottom{padding:18px 20px;flex-direction:column;align-items:flex-start;gap:12px}
}
</style>
'''

# ══════════════════════════════════════════════════════════
# 处理每个文件
# ══════════════════════════════════════════════════════════

# 每个页面原有的 header 块（正则）
HEADER_PATTERNS = [
    # 1. topbar + brand + mainnav 三件套（base.css 的页面）
    r'<div class="topbar">.*?</nav>',
    r'<div class="topbar">.*?</div>\s*<div class="brand">.*?</div>\s*<nav class="mainnav">.*?</nav>',
    # 2. 单行 nav（shop/product）
    r'<nav class="nav">.*?</nav>',
    # 3. admin 的 topbar（不处理）
]

# footer 块
FOOTER_PATTERN = r'<footer[^>]*>.*?</footer>'
FOOTER_PATTERN2 = r'<footer>.*?</footer>'

count = 0
for p in glob.glob(os.path.join(PROTO, "*.html")):
    fn = os.path.basename(p)
    if fn.startswith("_") or fn == "admin.html":
        continue

    html = open(p, encoding="utf-8").read()
    orig = html

    # ── 1. 移除旧的 header ──
    for pat in HEADER_PATTERNS:
        html = re.sub(pat, "", html, count=1, flags=re.S)

    # ── 2. 移除旧的 footer ──
    html = re.sub(FOOTER_PATTERN, "", html, flags=re.S)
    html = re.sub(FOOTER_PATTERN2, "", html, flags=re.S)

    # ── 3. 插入新 header（紧跟 <body...> 之后）──
    m = re.search(r'(<body[^>]*>)', html)
    if m:
        html = html[:m.end()] + "\n\n" + HEADER_HTML + "\n" + html[m.end():]

    # ── 4. 插入新 footer（</body> 之前）──
    html = html.replace("</body>", FOOTER_HTML + "\n\n</body>")

    # ── 5. 追加统一 CSS（</head> 之前）──
    if "统一页眉" not in html:
        html = html.replace("</head>", CHROME_CSS + "\n</head>")

    if html != orig:
        open(p, "w", encoding="utf-8").write(html)
        count += 1
        print(f"  {fn}")

print(f"\n共处理 {count} 个页面")
