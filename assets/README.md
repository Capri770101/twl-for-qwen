# 设计素材

商品的原始图片。**不是前端用的图**。

---

## 结构

```
assets/
├── products/                 商品原图
│   ├── 00_white_rose.png     白玫瑰
│   ├── 01_chenguang.png      晨光序曲
│   ├── 02_xiaoman.png        小满
│   ├── 03_wuye.png           午夜蓝调
│   ├── 04_muxing.png         木星
│   ├── 05_xueluo.png         雪落
│   └── 06_shancha.png        山茶
│
└── hero/
    └── hero_workshop.png     首页大图
```

---

## 和 `frontend/images/` 的区别

| 目录 | 用途 | 谁用 |
|---|---|---|
| `assets/` | **设计源文件**，原图 | 改图时从这里改 |
| `frontend/images/` | **前端用的图**，经过压缩 | 页面加载 |

**流程：**

```
拍照/生成原图
  ↓ 存到 assets/
修图、压缩
  ↓ 复制到 frontend/images/
页面引用 /images/xx.png
```

**为什么分开：**

- `assets/` 的图可能是几 MB 的高清原图，直接给页面用太慢
- `frontend/images/` 的是压缩过的，加载快
- 分开放，以后换图只要替换 `frontend/images/` 里的，不用碰原图

---

## 当前状态

**这些图都是 AI 生成的（ComfyUI），用于原型阶段。**

**上线前必须换成真实花艺摄影。**

原因：
- AI 生成的花不完全是真实品种的样子
- 客户收到实物和图片差距大 → 售后问题
- 品牌信任度：真实照片比 AI 图更可信

**拍摄建议：**

- 白墙背景，自然光
- 侧 45 度角，能看出花束层次
- 手持拍摄（露手臂），体现真实尺寸
- 同一束花拍 2–3 个角度
- 后期只调亮度对比，不做色彩美化

---

## 加新图

1. 原图放 `assets/products/`
2. 压缩到 200KB 以内（用 squoosh.app 或 TinyPNG）
3. 复制到 `frontend/images/`
4. 在数据库里更新商品的 `cover` 字段：
   ```sql
   UPDATE products SET cover = '/images/07_xxx.png' WHERE id = 'TW-007';
   ```
