"""phase1 core marketplace tables"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "20260909_0001"
down_revision = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shops",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("external_shop_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(500)),
        sa.Column("seller_type", sa.String(64)),
        sa.Column("rating", sa.Float()),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("platform", "external_shop_id", name="uq_shop_platform_external"),
    )
    op.create_table(
        "listings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("external_item_id", sa.String(128), nullable=False),
        sa.Column("shop_id", sa.Uuid(), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("category_external_id", sa.String(128)),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "platform", "external_item_id", "shop_id", name="uq_listing_platform_item_shop"
        ),
    )
    op.create_table(
        "product_variants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("listing_id", sa.Uuid(), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("external_variation_id", sa.String(128), nullable=False),
        sa.Column("sku_text", sa.String(500)),
        sa.Column("variation_name", sa.String(1000), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "listing_id", "external_variation_id", name="uq_variant_listing_external"
        ),
    )
    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("observed_price", sa.BigInteger(), nullable=False),
        sa.Column("listed_price", sa.BigInteger()),
        sa.Column("sale_price", sa.BigInteger()),
        sa.Column("flash_price", sa.BigInteger()),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("stock_state", sa.String(64)),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("source_hash", sa.String(128)),
        sa.Column("raw_ref", sa.Text()),
    )
    op.create_index(
        "ix_price_variant_collected", "price_snapshots", ["variant_id", "collected_at"]
    )
    op.create_index("ix_price_collected", "price_snapshots", ["collected_at"])


def downgrade() -> None:
    op.drop_index("ix_price_collected", table_name="price_snapshots")
    op.drop_index("ix_price_variant_collected", table_name="price_snapshots")
    op.drop_table("price_snapshots")
    op.drop_table("product_variants")
    op.drop_table("listings")
    op.drop_table("shops")
