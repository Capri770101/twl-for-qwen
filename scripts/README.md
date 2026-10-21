# 脚本

开发和运维用的脚本。**全部可用，不是示例。**

---

## 测试脚本（5 个）

### `test_loop.py` —— 业务闭环测试（21 项）

**最重要的一组。** 验证「用户下单 → 支付 → 后台推进 → 售后回复」整条链路。

```bash
python test_loop.py          # 需要后端在跑
```

**覆盖：**

```
── 用户侧 ──
 1. 浏览商品
 2. 商品详情
 3. 配送可用性
 4. 创建订单（游客）
 5. 查订单（待支付）
 6. 发起支付
 7. 支付回调
 8. 支付后状态（已支付）
 9. 重复回调幂等

── 后台侧 ──
10. 管理员登录
11. 后台看到订单
12. 后台统计

── 订单状态推进 ──
13. 推进 → 配花中      preparing
13. 推进 → 配送中      delivering
13. 推进 → 已送达      delivered
13. 推进 → 已完成      completed
14. 非法流转被拒       409

── 售后 ──
15. 用户提工单
16. 后台看到工单
17. 后台回复
18. 工单状态变更（resolved）
──────────────────────────
                        21 项
```

**注意：** 会真实创建订单和工单，跑多了数据库会有测试数据。

---

### `test_mcp.py` —— MCP 工具测试（13 项）

**不需要服务，直接调工具函数。**

```bash
cd backend
.venv\Scripts\python.exe ..\scripts\test_mcp.py
```

**覆盖：**

```
 1. search_flowers      搜花
 2.   按关键词
 3.   按分类
 4.   按价格
 5. get_product         商品详情
 6.   不存在商品        错误处理
 7. check_delivery      配送可用性
 8. list_categories     分类列表
 9. get_flower_meaning  查花语
10. list_articles       文章列表
11. create_order        下单
12. query_order         查订单
13. create_ticket       提工单
──────────────────────────
                        13 项
```

**注意：** `create_order` 会占库存。

---

### `full_test.py` —— 全流程测试（62 项）

接口层的完整测试，覆盖所有模块。

```bash
python full_test.py          # 需要后端在跑
```

**覆盖：**

```
一、认证流程             6 项
二、地址簿增删改查       10 项
三、商品浏览与筛选        7 项
四、下单 → 支付 → 流转   12 项
五、订单取消与库存恢复     4 项
六、售后工单              3 项
七、配置读写              1 项
八、文章管理              6 项
九、后台统计              4 项
十、边界与安全            7 项
──────────────────────────
                         62 项
```

**和 `test_loop.py` 的区别：**
- `full_test.py` 测**接口能不能用**
- `test_loop.py` 测**业务流程通不通**

---

### `security_test.py` —— 安全测试（18 项）

```bash
python security_test.py      # 需要后端在跑
```

**覆盖：**

```
后台接口鉴权             4 项
内容与配置鉴权           4 项
上传鉴权                 1 项
限流                     2 项
权限分级                 2 项
Token 黑名单             3 项
其他                     2 项
──────────────────────────
                        18 项
```

---

### 单元测试（20 个）

不在这个目录，在 `backend/tests/`。

```bash
cd backend
.venv\Scripts\python.exe -m pytest tests/ -q
```

**覆盖：** 订单状态机、金额计算、token 解析、日志脱敏、限流逻辑。

**不需要数据库。**

---

## SEO / 性能脚本（5 个）

### `audit_seo.py` —— SEO 综合测评

**出分数，找问题。**

```bash
python audit_seo.py          # 需要后端在跑
```

**测 6 大类：**

```
1. 爬虫可读性        关键内容在不在 HTML 源码里
2. meta 唯一性       每篇文章的 title/description/canonical 是否不同
3. 结构化数据        JSON-LD 语义完整性
4. 内容质量          字数、FAQ 数、有没有一句话答案
5. 站点文件          sitemap/llms.txt 是否包含所有内容
6. 内链              文章之间有没有链接
```

**输出示例：**

```
爬虫可读性            ██████████ 7/7  100%
文章 meta 唯一       ██████████ 5/5  100%
结构化数据            ██████████ 4/4  100%
内容质量             ██████████ 15/15  100%
sitemap           ██████████ 31/31  100%
llms.txt          ██████████ 5/5  100%
内链                ██████████ 15/15  100%

总分  100%
```

---

### `check_crawl.py` —— 爬虫可读性

**单独测这一项**（`audit_seo.py` 里也有，但这个是专项）。

```bash
python check_crawl.py        # 需要后端在跑
```

**为什么重要：** 如果关键内容不在 HTML 源码里（靠 JS 渲染），爬虫读不到，SEO 就是废的。

**改造前 3/7，改造后 7/7。**

---

### `check_perf.py` —— 轻量性能测评

**不依赖 Lighthouse**，直接测 TTFB、页面大小、阻塞资源。

```bash
python check_perf.py         # 需要后端在跑
```

**输出：**

```
TTFB             6 ms  →  100 分
阻塞资源         0 个   →  100 分
最大页面        33 KB  →  100 分
外部依赖         5 个   →  75 分

综合        93 分
```

**和 Lighthouse 的关系：** 这个是快速检查，Lighthouse 是完整报告。

---

### `check_paths.py` —— 路径可移植性

**检查有没有硬编码绝对路径。**

```bash
python check_paths.py
```

**测 6 项：**

