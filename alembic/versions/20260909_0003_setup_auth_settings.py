"""first-run setup, authentication and integration settings"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "20260909_0003"
down_revision = "20260909_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "setup_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("complete", sa.Boolean(), nullable=False),
        sa.Column("app_url", sa.Text()),
        sa.Column("timezone", sa.String(80), nullable=False),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "admin_users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("admin_users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])

    op.create_table(
        "integration_configs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("provider", sa.String(80)),
        sa.Column("base_url", sa.Text()),
        sa.Column("model_name", sa.String(200)),
        sa.Column("secret_encrypted", sa.Text()),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("kind", "name", name="uq_integration_kind_name"),
    )
    op.create_index("ix_integration_configs_kind", "integration_configs", ["kind"])

    op.create_table(
        "marketplace_accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("profile_dir", sa.Text(), nullable=False),
        sa.Column("browser_login_url", sa.Text()),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("account_hint", sa.String(200)),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("platform", "label", name="uq_marketplace_platform_label"),
    )
    op.create_index("ix_marketplace_accounts_platform", "marketplace_accounts", ["platform"])


def downgrade() -> None:
    op.drop_index("ix_marketplace_accounts_platform", table_name="marketplace_accounts")
    op.drop_table("marketplace_accounts")
    op.drop_index("ix_integration_configs_kind", table_name="integration_configs")
    op.drop_table("integration_configs")
    op.drop_index("ix_auth_sessions_expires_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_token_hash", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index("ix_admin_users_email", table_name="admin_users")
    op.drop_table("admin_users")
    op.drop_table("setup_state")
