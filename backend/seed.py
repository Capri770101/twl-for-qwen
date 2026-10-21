# ============================================================
# 【这个文件是干什么的】
# 往数据库里灌初始数据（8 个商品）。
#
# 【什么时候用】
#   1. 第一次部署（数据库是空的）
#   2. 想重置商品数据
#
# 【怎么跑】
#   cd backend
#   .venv\Scripts\python.exe seed.py
#
# 【注意】
# - 会先删除同 ID 的商品再插入，所以可以重复跑
# - 不会删订单（订单是真实数据）
# - 前提：数据库表已经建好（先跑 alembic upgrade head）
# ============================================================

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

# 把项目根目录加到路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal, check_database_connection
from app.core.logging import get_logger, setup_logging
from app.models import Product, ProductCategory, ProductStatus

setup_logging()
logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════
# 【商品数据】
#
# 要改商品就改这里，然后重新跑脚本。
#
# 字段说明：
#   id            商品编号
#   name          商品名
#   subtitle      副标题
#   price         售价（元，用字符串避免浮点误差）
#   original_price 原价（None 表示没有）
#   cover         图片地址
#   flowers       花材清单
#   meaning       花语
#   category      分类
#   sort_order    排序权重
# ════════════════════════════════════════════════════════════
PRODUCTS = [
    {
        "id": "TW-001",
        "name": "晨光序曲",
        "subtitle": "香槟玫瑰 20 枝 · 满天星",
        "price": "299.00",
        "original_price": "359.00",
        "cover": "/images/01_chenguang.png",
        "flowers": ["香槟玫瑰 ×20", "满天星", "尤加利叶", "雾面包装纸", "香槟丝带"],
        "meaning": "香槟色介于热恋与克制之间。适合说了一句「我在」之后，什么都不必再说的时刻。",
        "category": ProductCategory.LOVE.value,
        "sort_order": 1,
    },
    {
        "id": "TW-002",
        "name": "小满",
        "subtitle": "白郁金香 12 枝 · 尤加利",
        "price": "259.00",
        "original_price": None,
        "cover": "/images/02_xiaoman.png",
        "flowers": ["白郁金香 ×12", "尤加利叶", "白色包装纸", "白丝带"],
        "meaning": "刚刚好，不多不少的喜欢。",
        "category": ProductCategory.DAILY.value,
        "sort_order": 2,
    },
    {
        "id": "TW-003",
        "name": "午夜蓝调",
        "subtitle": "蓝紫绣球 3 枝 · 银叶菊",
        "price": "359.00",
        "original_price": None,
        "cover": "/images/03_wuye.png",
        "flowers": ["蓝紫绣球 ×3", "银叶菊", "深蓝包装纸", "藏青丝带"],
        "meaning": "夜里想起一个人时，就是这个颜色。",
        "category": ProductCategory.LOVE.value,
        "sort_order": 3,
    },
    {
        "id": "TW-004",
        "name": "木星",
        "subtitle": "向日葵 6 枝 · 尤加利叶",
        "price": "219.00",
        "original_price": None,
        "cover": "/images/04_muxing.png",
        "flowers": ["向日葵 ×6", "尤加利叶", "牛皮纸", "麻绳"],
        "meaning": "把晴天寄给你。",
        "category": ProductCategory.BIRTHDAY.value,
        "sort_order": 4,
    },
    {
        "id": "TW-005",
        "name": "雪落",
        "subtitle": "白玫瑰 33 枝 · 银叶菊",
        "price": "499.00",
        "original_price": "559.00",
        "cover": "/images/05_xueluo.png",
        "flowers": ["白玫瑰 ×33", "银叶菊", "象牙白包装纸", "白丝带"],
        "meaning": "三十三，是三生三世里没说完的那句。",
        "category": ProductCategory.LOVE.value,
        "sort_order": 5,
    },
    {
        "id": "TW-006",
        "name": "山茶",
        "subtitle": "红茶花 9 枝 · 枯枝",
        "price": "279.00",
        "original_price": None,
        "cover": "/images/06_shancha.png",
        "flowers": ["红茶花 ×9", "枯枝", "深红包装纸", "黑丝带"],
        "meaning": "冬天里唯一不肯低头的颜色。",
        "category": ProductCategory.SYMPATHY.value,
        "sort_order": 6,
    },
    {
        "id": "TW-007",
        "name": "微风",
        "subtitle": "洋桔梗 15 枝 · 应季配叶",
        "price": "289.00",
        "original_price": None,
        "cover": "/images/00_white_rose.png",
        "flowers": ["洋桔梗 ×15", "应季配叶", "浅色包装纸", "米白丝带"],
        "meaning": "轻轻掠过，却让人记很久。",
        "category": ProductCategory.DAILY.value,
        "sort_order": 7,
    },
    {
        "id": "TW-008",
        "name": "四季",
        "subtitle": "当季花材 12 枝 · 每周更换",
        "price": "329.00",
        "original_price": None,
        "cover": "/images/00_white_rose.png",
        "flowers": ["当季混合花材 ×12", "配叶", "牛皮纸", "麻绳"],
        "meaning": "一年四季，各有各的好。",
        "category": ProductCategory.BIRTHDAY.value,
        "sort_order": 8,
    },
]


async def seed() -> None:
    """【干什么】执行数据初始化"""

    # 先检查数据库能不能连上
    if not await check_database_connection():
        logger.error("数据库连不上，请检查 .env 配置")
        sys.exit(1)

    async with AsyncSessionLocal() as session:
        # 逐个商品：先删同 ID 的，再插入
        for data in PRODUCTS:
            # 删除已有的
            await session.execute(delete(Product).where(Product.id == data["id"]))

            # 插入新的
            product = Product(
                id=data["id"],
                name=data["name"],
                subtitle=data["subtitle"],
                price=Decimal(data["price"]),
                original_price=Decimal(data["original_price"]) if data["original_price"] else None,
                cover=data["cover"],
                flowers=data["flowers"],
                meaning=data["meaning"],
                category=data["category"],
                status=ProductStatus.ON.value,
                stock=999,
                sort_order=data["sort_order"],
            )
            session.add(product)

        await session.commit()

        # 统计
        result = await session.execute(select(Product))
        count = len(list(result.scalars().all()))

    logger.info("数据初始化完成", product_count=count)
    print(f"\n[seed] 商品 {count} 个已写入")
    print("[seed] 完成\n")


if __name__ == "__main__":
    asyncio.run(seed())
