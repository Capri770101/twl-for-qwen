# -*- coding: utf-8 -*-
"""批量生成剩余页面（宽屏结构 + 统一页眉页脚）"""

import os

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

# ══════════════════════════════════════════════════════════
BASE_CSS = """
  :root{--white:#fff;--paper:#f1efeb;--ink:#1a1a1a;--gray-7:#666;--gray-a:#999;--line:#e5e5e5;--line-light:#ebe9e5}
  *{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
  body{background:var(--white);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue","PingFang SC",sans-serif;font-weight:400;line-height:1.7;-webkit-font-smoothing:antialiased}
  a{color:inherit;text-decoration:none}
  img{display:block;width:100%}

  /* 页眉 */
  .hd-top{padding:13px 40px 0;display:flex;justify-content:flex-end;gap:24px;font-size:12px;color:#666}
  .hd-top a:hover{color:#1a1a1a}
  .hd-brand{padding:20px 24px 26px;text-align:center}
  .hd-brand h1{font-family:'Noto Serif SC',serif;font-size:22px;font-weight:400;letter-spacing:.5em;text-indent:.5em;line-height:1;color:#1a1a1a}
  .hd-brand .en{display:block;margin-top:9px;font-size:10px;letter-spacing:.42em;text-transform:uppercase;color:#999}
  .hd-nav{border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:0 10px}
  .hd-nav ul{display:flex;justify-content:center;list-style:none}
  .hd-nav a{display:block;padding:15px 18px;font-size:13px;color:#666;white-space:nowrap;transition:color .2s}
  .hd-nav a:hover,.hd-nav a.on{color:#1a1a1a}

  /* 页脚 */
  .site-footer{background:#f1efeb;border-top:1px solid var(--line);padding:56px 0 0;margin-top:80px}
  .ft-row{display:flex;padding:0 40px 44px;max-width:1560px;margin:0 auto;overflow-x:auto}
  .ft-brand{flex:0 0 auto;padding-right:48px;margin-right:48px;border-right:1px solid #ddd9d2;min-width:200px}
  .ft-brand h4{font-family:'Noto Serif SC',serif;font-size:15px;font-weight:400;letter-spacing:.4em;text-indent:.4em;color:#1a1a1a;line-height:1;margin-bottom:10px}
  .ft-brand .en{font-size:9px;letter-spacing:.34em;text-transform:uppercase;color:#999}
  .ft-brand .slogan{margin-top:20px;font-size:11px;line-height:2;color:#888}
  .ft-col{flex:0 0 auto;padding-right:48px;min-width:110px}
  .ft-col:last-child{padding-right:0}
  .ft-col h5{font-size:10px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:#999;margin-bottom:14px}
  .ft-col a{display:block;font-size:12px;line-height:2.4;color:#555;white-space:nowrap}
  .ft-col a:hover{color:#1a1a1a}
  .ft-bottom{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:22px 40px;border-top:1px solid #ddd9d2;max-width:1560px;margin:0 auto;flex-wrap:wrap}
  .ft-bottom .cr{font-size:10px;color:#999}
  .social{display:flex;gap:9px}
  .social a{width:28px;height:28px;border:1px solid #ddd9d2;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;color:#777}
  .social a:hover{background:#1a1a1a;color:#fff;border-color:#1a1a1a}

  /* 通用 */
  .page-head{max-width:1320px;margin:0 auto;padding:72px 40px 48px}
  .page-head h1{font-size:64px;font-weight:400;letter-spacing:-.015em;line-height:1.05;margin-bottom:16px}
  .page-head p{font-size:15px;color:#666;line-height:1.8;max-width:560px}

  @media (max-width:1100px){.page-head{padding:56px 24px 36px}.page-head h1{font-size:48px}}
  @media (max-width:767px){
    .page-head{padding:40px 16px 28px}.page-head h1{font-size:34px}
    .hd-top{padding:10px 16px 0;font-size:10px}
    .hd-brand{padding:14px 16px 18px}
    .hd-brand h1{font-size:18px;letter-spacing:.4em;text-indent:.4em}
    .hd-nav{overflow-x:auto;scrollbar-width:none}
    .hd-nav ul{justify-content:flex-start}
    .hd-nav a{padding:12px 14px;font-size:11.5px}
    .ft-row{flex-wrap:wrap;padding:0 20px 32px;gap:28px}
    .ft-brand{border-right:0;padding-right:0;margin-right:0;width:100%}
    .ft-brand .slogan{display:none}
    .ft-col{padding-right:0;min-width:calc(50% - 14px)}
    .ft-bottom{padding:18px 20px;flex-direction:column;align-items:flex-start;gap:12px}
  }
"""

HEADER = """
<header>
  <div class="hd-top"><a href="#">Contact</a><a href="#">Login</a></div>
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
"""

FOOTER = """
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
"""


