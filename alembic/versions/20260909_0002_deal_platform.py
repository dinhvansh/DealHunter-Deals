"""deal engine, watchlist, verification and affiliate tables"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "20260909_0002"
down_revision = "20260909_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vouchers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("external_voucher_id", sa.String(160)),
        sa.Column("voucher_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("discount_type", sa.String(32), nullable=False),
        sa.Column("discount_value", sa.BigInteger(), nullable=False),
        sa.Column("max_discount", sa.BigInteger()),
        sa.Column("min_spend", sa.BigInteger(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True)),
        sa.Column("end_at", sa.DateTime(timezone=True)),
        sa.Column("stack_group", sa.String(64)),
        sa.Column("stackable", sa.Boolean()),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_vouchers_platform", "vouchers", ["platform"])

    op.create_table(
        "promotion_evaluations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("observed_price", sa.BigInteger(), nullable=False),
        sa.Column("estimated_price", sa.BigInteger(), nullable=False),
        sa.Column("applied_vouchers", sa.JSON(), nullable=False),
        sa.Column("rejected_vouchers", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_promo_eval_variant", "promotion_evaluations", ["variant_id"])

    op.create_table(
        "deal_scores",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("deal_score", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("opportunity_score", sa.Integer(), nullable=False),
        sa.Column("share_score", sa.Integer()),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_deal_scores_variant", "deal_scores", ["variant_id"])
    op.create_index("ix_deal_scores_opportunity", "deal_scores", ["opportunity_score"])

    op.create_table(
        "watchlists",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.String(160), nullable=False),
        sa.Column("variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("target_price", sa.BigInteger()),
        sa.Column("min_deal_score", sa.Integer()),
        sa.Column("verify_account", sa.Boolean(), nullable=False),
        sa.Column("alert_on_price_drop", sa.Boolean(), nullable=False),
        sa.Column("alert_on_new_voucher", sa.Boolean(), nullable=False),
        sa.Column("alert_on_historical_low", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "variant_id", name="uq_watch_user_variant"),
    )
    op.create_index("ix_watchlists_user", "watchlists", ["user_id"])
    op.create_index("ix_watchlists_variant", "watchlists", ["variant_id"])

    op.create_table(
        "verification_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.String(160)),
        sa.Column("variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("observed_price", sa.BigInteger(), nullable=False),
        sa.Column("estimated_price", sa.BigInteger()),
        sa.Column("verified_price", sa.BigInteger()),
        sa.Column("eligible_promotions", sa.JSON(), nullable=False),
        sa.Column("ineligible_promotions", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_verification_variant", "verification_runs", ["variant_id"])

    op.create_table(
        "affiliate_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id")),
        sa.Column("listing_id", sa.Uuid(), sa.ForeignKey("listings.id")),
        sa.Column("destination_url", sa.Text(), nullable=False),
        sa.Column("affiliate_url", sa.Text(), nullable=False),
        sa.Column("redirect_code", sa.String(32), nullable=False, unique=True),
        sa.Column("campaign", sa.String(160)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_affiliate_redirect", "affiliate_links", ["redirect_code"])

    op.create_table(
        "affiliate_clicks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("affiliate_link_id", sa.Uuid(), sa.ForeignKey("affiliate_links.id"), nullable=False),
        sa.Column("source", sa.String(80)),
        sa.Column("campaign", sa.String(160)),
        sa.Column("referrer", sa.Text()),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_affiliate_click_link", "affiliate_clicks", ["affiliate_link_id"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.String(160), nullable=False),
        sa.Column("variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("alert_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_alerts_user", "alerts", ["user_id"])
    op.create_index("ix_alerts_variant", "alerts", ["variant_id"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("affiliate_clicks")
    op.drop_table("affiliate_links")
    op.drop_table("verification_runs")
    op.drop_table("watchlists")
    op.drop_table("deal_scores")
    op.drop_table("promotion_evaluations")
    op.drop_table("vouchers")
