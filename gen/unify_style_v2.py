# -*- coding: utf-8 -*-
"""把所有页面统一到新风格：无衬线大字标题 + 浅灰信息块 + 细分割线"""

import os, glob

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

STYLE_CSS = '''
<style>
/* ═══════════════════════════════════════════════════════
   全站统一风格 v2
   无衬线 · 大标题 · 浅灰信息块 · 细线 · 大留白
   ═══════════════════════════════════════════════════════ */

/* ── 字体：全部无衬线 ── */
body,button,input,textarea,select{
  font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue","Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  -webkit-font-smoothing:antialiased;
}

/* 标题：无衬线 + 负字距（现代感） */
h1,h2,h3,h4,h5,h6,
.page-head h2,.info h1,.coll-head h1,.art-head h1,
.hero h2,.duo .txt h3,.card .info h3,.rel-card h4,
.empty h3,.cart-head h2,.result h2,.acc-head h2,
.addr-head h2,.as-head h2,.od-head h2,
.sec-head h2,.statement h2,.advisor h2,
.fl-head h2,.ordered h3,
.body-sec h3,.section h2{
  font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue","Segoe UI","PingFang SC","Microsoft YaHei",sans-serif !important;
  font-weight:400 !important;
  letter-spacing:-.015em !important;
}

/* Logo 与品牌名保留衬线 */
.hd-brand h1,.ft-brand h4,.brand h1,.logo{
  font-family:'Noto Serif SC',serif !important;
  letter-spacing:.5em !important;
}

/* 英文小标题：无衬线，加大字距 */
.en,.en-sub,.eyebrow,.kicker,.vendor,.no{
  font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif !important;
  letter-spacing:.14em !important;
}

/* ── 页面主标题：放大 ── */
.page-head{padding:72px 40px 48px !important}
.page-head h2{font-size:56px !important;line-height:1.08 !important;margin-bottom:18px !important}
.page-head .kicker{margin-bottom:22px !important;color:#999 !important}

/* ── 分割线改淡 ── */
.page-head{border-bottom-color:#ebe9e5 !important}
.sec,.body-sec,.detail,.info,.fees,.form-sec,.cart-head,
.art-body,.faq,.timeline,.od-head,.acc-head,.addr-head,
.as-head,.co-head,.result,.pay-head,.coll-head,.items,
.order,.addr,.item,.fl-item,.order-ref{
  border-color:#ebe9e5 !important;
}

/* ── 卡片信息块改浅灰底 ── */
.card .info{background:#f1efeb !important}
.grid{background:transparent !important;gap:24px !important;padding:0 40px 80px !important}

/* ── 按钮：统一 4px 圆角 ── */
.btn,.btn-block,.buy-btns a,.dock .btn,
.alert .actions .btn,.alert .actions .btn-ghost,
.add a,.empty a,.load-more a,.back-link a,
.code-btn,.btn-login,.wx-login,.btn-add,.btn-buy{
  border-radius:4px !important;
}

/* ── 折叠面板 / 表单：细线 ── */
details,summary{border-color:#ebe9e5 !important}
.field,.row,.irow,.drow,.spec-row,.fee,.sum-row,.row-form{
  border-color:#ebe9e5 !important;
}

/* ── 标题区留白加大 ── */
.story{padding:100px 40px !important;background:#f1efeb !important}
.story p{font-size:16px !important;line-height:2 !important;color:#333 !important;max-width:680px !important}
.hero{padding:120px 40px 100px !important}
.hero h2{font-size:72px !important;line-height:1.15 !important}
.hero .sub{font-size:14px !important;letter-spacing:.18em !important}

/* ── 花语/内容页 ── */
.art-head h1{font-size:44px !important;line-height:1.2 !important}
.art-body p,.body-sec p{font-size:16px !important;line-height:1.95 !important;color:#333 !important}
.art-body h2,.body-sec h3{font-size:22px !important;margin-top:52px !important}

/* ── 让所有内容区块居中限宽 ── */
@media (min-width:1024px){
  .page-head,.content,.section,.sec,.body-sec,.art-body,
  .timeline,.detail,.fees,.form-sec,.agree,.cart-head,
  .summary,.note,.note-bar,.info,.opt,.buy-actions,.ship,
  .meaning,.acc,.od-head,.acc-head,.addr-head,.as-head,
  .co-head,.result,.pay-head,.methods,.secure,.fl-head,
  .fl-tabs,.fl-list,.faq,.related-head,.prod,.ops,
  .items,.order-ref,.login-head,.login-form,.divider,
  .wx-login,.terms,.skip,.more,.back-link,.cta,.insta,
  .cat-entry,.search-bar,.hot,.result-head,.load-more{
    max-width:1320px;
    margin-left:auto;
    margin-right:auto;
  }
}

/* ── 移动端 ── */
@media (max-width:768px){
  .page-head{padding:44px 16px 32px !important}
  .page-head h2{font-size:34px !important}
  .hero{padding:64px 20px 56px !important}
  .hero h2{font-size:38px !important}
  .story{padding:56px 20px !important}
  .story p{font-size:14px !important}
  .art-head h1{font-size:26px !important}
  .art-body p,.body-sec p{font-size:14px !important}
  .grid{padding:0 12px 48px !important;gap:12px !important}
}
</style>
'''

count = 0
for p in sorted(glob.glob(os.path.join(PROTO, "*.html"))):
    fn = os.path.basename(p)
    if fn.startswith("_") or fn == "admin.html":
        continue

    html = open(p, encoding="utf-8").read()

    if "全站统一风格 v2" in html:
        continue

    html = html.replace("</head>", STYLE_CSS + "\n</head>")
    open(p, "w", encoding="utf-8").write(html)
    print(f"  {fn}")
    count += 1

print(f"\n共 {count} 个页面应用新风格")
