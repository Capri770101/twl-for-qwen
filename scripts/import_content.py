# -*- coding: utf-8 -*-
"""
把 Markdown 文章导入数据库

【怎么用】
    cd scripts
    python import_content.py                    # 导入全部
    python import_content.py 花语/champagne-rose.md   # 导入单篇

【Markdown 格式】
文件开头是 YAML frontmatter（--- 包起来），下面是正文。

示例：
    ---
    slug: champagne-rose
    title: 香槟玫瑰的花语是什么
    category: rose
    meaning: 爱上你是我今生最大的幸福
    tags: [玫瑰, 告白]
    status: published
    ---

    ## 正文标题

    正文内容...

    ## 常见问题

    ### 问题一？

    回答...

【FAQ 怎么提取】
正文里「## 常见问题」下面的「### 问题」+ 段落，会自动提取成 FAQ 数组，
用于生成 JSON-LD 的 FAQPage 结构化数据。
"""

import asyncio
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
BACKEND = ROOT / "backend"

sys.path.insert(0, str(BACKEND))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, check_database_connection
from app.core.logging import get_logger, setup_logging
from app.models.content import Article

setup_logging()
logger = get_logger(__name__)


# ══════════════════════════════════════════════════════════
# 解析 frontmatter
# ══════════════════════════════════════════════════════════

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    【干什么】把 MD 文件拆成 (元数据, 正文)

    【frontmatter 格式】
    ---
    key: value
    key2: [a, b]
    ---
    正文...

    【为什么自己写解析】
    不想引入 pyyaml 依赖。格式简单，自己解析够用。
    """
    if not text.startswith("---"):
        return {}, text

    # 找第二个 ---
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    header = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")

    meta = {}
    for line in header.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            continue

        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        # 数组：[a, b, c]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            meta[key] = [v.strip() for v in inner.split(",") if v.strip()]
        # 布尔
        elif value.lower() in ("true", "false"):
            meta[key] = value.lower() == "true"
        # 数字
        elif value.isdigit():
            meta[key] = int(value)
        # 字符串
        else:
            meta[key] = value

    return meta, body


# ══════════════════════════════════════════════════════════
# 提取 FAQ
# ══════════════════════════════════════════════════════════

def extract_faq(body: str) -> list[dict]:
    """
    【干什么】从正文里提取 FAQ。

    【格式】
    ## 常见问题

    ### 问题一？

    回答内容...

    ### 问题二？

    回答内容...

    【为什么这么做】
    一篇文章正文写一遍，FAQ 自动提取，
    不用在 frontmatter 里再写一遍。
    """
    # 找「## 常见问题」这一节
    m = re.search(r"##\s*常见问题\s*\n(.*?)(?=\n##\s|\Z)", body, re.DOTALL)
    if not m:
        return []

    section = m.group(1)

    # 按 ### 拆分
    parts = re.split(r"###\s*", section)
    faq = []

    for part in parts[1:]:  # 第一个是空字符串
        part = part.strip()
        if not part:
            continue

        lines = part.split("\n", 1)
        question = lines[0].strip().rstrip("？?").strip() + "？"
        answer = lines[1].strip() if len(lines) > 1 else ""

        # 去掉回答里的空行
        answer = re.sub(r"\n\s*\n", " ", answer).strip()

        if question and answer:
            faq.append({"question": question, "answer": answer})

    return faq


# ══════════════════════════════════════════════════════════
# 导入单篇
# ══════════════════════════════════════════════════════════

async def import_one(session, md_path: Path) -> tuple[str, str]:
    """
    【干什么】导入一个 MD 文件

    【返回】
        (状态, 说明)  状态是 created / updated / skipped
    """
    text = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    slug = meta.get("slug")
    title = meta.get("title")

    if not slug or not title:
        return "skipped", f"缺 slug 或 title"

    # 提取 FAQ
    faq = extract_faq(body)

    # 查有没有
    result = await session.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    data = {
        "title": title,
        "summary": meta.get("summary") or body[:150].replace("\n", " ").strip(),
        "content": body,
        "cover": meta.get("cover"),
        "category": meta.get("category"),
        "meaning": meta.get("meaning"),
        "tags": meta.get("tags"),
        "faq": faq if faq else None,
        "status": meta.get("status", "draft"),
        "seo_title": meta.get("seo_title") or title,
        "seo_description": meta.get("seo_description") or meta.get("summary"),
        "sort_weight": meta.get("sort_weight", 0),
    }

    if article:
        # 更新
        for k, v in data.items():
            if v is not None:
                setattr(article, k, v)
        return "updated", f"更新「{title}」（{len(faq)} 个 FAQ）"
    else:
        # 新增
        article = Article(
            id=f"art{__import__('secrets').token_hex(10)}",
            slug=slug,
            **data,
        )
        session.add(article)
        return "created", f"新增「{title}」（{len(faq)} 个 FAQ）"


# ══════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════

async def main(target: str | None = None):
    if not await check_database_connection():
        print("数据库连不上")
        sys.exit(1)

    if target:
        files = [CONTENT_DIR / target]
    else:
        files = sorted(CONTENT_DIR.rglob("*.md"))
        files = [f for f in files if f.name != "README.md"]

    if not files:
        print("没有找到 MD 文件")
        return

    print(f"找到 {len(files)} 个文件\n")

    created = updated = skipped = 0

    async with AsyncSessionLocal() as session:
        for f in files:
            if not f.exists():
                print(f"  ✗ {f} 不存在")
                skipped += 1
                continue

            status, msg = await import_one(session, f)

            if status == "created":
                print(f"  + {f.relative_to(CONTENT_DIR)}  {msg}")
                created += 1
            elif status == "updated":
                print(f"  ~ {f.relative_to(CONTENT_DIR)}  {msg}")
                updated += 1
            else:
                print(f"  - {f.relative_to(CONTENT_DIR)}  {msg}")
                skipped += 1

        await session.commit()

    print()
    print(f"新增 {created}，更新 {updated}，跳过 {skipped}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(target))
