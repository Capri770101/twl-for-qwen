# -*- coding: utf-8 -*-
"""批量生成 luxe 的简单页面（关于/联系/帮助三页）"""
import os

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{title} | 跳舞兰</title>
<meta name="description" content="{desc}">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;500&family=Cormorant+Garamond:wght@300;400;500&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="base.css">
<style>
  .body-sec{{padding:44px 24px;border-bottom:1px solid var(--gray-e)}}
  .body-sec h3{{
    font-family:'Noto Serif SC',serif;font-size:16px;font-weight:400;
    letter-spacing:.08em;margin-bottom:14px;margin-top:32px;
    padding-left:12px;border-left:2px solid var(--green);
  }}
  .body-sec h3:first-child{{margin-top:0}}
  .body-sec p{{font-size:13px;line-height:2.3;color:#3a3733;margin-bottom:14px}}
  .body-sec p:last-child{{margin-bottom:0}}
  .body-sec strong{{font-weight:500;color:var(--ink)}}

  .dl{{margin:0 0 22px}}
  .dl .row{{
    display:flex;justify-content:space-between;gap:16px;
    padding:13px 0;border-bottom:1px solid var(--gray-e);font-size:12.5px;
  }}
  .dl .row:last-child{{border-bottom:0}}
  .dl .k{{color:var(--gray-7);white-space:nowrap}}
  .dl .v{{text-align:right;line-height:1.9}}
  .dl .v a{{color:var(--green)}}
  .dl .v.hl{{color:var(--green);font-family:'Cormorant Garamond',serif;font-size:16px}}

  .cards{{display:grid;gap:1px;background:var(--gray-d);border:1px solid var(--gray-d)}}
  .card{{background:#fff;padding:20px}}
  .card .t{{font-size:13px;margin-bottom:6px;color:var(--ink)}}
  .card .d{{font-size:11.5px;line-height:2;color:var(--gray-7)}}

  .cta{{padding:40px 24px 56px;text-align:center}}
  .cta a{{
    display:inline-block;padding:14px 40px;
    background:var(--green);color:#fff;
    font-size:12px;letter-spacing:.12em;
  }}
</style>
</head>
<body>

<div class="topbar">
  <a href="index.html">← 返回</a>
  <div class="r"><a href="shop.html">买花</a></div>
</div>

<div class="brand">
  <a href="index.html"><h1>跳舞兰</h1><span class="en">Tiao Wu Lan</span></a>
</div>

<div class="page-head">
  <div class="kicker">{kicker}</div>
  <h2>{title}</h2>
  <p>{subtitle}</p>
</div>

<div class="body-sec">
{content}
</div>

{cta}

<footer>
  <div class="foot-row">
    <div class="foot-brand">
      <h4>跳舞兰</h4>
      <div class="en">Tiao Wu Lan</div>
      <div class="slogan">Living With<br>Flowers Every Day</div>
    </div>
    <div class="foot-col">
      <h5>Shop</h5>
      <a href="shop.html">全部花束</a>
      <a href="#">日常</a>
      <a href="#">告白</a>
      <a href="#">生日</a>
    </div>
    <div class="foot-col">
      <h5>Help</h5>
      <a href="help-delivery.html">配送范围</a>
      <a href="help-returns.html">售后政策</a>
      <a href="help-faq.html">常见问题</a>
    </div>
    <div class="foot-col">
      <h5>About</h5>
      <a href="about.html">品牌故事</a>
      <a href="flower-language.html">花语百科</a>
      <a href="#">企业合作</a>
    </div>
    <div class="foot-col">
      <h5>Contact</h5>
      <a href="mailto:hello@tiaowulan.com">hello@tiaowulan.com</a>
      <a href="contact.html">400-000-0000</a>
      <a href="#">9:00 – 21:00</a>
    </div>
  </div>
  <div class="foot-bottom">
    <div class="cr">© 深圳市跳舞兰科技有限公司 2026 &nbsp;·&nbsp; 粤ICP备 00000000 号</div>
    <div class="social">
      <a href="#">ig</a><a href="#">wx</a><a href="#">xhs</a><a href="#">dy</a>
    </div>
  </div>
</footer>

</body>
</html>
'''

CTA_SHOP = '<div class="cta"><a href="shop.html">看看花束</a></div>'
CTA_NONE = ''

PAGES = {

"about.html": dict(
    title="关于跳舞兰",
    kicker="About",
    subtitle="2016 年生于深圳的花艺工作室",
    desc="跳舞兰成立于 2016 年，是深圳的花艺工作室。提供花束、花艺定制、企业订花。深圳同城 2 小时达。",
    content='''
<h3>我们相信什么</h3>
<p>
  跳舞兰诞生于 2016 年的深圳。<br>
  我们相信，花不只属于节日与仪式 —— 它也可以是某个普通的下午，
  桌角上的一小束，或者递给同事时随手的一枝。
</p>
<p>
  「<strong>与花共度的每一天</strong>」这句话，既是我们的名字，也是我们想做的事：
  让花重新回到生活里，像它本来该有的样子。
</p>

<h3>我们做什么</h3>
<p>
  我们每天从云南直采花材，冷链到店，当日制作。
  不做隔夜花，不囤货，不为了好看而用不新鲜的花。
</p>
<p>
  每一束花都由花艺师手工完成。花材受季节影响，
  如果遇到个别缺货，我们会提前联系你，而不是自作主张换掉。
</p>

<h3>数字</h3>
<div class="dl">
  <div class="row"><span class="k">成立年份</span><span class="v hl">2016</span></div>
  <div class="row"><span class="k">服务城市</span><span class="v">深圳 · 广州 · 全国 200+ 城市</span></div>
  <div class="row"><span class="k">深圳配送</span><span class="v">同城 2 小时达</span></div>
  <div class="row"><span class="k">其他城市</span><span class="v">次日达 · 顺丰冷链</span></div>
</div>

<h3>我们不做的事</h3>
<p>
  不做过度包装。不做假花。不做「图片仅供参考」的花束。
  不为了压价换掉花材而不告诉你。
</p>
''',
    cta=CTA_SHOP,
),

"contact.html": dict(
    title="联系我们",
    kicker="Contact",
    subtitle="有问题随时找我们",
    desc="跳舞兰联系方式：邮箱 hello@tiaowulan.com，电话 400-000-0000，服务时间每天 9:00-21:00。",
    content='''
<h3>联系方式</h3>
<div class="dl">
  <div class="row"><span class="k">邮箱</span><span class="v"><a href="mailto:hello@tiaowulan.com">hello@tiaowulan.com</a></span></div>
  <div class="row"><span class="k">电话</span><span class="v"><a href="tel:4000000000">400-000-0000</a></span></div>
  <div class="row"><span class="k">微信</span><span class="v">tiaowulan</span></div>
  <div class="row"><span class="k">服务时间</span><span class="v">每天 9:00 – 21:00</span></div>
</div>

<h3>这些事可以直接找我们</h3>
<div class="cards">
  <div class="card">
    <div class="t">订单问题</div>
    <div class="d">配送延迟、地址修改、订单取消 —— 提供订单号，我们 2 小时内回复。</div>
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

<h3>回复时间</h3>
<p>
  工作时间（9:00–21:00）内，<strong>2 小时内回复</strong>。<br>
  非工作时间提交的问题，次日 9:00 前处理。
</p>
''',
    cta='<div class="cta"><a href="mailto:hello@tiaowulan.com">发邮件给我们</a></div>',
),

"help-delivery.html": dict(
    title="配送范围",
    kicker="Delivery",
    subtitle="送哪儿、多久到、多少钱",
    desc="跳舞兰配送范围：深圳同城 2 小时达，广州次日达，全国 200+ 城市顺丰冷链。满 199 免运费。",
    content='''
<h3>配送时效</h3>
<div class="dl">
  <div class="row"><span class="k">深圳同城</span><span class="v hl">2 小时达</span></div>
  <div class="row"><span class="k">广州</span><span class="v">次日达</span></div>
  <div class="row"><span class="k">全国 200+ 城市</span><span class="v">次日达 · 顺丰冷链</span></div>
  <div class="row"><span class="k">偏远地区</span><span class="v">2–3 天</span></div>
</div>

<h3>下单截止时间</h3>
<div class="dl">
  <div class="row"><span class="k">深圳当日达</span><span class="v">当天 16:00 前下单</span></div>
  <div class="row"><span class="k">深圳次日达</span><span class="v">当天 21:00 前下单</span></div>
  <div class="row"><span class="k">其他城市</span><span class="v">提前 1 天下单</span></div>
</div>

<h3>配送费</h3>
<div class="dl">
  <div class="row"><span class="k">满 ¥199</span><span class="v hl">免运费</span></div>
  <div class="row"><span class="k">不满 ¥199</span><span class="v">¥15</span></div>
  <div class="row"><span class="k">偏远地区</span><span class="v">¥25 起</span></div>
</div>

<h3>可选时段</h3>
<p>
  深圳同城可选两个时段：<strong>14:00–16:00</strong> 和 <strong>18:00–20:00</strong>。<br>
  其他城市为全天配送（9:00–18:00），无法指定具体时段。
</p>

<h3>配送不到的情况</h3>
<p>
  如果地址超出配送范围，下单时系统会提示。
  如果已经下单但发现送不到，我们会联系你改地址或退款，不收取任何费用。
</p>

<h3>签收</h3>
<p>
  鲜花需要本人或指定收花人签收。如果收花人不在，
  配送员会电话联系。连续 3 次联系不上，订单会退回并安排二次配送（需补配送费）。
</p>
''',
    cta='<div class="cta"><a href="shop.html">现在下单</a></div>',
),

"help-returns.html": dict(
    title="售后政策",
    kicker="Returns",
    subtitle="花有问题，我们负责到底",
    desc="跳舞兰售后政策：花材破损、不新鲜、与描述不符，当天处理。支持补送、退款、部分退款。",
    content='''
<h3>什么情况可以申请售后</h3>
<div class="cards">
  <div class="card">
    <div class="t">花材破损</div>
    <div class="d">运输过程中压坏、折断 —— 拍照发我们，当天补送或退款。</div>
  </div>
  <div class="card">
    <div class="t">花材不新鲜</div>
    <div class="d">收到时已经蔫了、发黄、有异味 —— 全额退款。</div>
  </div>
  <div class="card">
    <div class="t">与描述不符</div>
    <div class="d">花材、数量、包装与页面描述明显不符 —— 部分退款或补送。</div>
  </div>
  <div class="card">
    <div class="t">配送延迟</div>
    <div class="d">超出承诺时段 2 小时以上 —— 补偿配送费或部分退款。</div>
  </div>
</div>

<h3>怎么申请</h3>
<p>
  <strong>1.</strong> 在「我的订单」找到这笔订单<br>
  <strong>2.</strong> 点「申请售后」，选择问题类型<br>
  <strong>3.</strong> 上传照片（重要，没有照片无法处理）<br>
  <strong>4.</strong> 提交后会生成工单号，客服 2 小时内联系你
</p>
<p>
  <strong>注意：</strong>游客下单无法在线申请售后，需通过邮箱或电话联系客服，
  并提供订单号。
</p>

<h3>处理时效</h3>
<div class="dl">
  <div class="row"><span class="k">客服响应</span><span class="v hl">2 小时内</span></div>
  <div class="row"><span class="k">补送</span><span class="v">当天或次日</span></div>
  <div class="row"><span class="k">退款到账</span><span class="v">1–3 个工作日</span></div>
</div>

<h3>什么情况不能退</h3>
<p>
  · 已经送达超过 <strong>24 小时</strong>才提出的（鲜花有保鲜期，无法判断责任）<br>
  · 没有照片，无法核实问题的<br>
  · 因收花人自身原因（拒收、地址错误、长时间联系不上）导致的损耗<br>
  · 定制花束中已明确告知的花材替换
</p>

<h3>退款怎么退</h3>
<p>
  原路退回。微信支付退回微信，支付宝退回支付宝。
  一般 1–3 个工作日到账，具体以支付渠道为准。
</p>
''',
    cta='<div class="cta"><a href="contact.html">联系客服</a></div>',
),

"help-faq.html": dict(
    title="常见问题",
    kicker="FAQ",
    subtitle="你可能想问的",
    desc="跳舞兰常见问题：送花时间、花材新鲜度、能否指定时间、游客下单、发票、修改地址等。",
    content='''
<h3>下单相关</h3>
<div class="dl">
  <div class="row"><span class="k">最早能什么时候送到？</span><span class="v">深圳 2 小时，其他城市次日</span></div>
  <div class="row"><span class="k">能指定送达时间吗？</span><span class="v">深圳可选时段，其他城市不能</span></div>
  <div class="row"><span class="k">可以匿名送花吗？</span><span class="v">可以，下单时勾选</span></div>
  <div class="row"><span class="k">贺卡可以写多少字？</span><span class="v">建议 30 字以内</span></div>
</div>

<h3>花材相关</h3>
<div class="dl">
  <div class="row"><span class="k">花是新鲜的吗？</span><span class="v">当日到店，当日制作</span></div>
  <div class="row"><span class="k">能养几天？</span><span class="v">含保鲜剂 5–7 天</span></div>
  <div class="row"><span class="k">缺货会怎么办？</span><span class="v">提前联系你确认替换</span></div>
  <div class="row"><span class="k">可以只要某种花吗？</span><span class="v">可以，联系客服定制</span></div>
</div>

<h3>支付相关</h3>
<div class="dl">
  <div class="row"><span class="k">支持哪些支付方式？</span><span class="v">微信 / 支付宝 / 银行卡</span></div>
  <div class="row"><span class="k">可以开发票吗？</span><span class="v">可以，联系客服</span></div>
  <div class="row"><span class="k">订单多久失效？</span><span class="v">30 分钟未支付自动取消</span></div>
</div>

<h3>账号相关</h3>
<div class="dl">
  <div class="row"><span class="k">必须登录才能买吗？</span><span class="v">不用，游客也能下单</span></div>
  <div class="row"><span class="k">游客下单有什么限制？</span><span class="v">只能当前浏览器查单，无法在线售后</span></div>
  <div class="row"><span class="k">游客订单能找回吗？</span><span class="v">登录同手机号可自动认领</span></div>
</div>

<h3>售后相关</h3>
<div class="dl">
  <div class="row"><span class="k">花有问题怎么办？</span><span class="v">拍照，24 小时内申请售后</span></div>
  <div class="row"><span class="k">多久能处理完？</span><span class="v">客服 2 小时内响应</span></div>
  <div class="row"><span class="k">能退款吗？</span><span class="v">质量问题全额退，原路退回</span></div>
</div>

<h3>还没解决？</h3>
<p>
  发邮件到 <strong>hello@tiaowulan.com</strong>，或工作时间打电话 400-000-0000。
  提供订单号，我们 2 小时内回复。
</p>
''',
    cta='<div class="cta"><a href="contact.html">联系客服</a></div>',
),

}

for fn, data in PAGES.items():
    html = TEMPLATE.format(**data)
    path = os.path.join(PROTO, fn)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  {fn}: {len(html)} 字符")

print("[done]")
