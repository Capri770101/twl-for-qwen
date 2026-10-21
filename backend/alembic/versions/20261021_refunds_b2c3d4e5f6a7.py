"""add refunds table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-21

【干什么】
新增退款单表。

【为什么单独一张表】
一笔订单可以退多次（部分退款、分次退款）。
放在订单表上只能记一个数，记不了流水。
"""

from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refunds",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("refund_no", sa.String(32), nullable=False, unique=True),
        sa.Column("order_no", sa.String(32), nullable=False),
        sa.Column("ticket_no", sa.String(32), nullable=True),
        sa.Column("user_id", sa.String(40), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("order_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("reject_reason", sa.String(500), nullable=True),
        sa.Column("channel", sa.String(20), nullable=True),
        sa.Column("external_ref", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("operator", sa.String(50), nullable=True),
        sa.Column("applied_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("refunded_at", sa.DateTime(), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        # Base 基类的两个时间戳
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        comment="退款单表",
    )
    op.create_index("ix_refunds_refund_no", "refunds", ["refund_no"], unique=True)
    op.create_index("ix_refunds_order_no", "refunds", ["order_no"])
    op.create_index("ix_refunds_ticket_no", "refunds", ["ticket_no"])
    op.create_index("ix_refunds_user_id", "refunds", ["user_id"])
    op.create_index("ix_refunds_status", "refunds", ["status"])
    op.create_index("ix_refunds_is_demo", "refunds", ["is_demo"])
    op.create_index("idx_refunds_order_status", "refunds", ["order_no", "status"])


def downgrade() -> None:
    op.drop_table("refunds")
