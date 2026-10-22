/* ═══════════════════════════════════════════════════════════
   跳舞兰 · 动效运行时（motion.js）
   ───────────────────────────────────────────────────────────
   必须放在 js/api.js 之后加载（要包装 TWL.updateBadge）。

   做什么：
     1. 滚动入场 —— 区块进入视口时淡入上移
     2. 图片加载淡入
     3. 购物袋数字变化时弹一下
     4. 动态渲染的内容（商品列表等）自动接管

   三条安全线（改之前务必读）：
     · 没有 IntersectionObserver 就完全不加 .reveal class，
       元素保持默认可见，绝不出现「页面一片空白」
     · 2.5 秒兜底：还没入场的元素强制显示
     · prefers-reduced-motion 下整体退化为瞬时切换
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  var reduceMotion = false;
  try {
    reduceMotion = window.matchMedia
      && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (e) { /* 老浏览器忽略 */ }

  var canObserve = ('IntersectionObserver' in window) && !reduceMotion;

  /* 自动入场的区块。
     只挑「成块的内容容器」，不碰按钮、图标这种点一下就变的小元素。

     注意：选择器要按各页面真实的 DOM 结构来点，不能想当然。
     首页用的是 <section class="story|duo|process|cat-entry">，
     一开始没把 section 列进来，结果整个首页只有 1 个元素有入场动效，
     肉眼根本看不出 —— 这就是「动效没生效」的真正原因。

     下面按页面类型分组，改的时候对号入座：
       [通用]   section / page-head / card / box / item
       [商城]   shop .grid、product .pdp
       [交易]   cart .cart-*、checkout .wrap、pay .methods
       [订单]   orders .ord-wrap、order-detail .od-wrap、order-success .res-wrap
       [账户]   login .login-wrap、address .addr-wrap
       [内容]   about .about-wrap、contact .co2、flower .list、help .help-body
       [后台]   admin .stat / .box */
  var AUTO_SELECTOR = [
    /* ── 通用 ── */
    'section',
    '.page-head',
    '.page-title',
    '.hero-inner',
    '.card',
    '.grid > *',
    '.item',
    '.box',
    '.stat',
    '.alert',

    /* ── 商城 ── */
    /* 商品详情：不整块入场，让主图和信息区分开动 ——
       主图「推近」、信息逐条浮现，比整块淡入有层次。
       .pdp 本身不列进来，否则父子同时位移，视觉上会叠加成一坨。 */
    '.pdp > .gallery',
    '.pdp > .info',
    '.pd-wrap',
    '.filters',
    '.chips',

    /* ── 交易链路 ── */
    '.cart-wrap',
    '.cart-left',
    '.cart-right',
    '.summary',
    '.wrap > .left',
    '.wrap > .right',
    '.methods',
    '.step',

    /* ── 订单 ── */
    '.ord-wrap',
    '.od-wrap',
    '.res-wrap',
    '.order',               /* 订单列表里的每条（<a class="order">） */
    '.timeline > *',        /* 订单详情的状态时间线 */

    /* ── 账户 ── */
    '.login-wrap',
    '.fld',
    '.addr-wrap',

    /* ── 内容页 ── */
    '.about-wrap',
    '.co2',
    '.as-wrap',
    '.help-wrap',
    '.help-body',
    '.art-wrap',
    '.list > *',
    '.faq-item',

    /* ── 搜索 ── */
    '.search-wrap',
    '.search-box',
    '.hot',
  ].join(',');

  var io = null;

  if (canObserve) {
    /* 【为什么不再 unobserve】
       原来入场一次就 unobserve，元素滚出再滚回来永远不再播动画 ——
       这就是「只有第一次才出现」。改成双向：进视口加 .in，出视口摘 .in，
       滚回来重新播。

       【关键：重置必须等元素「完全离开视口」】
       不能靠 rootMargin 判可见性来重置 —— 那样元素在视口顶部边缘时
       会被判为不可见，直接摘掉 .in，用户眼睁睁看着内容消失。
       所以这里只用 rootMargin 控制「入场时机」（底部收缩 14%，
       等元素真的进到画面里再动），重置则手动判断它是否已经完全滚出屏幕。

       【400ms 冷却】
       快速来回滚动时，避免元素在阈值附近反复切换导致闪烁。 */
    io = new IntersectionObserver(function (entries) {
      var vh = window.innerHeight || 800;

      for (var i = 0; i < entries.length; i++) {
        var e = entries[i];
        var el = e.target;

        if (e.isIntersecting) {
          el.classList.add('in');
          el.__twlShown = true;
          continue;
        }

        /* 不可见 → 只有真的完全滚出屏幕才重置 */
        if (!el.__twlShown) continue;

        var rect = el.getBoundingClientRect();
        var fullyOut = (rect.bottom <= 0) || (rect.top >= vh);
        if (!fullyOut) continue;

        var now = Date.now();
        if (el.__twlResetAt && now - el.__twlResetAt < 400) continue;

        el.classList.remove('in');
        el.__twlResetAt = now;
      }
    }, {
      rootMargin: '0px 0px -14% 0px',
      threshold: 0,
    });
  }

  /* 给元素挂入场动效。没有观察器时直接跳过 —— 宁可没动效，
     也不能让内容因为 opacity:0 而看不见。 */
  function markReveal(el, delay) {
    if (!io || !el || el.classList.contains('reveal')) return;
    el.classList.add('reveal');
    if (delay) el.setAttribute('data-delay', String(delay));
    io.observe(el);
  }

  /* ── 扫描一遍 DOM ── */
  function scan(root) {
    if (!io) return;
    var scope = root || document;

    /* 成块内容。
       视口内的元素给错峰延迟 —— 首屏是用户唯一一定会看到的地方，
       如果所有区块同时淡入，750ms 内就结束了，等于「打开就是成品」，
       用户感觉不到动效。错峰之后是「标题 → 图 → 文字」依次出现。 */
    var nodes = scope.querySelectorAll(AUTO_SELECTOR);
    var vh = window.innerHeight || 800;
    var inViewSeq = 0;

    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var rect = el.getBoundingClientRect();
      var inViewport = rect.top < vh && rect.bottom > 0;

      var delay = 0;
      if (inViewport) {
        delay = Math.min(inViewSeq + 1, 6);
        inViewSeq++;
      }

      markReveal(el, delay);
    }

    /* 列表/网格里的子项错峰入场。
       不同页面用的容器类名不一样（商城 .grid、花语 .list、帮助页 .cards、
       订单 #orderList），这里一起处理，避免每个页面单独写。 */
    var groups = scope.querySelectorAll('.grid, .list, .cards, #orderList, .ord-list');
    for (var g = 0; g < groups.length; g++) {
      var kids = groups[g].children;
      for (var k = 0; k < kids.length; k++) {
        markReveal(kids[k], (k % 6) + 1);
      }
    }

    /* FAQ 条目也逐条入场 */
    var faqs = scope.querySelectorAll('.faq-item, .help-body > dl');
    for (var q = 0; q < faqs.length; q++) {
      markReveal(faqs[q], Math.min(q + 1, 6));
    }
  }

  /* ── 图片加载淡入 ── */
  function fadeImages(root) {
    var scope = root || document;
    var imgs = scope.querySelectorAll('img:not([data-fade])');
    for (var i = 0; i < imgs.length; i++) {
      (function (img) {
        /* 已经加载完的直接显示，不要再闪一下 */
        if (img.complete && img.naturalWidth > 0) {
          img.setAttribute('data-fade', '');
          img.classList.add('loaded');
          return;
        }
        img.setAttribute('data-fade', '');
        img.addEventListener('load', function () {
          img.classList.add('loaded');
        }, { once: true });
        img.addEventListener('error', function () {
          img.classList.add('loaded');
        }, { once: true });
      })(imgs[i]);
    }
  }

  /* ── 数字滚动 ──
     适用：后台数据看板的 .stat .num、任何带 data-count 的元素。
     数字从 0 滚到目标值，比直接蹦出个数字有质感得多。

     【为什么跳过有子元素的】
     后台营收那格是 `3,486<small>元</small>`，直接改 textContent 会把
     <small> 标签干掉。所以只处理「纯文本」的数字格，带标签的跳过，
     宁可不动也不破坏结构。 */
  function countUp(el, duration) {
    if (!el || el.__twlCounting) return;
    if (el.children && el.children.length > 0) return;

    var raw = (el.textContent || '').trim();
    if (!raw) return;

    /* 拆成 前缀 + 数字 + 后缀，例如 "¥3,486" → ("¥", 3486, "") */
    var m = raw.match(/^([^\d\-]*)(-?[\d,]+(?:\.\d+)?)([\s\S]*)$/);
    if (!m) return;

    var prefix = m[1];
    var numStr = m[2].replace(/,/g, '');
    var suffix = m[3];
    var target = parseFloat(numStr);
    if (!isFinite(target) || target === 0) return;

    var decimals = (numStr.split('.')[1] || '').length;
    var dur = duration || 900;
    var startTs = null;

    el.__twlCounting = true;

    function fmt(v) {
      var fixed = v.toFixed(decimals);
      /* 整数部分加千分位，和后端 money() 的显示保持一致 */
      var parts = fixed.split('.');
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
      return parts.join('.');
    }

    function frame(now) {
      if (startTs === null) startTs = now;
      var t = Math.min((now - startTs) / dur, 1);
      /* easeOutCubic：起步快、收尾慢，滚动的感觉更自然 */
      var eased = 1 - Math.pow(1 - t, 3);

      if (t < 1) {
        el.textContent = prefix + fmt(target * eased) + suffix;
        requestAnimationFrame(frame);
      } else {
        /* 收尾用原文，避免格式和原显示有细微差异 */
        el.textContent = raw;
        el.__twlCounting = false;
      }
    }

    requestAnimationFrame(frame);
  }

  /* 监听数字变化：后台数据是异步填进来的，
     等它填完再滚，不能一上来就滚。 */
  function watchNumbers() {
    if (typeof MutationObserver === 'undefined') return;

    var SEL = '.stat .num, [data-count]';

    function attach(el) {
      if (el.__twlNumWatched) return;
      el.__twlNumWatched = true;
      el.__twlLastNum = (el.textContent || '').trim();

      var mo = new MutationObserver(function () {
        var now = (el.textContent || '').trim();
        if (now === el.__twlLastNum) return;
        el.__twlLastNum = now;
        countUp(el);
      });
      mo.observe(el, { childList: true, characterData: true, subtree: true });
    }

    document.querySelectorAll(SEL).forEach(attach);

    /* 动态插入的数字格也要接管 */
    var bodyMo = new MutationObserver(function (records) {
      for (var i = 0; i < records.length; i++) {
        var added = records[i].addedNodes;
        for (var j = 0; j < added.length; j++) {
          var node = added[j];
          if (node.nodeType !== 1) continue;
          if (node.matches && node.matches(SEL)) attach(node);
          if (node.querySelectorAll) {
            node.querySelectorAll(SEL).forEach(attach);
          }
        }
      }
    });
    bodyMo.observe(document.body, { childList: true, subtree: true });
  }

  /* ── 购物袋数字弹跳 ── */
  function hookBagBadge() {
    if (!window.TWL || typeof window.TWL.updateBadge !== 'function') return;
    if (window.TWL.__motionHooked) return;

    var original = window.TWL.updateBadge.bind(window.TWL);

    window.TWL.updateBadge = function () {
      var before = null;
      var el0 = document.querySelector('.bag-count');
      if (el0) before = el0.textContent;

      original();

      var el = document.querySelector('.bag-count');
      if (!el) return;
      if (before === null || el.textContent !== before) {
        el.classList.remove('pop');
        /* 强制重排，让动画能连续触发 */
        void el.offsetWidth;
        el.classList.add('pop');
      }
    };

    window.TWL.__motionHooked = true;
  }

  /* ── 监听动态渲染的内容 ── */
  function watchMutations() {
    if (!io || typeof MutationObserver === 'undefined') return;

    var pending = null;
    var mo = new MutationObserver(function (records) {
      var hasNewElement = false;
      for (var i = 0; i < records.length; i++) {
        if (records[i].addedNodes && records[i].addedNodes.length) {
          hasNewElement = true;
          break;
        }
      }
      if (!hasNewElement) return;

      /* 合并 120ms 内的多次变化，避免列表渲染时反复扫描 */
      if (pending) clearTimeout(pending);
      pending = setTimeout(function () {
        pending = null;
        scan();
        fadeImages();
      }, 120);
    });

    mo.observe(document.body, { childList: true, subtree: true });
  }

  /* ── 启动 ── */
  function boot() {
    hookBagBadge();
    scan();
    fadeImages();
    watchMutations();
    watchNumbers();

    /* 兜底：只在「观察器明显失效」时才强制显示。

       为什么不能无条件 2.5 秒后全显示 —— 那会把还没滚到的元素
       提前点亮，用户之后滚过去就没有入场动画了，等于把动效废掉。
       这就是「动效没生效」的真正原因。

       判据：3 秒后如果连一个元素都没入场过，说明 IntersectionObserver
       没在工作（被禁用、被 polyfill 破坏、或页面结构异常），
       这时候才全部显示，保证内容不会永远看不见。 */
    setTimeout(function () {
      var entered = document.querySelectorAll('.reveal.in').length;
      if (entered === 0) {
        var hidden = document.querySelectorAll('.reveal:not(.in)');
        for (var i = 0; i < hidden.length; i++) {
          hidden[i].classList.add('in');
        }
      }

      /* 图片单独兜底：3 秒还没 load 的（比如 src 为空、404），
         直接显示，避免永久透明。 */
      var unfaded = document.querySelectorAll('img[data-fade]:not(.loaded)');
      for (var j = 0; j < unfaded.length; j++) {
        unfaded[j].classList.add('loaded');
      }
    }, 3000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  /* 暴露给页面：动态渲染完可以手动调一次 */
  window.Motion = {
    scan: scan,
    fadeImages: fadeImages,
    countUp: countUp,
    reduced: reduceMotion,
  };
})();
