"""add demo flags

Revision ID: a1b2c3d4e5f6
Revises: 466482d0f9f1
Create Date: 2026-10-21

【干什么】
给 products 和 orders 加 is_demo 字段，标记演示数据。

【为什么】
交付环境的数据是测试桩，老板接手后要能一键清掉。
加个标记比按 ID 删更可靠。
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = '466482d0f9f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """加字段"""
    op.add_column(
        "products",
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_products_is_demo", "products", ["is_demo"])

    op.add_column(
        "orders",
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_orders_is_demo", "orders", ["is_demo"])


def downgrade() -> None:
    """回滚：删字段"""
    op.drop_index("ix_orders_is_demo", table_name="orders")
    op.drop_column("orders", "is_demo")

    op.drop_index("ix_products_is_demo", table_name="products")
    op.drop_column("products", "is_demo")
