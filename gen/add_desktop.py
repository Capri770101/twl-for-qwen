# -*- coding: utf-8 -*-
"""给所有页面追加桌面端增强样式（响应式，宽屏官网感）"""
import os, glob

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

DESKTOP_CSS = """
<style>
/* ═══════════════════════════════════════════════════════
   桌面端增强（≥1024px）—— 宽屏、多列、大留白
   ═══════════════════════════════════════════════════════ */

@media (min-width:1024px){

  /* 内容限宽居中（背景仍全宽） */
  .topbar,.brand,.mainnav,.crumb,.page-head,.coll-head,
  .content,.section,.sec,.info,.opt,.buy-btns,.ship,
  .meaning,.acc,.detail,.fees,.form-sec,.agree,
  .cart-head,.summary,.note,.note-bar,
  .filter-row,.ctrl,.count-bar,
  .fl-head,.fl-tabs,.fl-list,.art-head,.art-body,
  .faq,.related-head,.prod,.timeline,
  .acc-head,.tabs,.addr-head,.addr,.add,
  .ops,.as-head,.order-ref,.co-head,.result,
  .pay-head,.methods,.secure,
  .body-sec,.cta,.more,.back-link,.insta,
  .story,.hero,.cat-entry,.figure,.duo,.related,
  .foot-row,.foot-bottom,.search-bar,.hot,.result-head,
  .load-more,.login-head,.login-form,.divider,
  .wx-login,.terms,.skip,.items{
    max-width:1320px;
    margin-left:auto;
    margin-right:auto;
  }

  /* 加大左右留白 */
  .info,.opt,.buy-btns,.ship,.meaning,.acc .body,
  .page-head,.coll-head,.story,.sec,.form-sec,.fees,
  .body-sec,.content,.art-body,.faq,.hero{
    padding-left:56px;
    padding-right:56px;
  }
  .foot-row{padding-left:56px;padding-right:56px}

  /* 标题放大 */
  .page-head h2{font-size:48px}
  .coll-head h1{font-size:46px}
  .hero h2{font-size:64px;line-height:1.2}
  .art-head h1{font-size:32px}
  .info h1{font-size:30px}
  .price-row .p{font-size:28px}

  /* 商品网格 3 列 */
  .grid{grid-template-columns:repeat(3,1fr)}
  .rel-grid{grid-template-columns:repeat(4,1fr)}

  /* 双栏：文字 + 图 */
  .duo{display:grid;grid-template-columns:1fr 1fr;align-items:stretch}
  .duo .txt{
    padding:110px 72px;
    display:flex;flex-direction:column;justify-content:center;
  }
  .duo .pic img{aspect-ratio:auto;height:100%;min-height:520px}
  .duo.rev .txt{order:2}
  .duo.rev .pic{order:1}

  /* 分类入口 3 列 */
  .cat-entry{display:grid;grid-template-columns:repeat(3,1fr)}
  .cat-entry a{border-bottom:0;border-right:1px solid #fff}
  .cat-entry a:last-child{border-right:0}
  .cat-entry img{aspect-ratio:3/4}

  /* 大图更宽 */
  .figure img{aspect-ratio:21/9}

  /* Hero / 品牌故事更大 */
  .hero{padding-top:140px;padding-bottom:120px}
  .story{padding-top:120px;padding-bottom:120px}

  /* 页脚加大 */
  .foot-row{padding-top:16px;padding-bottom:56px}
  .foot-brand{min-width:220px;padding-right:56px;margin-right:56px}
  .foot-col{padding-right:56px;min-width:130px}
  .foot-brand h4{font-size:17px}

  /* 花语列表两列 */
  .fl-list{display:grid;grid-template-columns:repeat(2,1fr)}
  .fl-item{border-right:1px solid var(--gray-e)}
  .fl-item:nth-child(2n){border-right:0}

  /* 购物袋两栏 */
  .items{max-width:880px}
  .summary{max-width:1320px}

  /* 订单列表两列 */
  .order{max-width:100%}

  /* 登录页限宽 */
  .login-form,.login-head{max-width:480px}

  /* 搜索框限宽 */
  .search-bar,.hot,.result-head{max-width:900px}
}

/* 超宽屏 */
@media (min-width:1440px){
  .grid{grid-template-columns:repeat(4,1fr)}
  .topbar,.brand,.mainnav,.crumb,.page-head,.coll-head,
  .content,.section,.sec,.info,.opt,.buy-btns,.ship,
  .meaning,.acc,.detail,.fees,.form-sec,.agree,
  .cart-head,.summary,.note,.note-bar,
  .filter-row,.ctrl,.count-bar,
  .fl-head,.fl-tabs,.fl-list,.art-head,.art-body,
  .faq,.related-head,.prod,.timeline,
  .acc-head,.tabs,.addr-head,.addr,.add,
  .ops,.as-head,.order-ref,.co-head,.result,
  .pay-head,.methods,.secure,
  .body-sec,.cta,.more,.back-link,.insta,
  .story,.hero,.cat-entry,.figure,.duo,.related,
  .foot-row,.foot-bottom,
  .load-more,.login-head,.login-form,.divider,
  .wx-login,.terms,.skip{
    max-width:1520px;
  }
  .hero h2{font-size:76px}
}
</style>
"""

count = 0
for p in glob.glob(os.path.join(PROTO, "*.html")):
    fn = os.path.basename(p)
    if fn.startswith("_"):
        continue  # 跳过索引/预览页
    html = open(p, encoding="utf-8").read()

    # 避免重复追加
    if "桌面端增强" in html:
        continue

    # 追加到 </body> 之前
    if "</body>" in html:
        html = html.replace("</body>", DESKTOP_CSS + "\n</body>")
        open(p, "w", encoding="utf-8").write(html)
        print(f"  {fn}: 已追加桌面样式")
        count += 1

print(f"\n共处理 {count} 个页面")