```
1. 有没有 D:\ 这类硬编码路径
2. Python 文件是否用 __file__ 算路径
3. 前端资源引用是否正确
4. 页面之间的链接是否有效
5. docs 里的链接是否有效
6. 启动脚本是否用相对定位
```

**为什么需要：** 项目换位置后能不能跑。

---

### 内容生成（3 个）

#### `import_content.py` —— Markdown 导入

```bash
python import_content.py                    # 导入全部
python import_content.py 花语/white-rose.md  # 导入单篇
```

**做什么：**
- 解析 frontmatter（slug/title/category/...）
- 自动提取「## 常见问题」下的 FAQ
- 有则更新，无则新增

**写作规范见** `content/README.md`。

#### `apply_seo.py` —— 注入 meta

```bash
python apply_seo.py
```

给 21 个页面注入 robots / description / canonical / OG / Twitter Card / JSON-LD。

**配置在 `seo_config.py`**，改 SEO 就改那个文件。

#### `gen_site_files.py` —— 生成站点文件

```bash
python gen_site_files.py
```

生成：
- `frontend/robots.txt`
- `frontend/sitemap.xml`（从数据库读商品和文章）
- `frontend/llms.txt`（GEO 专用）

**加了新文章或新商品后要重跑。**

---

## 优化脚本（3 个）

### `compress_images.py` —— 图片压缩 PNG → WebP

```bash
python compress_images.py
```

**效果：** 6571KB → 315KB（-95%）

**参数：** quality=82，限制最大边长 1600px。

**加了新图要跑一次。**

### `opt_fonts.py` —— 去 Google Fonts

```bash
python opt_fonts.py
```

把 Google Fonts 换成系统字体，省 495KB + 6 个外部请求。

**一次性操作，不用重复跑。**

### `opt_perf.py` —— 性能优化

```bash
python opt_perf.py
```

- 给 api.js 加 defer
- 后端加 GZip
- 静态文件加缓存头

**一次性操作。**

---

## 数据脚本（2 个）

### `reset_demo.py` —— 清空演示数据

```bash
python reset_demo.py
```

**会删：**
- 所有 `is_demo=true` 的商品
- 所有 `is_demo=true` 的订单（含明细、日志、支付、配送、工单）
- 非管理员用户
- 所有地址

**不会删：**
- 表结构
- 管理员账号
- 配送规则配置
- 花语文章

**什么时候用：** 老板接手、灌真实数据之前。

### `add_internal_links.py` —— 批量加内链

```bash
python add_internal_links.py
```

给文章末尾加「你可能还想知道」区块，链接到相关文章。

**配置在脚本里的 `LINKS` 字典。**

---

## 启动脚本

### `start.ps1` —— 启动服务

```powershell
.\start.ps1
```

**或者双击根目录的 `启动.bat`。**

**做什么：**
1. 检查虚拟环境
2. 检查 .env（没有就从模板复制）
3. 检查端口占用
4. 启动 uvicorn

---

## 建议的检查流程

**改完代码：**

```bash
# 1. 单元测试（不需要服务）
cd ../backend
.venv\Scripts\python.exe -m pytest tests/ -q

# 2. 业务闭环（需要服务）
cd ../scripts
python test_loop.py

# 3. 全流程
python full_test.py

# 4. 安全
python security_test.py
```

**改完内容：**

```bash
python import_content.py
python gen_site_files.py
python audit_seo.py
```

**改完前端：**

```bash
python check_crawl.py
python audit_seo.py
python check_perf.py
```

---

## 全部脚本清单

| 脚本 | 用途 | 需要服务 | 一次性 |
|---|---|---|---|
| `test_loop.py` | 业务闭环测试（21 项） | ✓ | |
| `test_mcp.py` | MCP 工具测试（13 项） | | |
| `full_test.py` | 全流程测试（62 项） | ✓ | |
| `security_test.py` | 安全测试（18 项） | ✓ | |
| `audit_seo.py` | SEO 综合测评 | ✓ | |
| `check_crawl.py` | 爬虫可读性 | ✓ | |
| `check_perf.py` | 性能测评 | ✓ | |
| `check_paths.py` | 路径可移植性 | | |
| `import_content.py` | Markdown 导入 | | |
| `apply_seo.py` | 注入 meta | | |
| `gen_site_files.py` | 生成 sitemap/llms | | |
| `compress_images.py` | 图片压缩 | | |
| `add_internal_links.py` | 批量加内链 | | |
| `reset_demo.py` | 清空演示数据 | | |
| `opt_fonts.py` | 去 Google Fonts | | ✓ |
| `opt_perf.py` | 性能优化 | | ✓ |
| `start.ps1` | 启动服务 | | |

---

## 图片生成（3 个，ComfyUI 专用）

首页 21:9 通栏图的生成脚本。**只在需要换 hero 图时用。**

| 脚本 | 干什么 |
|---|---|
| `gen_hero_test.py` | 低分辨率试方向（1024x439） |
| `gen_hero_directions.py` | 批量生成多个方向候选 |
| `gen_hero_final.py` | 选定方向后放大到成品（2688x1152） |

**依赖：**
- 本机 ComfyUI（`D:\ComfyUI`）
- 模型：anima-aesthetic-v1.1 + 2x-AnimeSharpV4

**输出：** `frontend/images/hero_*.webp`

**注意：** 这些是**一次性工具**，不是日常脚本。
生成后手动挑选、压缩（`compress_images.py`）、替换引用。