def build(title, desc, css, body):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<style>
{BASE_CSS}
{css}
</style>
</head>
<body>
{HEADER}
{body}
{FOOTER}
</body>
</html>'''


# ══════════════════════════════════════════════════════════
# 1. 关于
# ══════════════════════════════════════════════════════════
PAGES = {}

PAGES["about.html"] = build(
    "关于 | 跳舞兰",
    "跳舞兰是深圳的花艺团队，提供花束、花艺定制、企业订花。",
    """
  .about-wrap{max-width:820px;margin:0 auto;padding:0 40px 100px}
  .about-wrap h2{font-size:28px;font-weight:400;letter-spacing:-.01em;margin-top:64px;margin-bottom:20px}
  .about-wrap h2:first-child{margin-top:0}
  .about-wrap p{font-size:17px;line-height:2;color:#333;margin-bottom:20px}
  .about-wrap strong{font-weight:500;color:#1a1a1a}
  .about-wrap .lead{font-size:22px;line-height:1.8;color:#1a1a1a;margin-bottom:52px}
  .dl{border-top:1px solid var(--line);margin:32px 0}
  .dl .row{display:flex;justify-content:space-between;padding:16px 0;border-bottom:1px solid var(--line-light);font-size:15px}
  .dl .k{color:#666}
  .dl .v{text-align:right}
  @media (max-width:767px){.about-wrap{padding:0 16px 60px}.about-wrap p{font-size:15px}.about-wrap .lead{font-size:18px}}
    """,
    """
<div class="page-head">
  <h1>关于跳舞兰</h1>
  <p>花不只属于节日与仪式，它也可以是某个普通的下午。</p>
</div>

<div class="about-wrap">

  <p class="lead">
    跳舞兰是一家在深圳做花的团队。我们相信，
    花不只是节日与仪式的东西 —— 它也可以是某个普通的下午，
    桌角上的一小束，或者递给同事时随手的一枝。
  </p>

  <h2>我们相信什么</h2>
  <p>
    「<strong>与花共度的每一天</strong>」这句话，既是我们的名字，
    也是我们想做的事：让花重新回到生活里，像它本来该有的样子。
  </p>

  <h2>我们做什么</h2>
  <p>
    我们每天从云南直采花材，冷链到店，当日制作。
    不做隔夜花，不囤货，不为了好看而用不新鲜的花。
  </p>
  <p>
    每一束花都由花艺师手工完成。花材受季节影响，
    如果遇到个别缺货，我们会提前联系你，而不是自作主张换掉。
  </p>

  <h2>我们不做的事</h2>
  <p>
    不做过度包装。不做假花。不做「图片仅供参考」的花束。<br>
    不为了压价换掉花材而不告诉你。
  </p>

  <h2>服务范围</h2>
  <div class="dl">
    <div class="row"><span class="k">深圳同城</span><span class="v">2 小时达</span></div>
    <div class="row"><span class="k">广州</span><span class="v">次日达</span></div>
    <div class="row"><span class="k">全国 200+ 城市</span><span class="v">次日达 · 顺丰冷链</span></div>
    <div class="row"><span class="k">免运费门槛</span><span class="v">满 ¥199</span></div>
  </div>

</div>
    """
)

# ══════════════════════════════════════════════════════════
# 2. 联系
# ══════════════════════════════════════════════════════════
PAGES["contact.html"] = build(
    "联系 | 跳舞兰",
    "跳舞兰联系方式：邮箱 hello@tiaowulan.com，电话 400-000-0000，服务时间每天 9:00-21:00。",
    """
  .co2{display:grid;grid-template-columns:1fr 1fr;gap:80px;max-width:1200px;margin:0 auto;padding:0 40px 100px;align-items:start}
  .co2 h2{font-size:24px;font-weight:400;margin-bottom:24px}
  .co2 h2:not(:first-child){margin-top:52px}
  .dl .row{display:flex;justify-content:space-between;padding:16px 0;border-bottom:1px solid var(--line-light);font-size:15px}
  .dl .row:first-child{border-top:1px solid var(--line)}
  .dl .k{color:#666}
  .dl .v{text-align:right}
  .dl .v a{color:#1a1a1a;text-decoration:underline;text-underline-offset:3px}
  .cards{display:grid;gap:1px;background:var(--line);border:1px solid var(--line)}
  .card{background:#fff;padding:24px}
  .card .t{font-size:16px;margin-bottom:8px}
  .card .d{font-size:14px;line-height:1.8;color:#666}
  @media (max-width:900px){.co2{grid-template-columns:1fr;gap:48px;padding:0 16px 60px}}
    """,
    """
<div class="page-head">
  <h1>联系我们</h1>
  <p>有问题随时找我们。工作时间 2 小时内回复。</p>
</div>

<div class="co2">

  <div>
    <h2>联系方式</h2>
    <div class="dl">
      <div class="row"><span class="k">邮箱</span><span class="v"><a href="mailto:hello@tiaowulan.com">hello@tiaowulan.com</a></span></div>
      <div class="row"><span class="k">电话</span><span class="v">400-000-0000</span></div>
      <div class="row"><span class="k">微信</span><span class="v">tiaowulan</span></div>
      <div class="row"><span class="k">服务时间</span><span class="v">每天 9:00 – 21:00</span></div>
      <div class="row"><span class="k">回复时效</span><span class="v">2 小时内</span></div>
    </div>
  </div>

  <div>
    <h2>这些事可以直接找我们</h2>
    <div class="cards">
      <div class="card">
        <div class="t">订单问题</div>
        <div class="d">配送延迟、地址修改、订单取消 —— 提供订单号，2 小时内回复。</div>
      </div>
      <div class="card">
        <div class="t">花材问题</div>
        <div class="d">收到花有破损、不新鲜、与描述不符 —— 拍照发给我们，当天处理。</div>
      </div>
      <div class="card">
        <div class="t">企业订花</div>
        <div class="d">办公室周花、活动用花、节日礼品 —— 告诉我们预算和场景，出方案。</div>
      </div>
      <div class="card">
        <div class="t">定制需求</div>
        <div class="d">特殊花材、特殊包装、特殊尺寸 —— 提前 3 天联系，我们尽量满足。</div>
      </div>
    </div>
  </div>

</div>
    """
)

# ══════════════════════════════════════════════════════════
# 3. 帮助三页共用模板
# ══════════════════════════════════════════════════════════
HELP_CSS = """
  .help-wrap{display:grid;grid-template-columns:200px 1fr;gap:80px;max-width:1100px;margin:0 auto;padding:0 40px 100px;align-items:start}
  .help-nav{position:sticky;top:40px;border-left:2px solid var(--line);padding-left:20px}
  .help-nav a{display:block;font-size:14px;color:#999;padding:8px 0;line-height:1.6}
  .help-nav a:hover{color:#666}
  .help-nav a.on{color:#1a1a1a;font-weight:500}
  .help-body h2{font-size:24px;font-weight:400;margin-top:52px;margin-bottom:18px}
  .help-body h2:first-child{margin-top:0}
  .help-body p{font-size:15px;line-height:1.95;color:#333;margin-bottom:16px}
  .help-body strong{font-weight:500;color:#1a1a1a}
  .dl .row{display:flex;justify-content:space-between;padding:14px 0;border-bottom:1px solid var(--line-light);font-size:15px}
  .dl .row:first-child{border-top:1px solid var(--line)}
  .dl .k{color:#666}
  .dl .v{text-align:right}
  .cards{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line);border:1px solid var(--line);margin:20px 0}
  .card{background:#fff;padding:22px}
  .card .t{font-size:15px;margin-bottom:6px}
  .card .d{font-size:13px;line-height:1.8;color:#666}
  @media (max-width:900px){
    .help-wrap{grid-template-columns:1fr;gap:32px;padding:0 16px 60px}
    .help-nav{position:static;border-left:0;border-bottom:1px solid var(--line);padding:0 0 16px;display:flex;gap:20px;overflow-x:auto}
    .help-nav a{padding:0;white-space:nowrap}
    .cards{grid-template-columns:1fr}
  }
"""

HELP_NAV = """
    <nav class="help-nav">
      <a href="help-delivery.html" {d}>配送范围</a>
      <a href="help-returns.html" {r}>售后政策</a>
      <a href="help-faq.html" {f}>常见问题</a>
    </nav>
"""

PAGES["help-delivery.html"] = build(
    "配送范围 | 跳舞兰",
    "跳舞兰配送范围：深圳同城 2 小时达，广州次日达，全国 200+ 城市顺丰冷链。满 199 免运费。",
    HELP_CSS,
    """
<div class="page-head">
  <h1>配送范围</h1>
  <p>送哪儿、多久到、多少钱。</p>
</div>

<div class="help-wrap">
""" + HELP_NAV.format(d='class="on"', r="", f="") + """
    <div class="help-body">

      <h2>配送时效</h2>
      <div class="dl">
        <div class="row"><span class="k">深圳同城</span><span class="v">2 小时达</span></div>
        <div class="row"><span class="k">广州</span><span class="v">次日达</span></div>
        <div class="row"><span class="k">全国 200+ 城市</span><span class="v">次日达 · 顺丰冷链</span></div>
        <div class="row"><span class="k">偏远地区</span><span class="v">2–3 天</span></div>
      </div>

      <h2>下单截止时间</h2>
      <div class="dl">
        <div class="row"><span class="k">深圳当日达</span><span class="v">当天 16:00 前下单</span></div>
        <div class="row"><span class="k">深圳次日达</span><span class="v">当天 21:00 前下单</span></div>
        <div class="row"><span class="k">其他城市</span><span class="v">提前 1 天下单</span></div>
      </div>

      <h2>配送费</h2>
      <div class="dl">
        <div class="row"><span class="k">满 ¥199</span><span class="v">免运费</span></div>
        <div class="row"><span class="k">不满 ¥199</span><span class="v">¥15</span></div>
        <div class="row"><span class="k">偏远地区</span><span class="v">¥25 起</span></div>
      </div>

      <h2>可选时段</h2>
      <p>
        深圳同城可选两个时段：<strong>14:00–16:00</strong> 和 <strong>18:00–20:00</strong>。<br>
        其他城市为全天配送（9:00–18:00），无法指定具体时段。
      </p>

      <h2>配送不到的情况</h2>
      <p>
        如果地址超出配送范围，下单时系统会提示。
        如果已经下单但发现送不到，我们会联系你改地址或退款，不收取任何费用。
      </p>

      <h2>签收</h2>
      <p>
        鲜花需要本人或指定收花人签收。如果收花人不在，配送员会电话联系。
        连续 3 次联系不上，订单会退回并安排二次配送（需补配送费）。
      </p>

    </div>
</div>
    """
)

PAGES["help-returns.html"] = build(
    "售后政策 | 跳舞兰",
    "跳舞兰售后政策：花材破损、不新鲜、与描述不符，当天处理。支持补送、退款、部分退款。",
    HELP_CSS,
    """
<div class="page-head">
  <h1>售后政策</h1>
  <p>花有问题，我们负责到底。</p>
</div>

<div class="help-wrap">
""" + HELP_NAV.format(d="", r='class="on"', f="") + """
    <div class="help-body">

      <h2>什么情况可以申请售后</h2>
      <div class="cards">
        <div class="card"><div class="t">花材破损</div><div class="d">运输过程中压坏、折断 —— 拍照发我们，当天补送或退款。</div></div>
        <div class="card"><div class="t">花材不新鲜</div><div class="d">收到时已经蔫了、发黄、有异味 —— 全额退款。</div></div>
        <div class="card"><div class="t">与描述不符</div><div class="d">花材、数量、包装与页面描述明显不符 —— 部分退款或补送。</div></div>
        <div class="card"><div class="t">配送延迟</div><div class="d">超出承诺时段 2 小时以上 —— 补偿配送费或部分退款。</div></div>
      </div>

      <h2>怎么申请</h2>
      <p>
        <strong>1.</strong> 在「我的订单」找到这笔订单<br>
        <strong>2.</strong> 点「申请售后」，选择问题类型<br>
        <strong>3.</strong> 上传照片（重要，没有照片无法处理）<br>
        <strong>4.</strong> 提交后会生成工单号，客服 2 小时内联系你
      </p>
      <p>
        <strong>注意：</strong>游客下单无法在线申请售后，需通过邮箱或电话联系客服，并提供订单号。
      </p>

      <h2>处理时效</h2>
      <div class="dl">
        <div class="row"><span class="k">客服响应</span><span class="v">2 小时内</span></div>
        <div class="row"><span class="k">补送</span><span class="v">当天或次日</span></div>
        <div class="row"><span class="k">退款到账</span><span class="v">1–3 个工作日</span></div>
      </div>

      <h2>什么情况不能退</h2>
      <p>
        · 已经送达超过 <strong>24 小时</strong>才提出的（鲜花有保鲜期，无法判断责任）<br>
        · 没有照片，无法核实问题的<br>
        · 因收花人自身原因（拒收、地址错误、长时间联系不上）导致的损耗<br>
        · 定制花束中已明确告知的花材替换
      </p>

    </div>
</div>
    """
)

PAGES["help-faq.html"] = build(
    "常见问题 | 跳舞兰",
    "跳舞兰常见问题：送花时间、花材新鲜度、能否指定时间、游客下单、发票、修改地址等。",
    HELP_CSS,
    """
<div class="page-head">
  <h1>常见问题</h1>
  <p>你可能想问的。</p>
</div>

<div class="help-wrap">
""" + HELP_NAV.format(d="", r="", f='class="on"') + """
    <div class="help-body">

      <h2>下单相关</h2>
      <div class="dl">
        <div class="row"><span class="k">最早能什么时候送到？</span><span class="v">深圳 2 小时，其他城市次日</span></div>
        <div class="row"><span class="k">能指定送达时间吗？</span><span class="v">深圳可选时段，其他城市不能</span></div>
        <div class="row"><span class="k">可以匿名送花吗？</span><span class="v">可以，下单时勾选</span></div>
        <div class="row"><span class="k">贺卡可以写多少字？</span><span class="v">建议 30 字以内</span></div>
      </div>

      <h2>花材相关</h2>
      <div class="dl">
        <div class="row"><span class="k">花是新鲜的吗？</span><span class="v">当日到店，当日制作</span></div>
        <div class="row"><span class="k">能养几天？</span><span class="v">含保鲜剂 5–7 天</span></div>
        <div class="row"><span class="k">缺货会怎么办？</span><span class="v">提前联系你确认替换</span></div>
        <div class="row"><span class="k">可以只要某种花吗？</span><span class="v">可以，联系客服定制</span></div>
      </div>

      <h2>支付相关</h2>
      <div class="dl">
        <div class="row"><span class="k">支持哪些支付方式？</span><span class="v">微信 / 支付宝 / 银行卡</span></div>
        <div class="row"><span class="k">可以开发票吗？</span><span class="v">可以，联系客服</span></div>
        <div class="row"><span class="k">订单多久失效？</span><span class="v">30 分钟未支付自动取消</span></div>
      </div>

      <h2>账号相关</h2>
      <div class="dl">
        <div class="row"><span class="k">必须登录才能买吗？</span><span class="v">不用，游客也能下单</span></div>
        <div class="row"><span class="k">游客下单有什么限制？</span><span class="v">只能当前浏览器查单</span></div>
        <div class="row"><span class="k">游客订单能找回吗？</span><span class="v">登录同手机号可自动认领</span></div>
      </div>

      <h2>售后相关</h2>
      <div class="dl">
        <div class="row"><span class="k">花有问题怎么办？</span><span class="v">拍照，24 小时内申请</span></div>
        <div class="row"><span class="k">多久能处理完？</span><span class="v">客服 2 小时内响应</span></div>
        <div class="row"><span class="k">能退款吗？</span><span class="v">质量问题全额退，原路退回</span></div>
      </div>

      <h2>还没解决？</h2>
      <p>
        发邮件到 <strong>hello@tiaowulan.com</strong>，或工作时间打电话 400-000-0000。
        提供订单号，我们 2 小时内回复。
      </p>

    </div>
</div>
    """
)

# ══════════════════════════════════════════════════════════
# 4. 登录
# ══════════════════════════════════════════════════════════
PAGES["login.html"] = build(
    "登录 | 跳舞兰",
    "登录跳舞兰查看订单、保存地址。",
    """
  .login-wrap{max-width:420px;margin:0 auto;padding:100px 40px 120px}
  .login-wrap h1{font-size:40px;font-weight:400;letter-spacing:-.015em;margin-bottom:12px;text-align:center}
  .login-wrap .sub{font-size:14px;color:#999;text-align:center;margin-bottom:52px;line-height:1.9}
  .fld{border-bottom:1px solid var(--line);padding:6px 0 14px;margin-bottom:28px}
  .fld label{display:block;font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:#999;margin-bottom:8px}
  .fld input{width:100%;border:0;background:none;font-size:16px;color:#1a1a1a;outline:none;font-family:inherit}
  .fld input::placeholder{color:#ccc}
  .code-row{display:flex;gap:16px;align-items:flex-end}
  .code-row .fld{flex:1}
  .code-btn{flex:0 0 auto;padding:12px 0 14px;font-size:13px;color:#666;border-bottom:1px solid var(--line);background:none;border-top:0;border-left:0;border-right:0;cursor:pointer;font-family:inherit;white-space:nowrap}
  .login-btn{width:100%;padding:17px;background:#1a1a1a;color:#fff;border:0;border-radius:4px;font-size:15px;letter-spacing:.06em;cursor:pointer;font-family:inherit;margin-top:12px}
  .login-btn:hover{opacity:.88}
  .terms{margin-top:28px;font-size:11px;color:#999;text-align:center;line-height:1.9}
  .terms a{color:#666;text-decoration:underline;text-underline-offset:3px}
  .skip{display:block;text-align:center;margin-top:36px;font-size:13px;color:#999;text-decoration:underline;text-underline-offset:3px}
  .skip:hover{color:#1a1a1a}
  @media (max-width:767px){.login-wrap{padding:60px 16px 80px}.login-wrap h1{font-size:30px}}
    """,
    """
<div class="login-wrap">
  <h1>登录</h1>
  <div class="sub">登录后可查看订单、保存地址<br>未注册的手机号将自动创建账号</div>

  <div class="fld">
    <label>手机号</label>
    <input type="tel" placeholder="请输入手机号" inputmode="numeric" maxlength="11">
  </div>

  <div class="code-row">
    <div class="fld">
      <label>验证码</label>
      <input type="text" placeholder="6 位数字" inputmode="numeric" maxlength="6">
    </div>
    <button class="code-btn">获取验证码</button>
  </div>

  <button class="login-btn">登 录</button>

  <div class="terms">
    登录即表示同意<br>
    <a href="#">《用户协议》</a> 与 <a href="#">《隐私政策》</a>
  </div>

  <a href="checkout.html" class="skip">不想登录，继续以游客下单</a>
</div>
    """
)

# ══════════════════════════════════════════════════════════
# 5. 我的订单
# ══════════════════════════════════════════════════════════
PAGES["orders.html"] = build(
    "我的订单 | 跳舞兰",
    "查看跳舞兰历史订单。",
    """
  .ord-wrap{max-width:1320px;margin:0 auto;padding:0 40px 100px}
  .tabs{display:flex;gap:28px;padding:0 0 24px;border-bottom:1px solid var(--line);margin-bottom:8px}
  .tabs a{font-size:14px;color:#999;transition:color .2s}
  .tabs a:hover{color:#666}
  .tabs a.on{color:#1a1a1a}
  .order{
    display:grid;
    grid-template-columns:180px 90px 1fr 200px 120px 80px;
    gap:24px;align-items:center;
    padding:24px 0;border-bottom:1px solid var(--line-light);
    transition:background .15s;
  }
  .order:hover{background:var(--paper-light)}
  .order .no{font-family:monospace;font-size:12px;color:#999}
  .order .pic{width:90px;height:110px;background:#e8e6e2;overflow:hidden}
  .order .pic img{width:100%;height:100%;object-fit:cover}
  .order .name{font-size:16px;margin-bottom:4px}
  .order .spec{font-size:13px;color:#999;line-height:1.6}
  .order .meta{font-size:13px;color:#666;line-height:1.8}
  .order .price{font-size:18px;text-align:right}
  .order .go{font-size:13px;color:#666;text-decoration:underline;text-underline-offset:3px;text-align:right}
  .order .go:hover{color:#1a1a1a}
  .pill{display:inline-block;padding:3px 10px;font-size:11px;border:1px solid var(--line);color:#666;white-space:nowrap}
  .pill.wait{border-color:#ddc9a0;color:#8a6420;background:#fdf8ee}
  .pill.doing{border-color:#a8c0d8;color:#345f80;background:#f0f6fa}
  .pill.done{border-color:#b5cbb9;color:#3d6b47;background:#f0f7f1}
  .pill.cancel{color:#999;background:var(--paper-light)}
  @media (max-width:1100px){
    .order{grid-template-columns:140px 70px 1fr 140px 100px;gap:16px}
    .order .go{display:none}
  }
  @media (max-width:767px){
    .ord-wrap{padding:0 16px 60px}
    .order{grid-template-columns:70px 1fr;gap:16px;padding:20px 0}
    .order .no,.order .meta,.order .price{display:none}
    .order .pic{width:70px;height:88px}
    .order .name{font-size:14px}
    .order .spec{font-size:12px}
    .tabs{gap:20px;font-size:12px}
  }
    """,
    """
<div class="page-head">
  <h1>我的订单</h1>
  <p>李女士 · 138****6688</p>
</div>

<div class="ord-wrap">

  <div class="tabs">
    <a href="#" class="on">全部</a>
    <a href="#">待支付</a>
    <a href="#">配花中</a>
    <a href="#">配送中</a>
    <a href="#">已完成</a>
  </div>

  <a href="order-detail.html" class="order">
    <div class="no">TWL20261020144237</div>
    <div class="pic"><img src="__IMG_P4__" alt="木星"></div>
    <div>
      <div class="name">木星</div>
      <div class="spec">向日葵 6 枝 · 尤加利叶 ×1</div>
    </div>
    <div class="meta">今天 18:00–20:00<br>深圳市南山区</div>
    <div class="price">¥219</div>
    <div class="go">详情 →</div>
  </a>

  <a href="order-detail.html" class="order">
    <div class="no">TWL20261020135005</div>
    <div class="pic"><img src="__IMG_P1__" alt="晨光序曲"></div>
    <div>
      <div class="name">晨光序曲</div>
      <div class="spec">香槟玫瑰 20 枝 · 满天星 ×1</div>
    </div>
    <div class="meta">今天 14:00–16:00<br>深圳市福田区</div>
    <div class="price">¥299</div>
    <div class="go">详情 →</div>
  </a>

  <a href="order-detail.html" class="order">
    <div class="no">TWL20261020124518</div>
    <div class="pic"><img src="__IMG_P5__" alt="雪落"></div>
    <div>
      <div class="name">雪落</div>
      <div class="spec">白玫瑰 33 枝 · 银叶菊 ×1</div>
    </div>
    <div class="meta">明天 09:00–11:00<br>深圳市罗湖区</div>
    <div class="price">¥499</div>
    <div class="go">详情 →</div>
  </a>

  <a href="order-detail.html" class="order">
    <div class="no">TWL20261018190512</div>
    <div class="pic"><img src="__IMG_P2__" alt="小满"></div>
    <div>
      <div class="name">小满</div>
      <div class="spec">白郁金香 12 枝 ×1</div>
    </div>
    <div class="meta">10月18日 · 已签收</div>
    <div class="price">¥259</div>
    <div class="go">详情 →</div>
  </a>

  <a href="order-detail.html" class="order">
    <div class="no">TWL20261015102033</div>
    <div class="pic"><img src="__IMG_P4__" alt="木星"></div>
    <div>
      <div class="name">木星</div>
      <div class="spec">向日葵 6 枝 ×1</div>
    </div>
    <div class="meta">10月15日 · 已签收</div>
    <div class="price">¥219</div>
    <div class="go">详情 →</div>
  </a>

</div>
    """
)

# ══════════════════════════════════════════════════════════
# 6. 订单详情
# ══════════════════════════════════════════════════════════
PAGES["order-detail.html"] = build(
    "订单详情 | 跳舞兰",
    "查看订单状态与配送进度。",
    """
  .od-wrap{display:grid;grid-template-columns:1fr 380px;gap:80px;max-width:1200px;margin:0 auto;padding:64px 40px 100px;align-items:start}
  .od-left h1{font-size:40px;font-weight:400;letter-spacing:-.015em;margin-bottom:10px}
  .od-left .no{font-size:13px;color:#999;font-family:monospace;margin-bottom:44px}
  .timeline-title{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#999;margin-bottom:20px}
  .step{display:flex;gap:20px;padding-bottom:28px;position:relative}
  .step:last-child{padding-bottom:0}
  .step::before{content:"";position:absolute;left:8px;top:20px;bottom:0;width:1px;background:var(--line)}
  .step:last-child::before{display:none}
  .step .dot{width:17px;height:17px;flex:0 0 17px;border-radius:50%;border:1px solid var(--line);background:#fff;position:relative;z-index:1;margin-top:2px}
  .step.done .dot{background:#1a1a1a;border-color:#1a1a1a}
  .step.now .dot{border-color:#1a1a1a;box-shadow:inset 0 0 0 4px #fff,inset 0 0 0 10px #1a1a1a}
  .step .txt .t{font-size:15px;margin-bottom:3px}
  .step:not(.done):not(.now) .txt .t{color:#bbb}
  .step .txt .d{font-size:12px;color:#999;line-height:1.8}
  .od-right{position:sticky;top:40px}
  .box{border:1px solid var(--line);padding:28px;margin-bottom:20px}
  .box h2{font-size:14px;font-weight:400;letter-spacing:.06em;padding-bottom:16px;border-bottom:1px solid var(--line);margin-bottom:18px}
  .item{display:flex;gap:16px;padding-bottom:20px;border-bottom:1px solid var(--line-light);margin-bottom:20px}
  .item .pic{width:64px;height:80px;flex:0 0 64px;background:#e8e6e2;overflow:hidden}
  .item .pic img{width:100%;height:100%;object-fit:cover}
  .item .t{flex:1}
  .item .t h3{font-size:15px;font-weight:400;margin-bottom:3px}
  .item .t .s{font-size:12px;color:#999}
  .drow{display:flex;justify-content:space-between;gap:16px;padding:9px 0;font-size:13px}
  .drow .k{color:#666;flex:0 0 72px}
  .drow .v{text-align:right;line-height:1.7}
  .drow .v.price{font-size:20px}
  .actions{display:flex;flex-direction:column;gap:10px;margin-top:20px}
  .actions a{padding:14px;text-align:center;font-size:14px;border-radius:4px}
  .actions .primary{background:#1a1a1a;color:#fff}
  .actions .ghost{border:1px solid var(--line);color:#1a1a1a}
  @media (max-width:1024px){.od-wrap{grid-template-columns:1fr 340px;gap:48px;padding:48px 24px 80px}}
  @media (max-width:860px){
    .od-wrap{grid-template-columns:1fr;gap:0;padding:0 0 60px}
    .od-left{padding:40px 16px 0}
    .od-right{position:static;padding:0 16px}
    .od-left h1{font-size:30px}
  }
    """,
    """
<div class="od-wrap">

  <div class="od-left">
    <h1>配花中</h1>
    <div class="no">TWL20261020144237C2EB</div>

    <div class="timeline-title">订单进度</div>

    <div class="step done"><div class="dot"></div><div class="txt"><div class="t">已支付</div><div class="d">10 月 20 日 14:42</div></div></div>
    <div class="step now"><div class="dot"></div><div class="txt"><div class="t">配花中</div><div class="d">已推送至花艺师 · 10 月 20 日 14:42</div></div></div>
    <div class="step"><div class="dot"></div><div class="txt"><div class="t">配送中</div><div class="d">预计 18:00 – 20:00</div></div></div>
    <div class="step"><div class="dot"></div><div class="txt"><div class="t">已送达</div><div class="d">—</div></div></div>
    <div class="step"><div class="dot"></div><div class="txt"><div class="t">已完成</div><div class="d">—</div></div></div>
  </div>

  <div class="od-right">

    <div class="box">
      <h2>商品</h2>
      <div class="item">
        <div class="pic"><img src="__IMG_P1__" alt="晨光序曲"></div>
        <div class="t">
          <h3>晨光序曲</h3>
          <div class="s">香槟玫瑰 20 枝 ×1</div>
        </div>
      </div>
      <div class="drow"><span class="k">收花人</span><span class="v">李女士 138****6688</span></div>
      <div class="drow"><span class="k">地址</span><span class="v">深圳市南山区科技园南路 18 号 1203</span></div>
      <div class="drow"><span class="k">送达</span><span class="v">今天 18:00 – 20:00</span></div>
      <div class="drow"><span class="k">贺卡</span><span class="v">生日快乐，妈妈</span></div>
      <div class="drow"><span class="k">实付</span><span class="v price">¥299</span></div>

      <div class="actions">
        <a href="after-sale.html" class="ghost">申请售后</a>
        <a href="contact.html" class="primary">联系客服</a>
      </div>
    </div>

  </div>

</div>
    """
)

# ══════════════════════════════════════════════════════════
# 7. 地址簿
# ══════════════════════════════════════════════════════════
PAGES["address.html"] = build(
    "地址簿 | 跳舞兰",
    "保存常用地址，下次下单不用重填。",
    """
  .addr-wrap{max-width:1200px;margin:0 auto;padding:0 40px 100px}
  .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-bottom:32px}
  .card{border:1px solid var(--line);padding:28px;position:relative}
  .card .top{display:flex;align-items:center;gap:10px;margin-bottom:14px}
  .card .name{font-size:17px}
  .card .phone{font-size:13px;color:#999;font-family:monospace}
  .card .def{font-size:10px;padding:2px 8px;background:#1a1a1a;color:#fff}
  .card .tag{font-size:10px;padding:2px 8px;border:1px solid var(--line);color:#666}
  .card .detail{font-size:14px;line-height:1.8;color:#666;margin-bottom:20px;min-height:52px}
  .card .ops{display:flex;gap:20px;border-top:1px solid var(--line-light);padding-top:16px}
  .card .ops a{font-size:13px;color:#666;text-decoration:underline;text-underline-offset:3px}
  .card .ops a:hover{color:#1a1a1a}
  .add-new{
    border:1px dashed var(--line);
    display:flex;align-items:center;justify-content:center;
    min-height:220px;font-size:14px;color:#999;cursor:pointer;
    transition:all .2s;
  }
  .add-new:hover{border-color:#1a1a1a;color:#1a1a1a}
  @media (max-width:1100px){.grid{grid-template-columns:repeat(2,1fr)}}
  @media (max-width:767px){.addr-wrap{padding:0 16px 60px}.grid{grid-template-columns:1fr;gap:16px}}
    """,
    """
<div class="page-head">
  <h1>地址簿</h1>
  <p>保存常用地址，下次下单不用重填。</p>
</div>

<div class="addr-wrap">
  <div class="grid">

    <div class="card">
      <div class="top">
        <span class="name">李女士</span>
        <span class="phone">138****6688</span>
        <span class="def">默认</span>
        <span class="tag">家</span>
      </div>
      <div class="detail">深圳市南山区科技园南路 18 号 1203</div>
      <div class="ops"><a href="#">编辑</a><a href="#">删除</a></div>
    </div>

    <div class="card">
      <div class="top">
        <span class="name">王先生</span>
        <span class="phone">139****1234</span>
        <span class="tag">公司</span>
      </div>
      <div class="detail">深圳市福田区深南大道 6008 号 A 座 25 楼</div>
      <div class="ops"><a href="#">编辑</a><a href="#">删除</a></div>
    </div>

    <div class="card">
      <div class="top">
        <span class="name">陈小姐</span>
        <span class="phone">137****5566</span>
      </div>
      <div class="detail">深圳市罗湖区东门中路 1022 号 5 楼</div>
      <div class="ops"><a href="#">编辑</a><a href="#">删除</a></div>
    </div>

    <div class="add-new">＋ 新增地址</div>

  </div>
</div>
    """
)

# ══════════════════════════════════════════════════════════
# 8. 申请售后
# ══════════════════════════════════════════════════════════
PAGES["after-sale.html"] = build(
    "申请售后 | 跳舞兰",
    "花有问题，我们负责到底。",
    """
  .as-wrap{display:grid;grid-template-columns:1fr 380px;gap:80px;max-width:1200px;margin:0 auto;padding:64px 40px 100px;align-items:start}
  .as-left h1{font-size:40px;font-weight:400;margin-bottom:44px}
  .sec{margin-bottom:36px}
  .sec .lbl{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#999;margin-bottom:14px}
  .types{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  .type{padding:14px;border:1px solid var(--line);text-align:center;font-size:14px;color:#666;cursor:pointer;transition:all .15s;border-radius:4px}
  .type:hover{border-color:#999}
  .type.on{border-color:#1a1a1a;color:#1a1a1a;background:var(--paper)}
  textarea{width:100%;min-height:120px;padding:16px;border:1px solid var(--line);border-radius:4px;font:inherit;font-size:15px;line-height:1.8;color:#1a1a1a;outline:none;resize:vertical}
  textarea::placeholder{color:#ccc}
  .upload{display:flex;gap:12px}
  .up-thumb{width:96px;height:96px;background:#e8e6e2;overflow:hidden;position:relative;border-radius:4px}
  .up-thumb img{width:100%;height:100%;object-fit:cover}
  .up-thumb .x{position:absolute;top:4px;right:4px;width:20px;height:20px;background:rgba(20,20,20,.7);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px}
  .up-box{width:96px;height:96px;border:1px dashed var(--line);border-radius:4px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;color:#999;cursor:pointer;font-size:12px}
  .up-box:hover{border-color:#1a1a1a;color:#1a1a1a}
  .phone-row{display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-top:1px solid var(--line-light)}
  .phone-row .k{font-size:15px;color:#666}
  .phone-row input{border:0;background:none;font:inherit;font-size:15px;text-align:right;outline:none}
  .as-right{position:sticky;top:40px}
  .box{border:1px solid var(--line);padding:28px}
  .box h2{font-size:14px;font-weight:400;padding-bottom:16px;border-bottom:1px solid var(--line);margin-bottom:18px}
  .item{display:flex;gap:16px;padding-bottom:18px;border-bottom:1px solid var(--line-light);margin-bottom:18px}
  .item .pic{width:64px;height:80px;flex:0 0 64px;background:#e8e6e2;overflow:hidden}
  .item .pic img{width:100%;height:100%;object-fit:cover}
  .item .t h3{font-size:15px;font-weight:400;margin-bottom:3px}
  .item .t .s{font-size:12px;color:#999;line-height:1.6}
  .submit{display:block;width:100%;margin-top:24px;padding:17px;background:#1a1a1a;color:#fff;border:0;border-radius:4px;font-size:15px;cursor:pointer;font-family:inherit;text-align:center}
  .submit:hover{opacity:.88}
  .notice{margin-top:20px;font-size:12px;color:#999;line-height:1.9}
  @media (max-width:1024px){.as-wrap{grid-template-columns:1fr 340px;gap:48px;padding:48px 24px 80px}}
  @media (max-width:860px){
    .as-wrap{grid-template-columns:1fr;gap:0;padding:0 0 60px}
    .as-left{padding:40px 16px 0}
    .as-right{position:static;padding:0 16px}
    .types{grid-template-columns:repeat(2,1fr)}
    .as-left h1{font-size:30px}
  }
    """,
    """
<div class="as-wrap">

  <div class="as-left">
    <h1>申请售后</h1>

    <div class="sec">
      <div class="lbl">问题类型</div>
      <div class="types">
        <div class="type">花材破损</div>
        <div class="type on">花材不新鲜</div>
        <div class="type">与描述不符</div>
        <div class="type">配送延迟</div>
        <div class="type">送错地址</div>
        <div class="type">其他问题</div>
      </div>
    </div>

    <div class="sec">
      <div class="lbl">问题描述</div>
      <textarea placeholder="说清楚具体问题，比如：收到时有几枝玫瑰已经蔫了，花瓣发黄"></textarea>
    </div>

    <div class="sec">
      <div class="lbl">上传图片（最多 3 张）</div>
      <div class="upload">
        <div class="up-thumb">
          <img src="__IMG_P1__" alt="问题照片">
          <div class="x">×</div>
        </div>
        <div class="up-box"><span style="font-size:20px">＋</span><span>添加</span></div>
      </div>
    </div>

    <div class="sec">
      <div class="lbl">联系方式</div>
      <div class="phone-row">
        <span class="k">手机号</span>
        <input placeholder="138****6688" inputmode="tel">
      </div>
    </div>
  </div>

  <div class="as-right">
    <div class="box">
      <h2>关联订单</h2>
      <div class="item">
        <div class="pic"><img src="__IMG_P1__" alt="晨光序曲"></div>
        <div class="t">
          <h3>晨光序曲 ×1</h3>
          <div class="s">TWL20261020144237C2EB<br>10 月 20 日 已送达</div>
        </div>
      </div>

      <button class="submit">提交申请</button>

      <div class="notice">
        客服 2 小时内联系你。<br>
        质量问题全额退款，1–3 个工作日原路退回。<br>
        送达超过 24 小时提出的申请，需要额外核实。
      </div>
    </div>
  </div>

</div>
    """
)

# ══════════════════════════════════════════════════════════
# 9. 搜索
# ══════════════════════════════════════════════════════════
PAGES["search.html"] = build(
    "搜索 | 跳舞兰",
    "搜索花名、花材、场景。",
    """
  .search-wrap{max-width:1320px;margin:0 auto;padding:64px 40px 100px}
  .search-box{display:flex;align-items:center;gap:16px;border-bottom:1px solid #1a1a1a;padding-bottom:16px;margin-bottom:32px}
  .search-box input{flex:1;border:0;background:none;font-size:28px;color:#1a1a1a;outline:none;font-family:inherit;font-weight:300}
  .search-box input::placeholder{color:#ccc}
  .search-box .icon{font-size:20px;color:#999}
  .hot{margin-bottom:48px}
  .hot .lbl{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#999;margin-bottom:16px}
  .tags{display:flex;flex-wrap:wrap;gap:10px}
  .tags a{padding:9px 18px;border:1px solid var(--line);border-radius:100px;font-size:13px;color:#666;transition:all .15s}
  .tags a:hover{border-color:#1a1a1a;color:#1a1a1a}
  .result-head{display:flex;justify-content:space-between;align-items:baseline;padding-bottom:20px;border-bottom:1px solid var(--line);margin-bottom:24px}
  .result-head h2{font-size:20px;font-weight:400}
  .result-head .n{font-size:14px;color:#999}
  .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:24px}
  .card{display:block}
  .card .pic{background:#e8e6e2;overflow:hidden}
  .card .pic img{width:100%;aspect-ratio:1/1;object-fit:cover;transition:transform .8s}
  .card:hover .pic img{transform:scale(1.02)}
  .card .info{background:var(--paper);padding:22px 20px 26px;min-height:110px}
  .card .info h3{font-size:16px;font-weight:400;margin-bottom:6px}
  .card .info .p{font-size:14px}
  @media (max-width:1100px){.grid{grid-template-columns:repeat(3,1fr);gap:16px}.search-wrap{padding:48px 24px 80px}.search-box input{font-size:22px}}
  @media (max-width:767px){
    .search-wrap{padding:40px 16px 60px}
    .grid{grid-template-columns:repeat(2,1fr);gap:12px}
    .search-box input{font-size:18px}
    .card .info{padding:14px 12px 18px;min-height:90px}
    .card .info h3{font-size:13px}
    .card .info .p{font-size:12px}
  }
    """,
    """
<div class="search-wrap">

  <div class="search-box">
    <span class="icon">⌕</span>
    <input placeholder="搜花名、花材、场景" value="玫瑰">
  </div>

  <div class="hot">
    <div class="lbl">热门搜索</div>
    <div class="tags">
      <a href="#">香槟玫瑰</a>
      <a href="#">向日葵</a>
      <a href="#">送妈妈</a>
      <a href="#">告白</a>
      <a href="#">生日</a>
      <a href="#">白玫瑰</a>
      <a href="#">郁金香</a>
      <a href="#">探望</a>
    </div>
  </div>

  <div class="result-head">
    <h2>「玫瑰」的搜索结果</h2>
    <span class="n">3 件</span>
  </div>

  <div class="grid">
    <a href="product.html" class="card">
      <div class="pic"><img src="__IMG_P1__" alt="晨光序曲"></div>
      <div class="info"><h3>晨光序曲</h3><div class="p">¥299 – ¥459</div></div>
    </a>
    <a href="product.html" class="card">
      <div class="pic"><img src="__IMG_P5__" alt="雪落"></div>
      <div class="info"><h3>雪落</h3><div class="p">¥499 – ¥699</div></div>
    </a>
    <a href="product.html" class="card">
      <div class="pic"><img src="__IMG_P0__" alt="微风"></div>
      <div class="info"><h3>微风</h3><div class="p">¥289</div></div>
    </a>
  </div>

</div>
    """
)

# ══════════════════════════════════════════════════════════
# 写文件
# ══════════════════════════════════════════════════════════
for fn, html in PAGES.items():
    path = os.path.join(PROTO, fn)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  {fn}: {len(html)} 字符")

print(f"\n生成 {len(PAGES)} 个页面")
