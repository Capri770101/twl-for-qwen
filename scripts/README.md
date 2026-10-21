# 脚本

开发和运维用的脚本。

---

## 测试脚本

### `full_test.py` —— 全流程测试（62 项）

按真实用户路径走一遍，验证每一步的状态变化。

```bash
# 需要后端在跑
python full_test.py
```

**覆盖：**

```
一、认证流程            6 项
二、地址簿增删改查      10 项
三、商品浏览与筛选       7 项
四、下单→支付→流转     12 项
五、订单取消与恢复       4 项
六、售后工单             3 项
七、配置读写             1 项
八、文章管理             6 项
九、后台统计             4 项
十、边界与安全           7 项
──────────────────────────────
                        62 项
```

**输出：** 逐项打勾 + 最后汇总。当前 62/62 全通过。

---

### `security_test.py` —— 安全测试（18 项）

```bash
python security_test.py
```

**覆盖：**

```
后台接口鉴权           4 项
内容与配置鉴权         4 项
上传鉴权               1 项
限流                   2 项
权限分级               2 项
Token 黑名单           3 项
其他                   2 项
──────────────────────────────
                      18 项
```

**输出：** 逐项打勾。当前 18/18 全通过。

---

## 工具脚本

### `embed_luxe.py` —— 图片内嵌

把 HTML 里的 `__IMG_xxx__` 占位符替换成 base64。

```bash
python embed_luxe.py
```

**什么时候用：**

- 给页面加了新图
- 从 `frontend/images/` 批量内嵌到 HTML

**注意：** 只有部分页面需要内嵌（首页、购物袋、售后）。商城和商品详情是从 API 动态加载图片的，不需要内嵌。

---

## 建议的检查流程

改完代码后：

```bash
# 1. 跑单元测试（不需要服务）
cd ../backend
.venv\Scripts\python -m pytest tests/ -q

# 2. 跑集成测试（需要服务）
cd ../scripts
python full_test.py
python security_test.py
```

**三个都通过，说明改动没破坏已有功能。**
---

## 演示模式相关

### eset_demo.py —— 一键清空演示数据

`ash
python reset_demo.py
`

**会删：**
- 所有 is_demo=true 的商品
- 所有 is_demo=true 的订单（含明细、日志、支付、配送、工单）
- 非管理员用户

**不会删：**
- 表结构
- 管理员账号
- 配送规则配置
- 花语文章

**什么时候用：** 老板接手、灌真实数据之前。

---

### seo_config.py —— SEO 配置表

21 个页面的 title / description / keywords / schema 都在这。

**改 SEO 就改这个文件，然后重跑 pply_seo.py。**

---

### pply_seo.py —— 注入 SEO 元信息

`ash
python apply_seo.py
`

给 21 个页面注入 robots / description / canonical / OG / Twitter Card / JSON-LD。

**重复跑不会重复插入**（会先删旧的 SEO 块）。

---

### gen_site_files.py —— 生成三个站点文件

`ash
python gen_site_files.py
`

生成：
- rontend/robots.txt
- rontend/sitemap.xml（从数据库读商品和文章）
- rontend/llms.txt（GEO 专用）

**加了新文章或新商品后要重跑。**

---

### check_seo.py —— SEO 验收

`ash
python check_seo.py
`

检查 21 个页面的 title / description / canonical / OG / JSON-LD / robots / h1 / alt。

---

### check_paths.py —— 路径可移植性

`ash
python check_paths.py
`

检查有没有硬编码绝对路径，确保项目换位置能跑。

---

### import_content.py —— 导入 Markdown 文章

`ash
python import_content.py                    # 导入全部
python import_content.py 花语/champagne-rose.md   # 导入单篇
`

解析 frontmatter + 自动提取 FAQ，写入数据库。

**写作规范见 content/README.md。**