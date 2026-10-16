"""add local accounts, sessions and ticket ownership

Revision ID: 20261016_0004
Revises: 20261016_0003
Create Date: 2026-10-16 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20261016_0004"
down_revision = "20261016_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=24), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    for col in ("id", "username", "email", "role"):
        op.create_index(f"ix_users_{col}", "users", [col], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    for col in ("id", "user_id", "token_hash", "expires_at"):
        op.create_index(f"ix_auth_sessions_{col}", "auth_sessions", [col], unique=False)

    op.add_column("tickets", sa.Column("created_by_user_id", sa.Integer(), nullable=True))
    op.add_column("tickets", sa.Column("technician_response", sa.Text(), nullable=True))
    op.add_column("tickets", sa.Column("response_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tickets", sa.Column("response_reviewed_by_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_tickets_created_by_user", "tickets", "users", ["created_by_user_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_tickets_response_reviewer", "tickets", "users", ["response_reviewed_by_user_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_tickets_created_by_user_id", "tickets", ["created_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tickets_created_by_user_id", table_name="tickets")
    op.drop_constraint("fk_tickets_response_reviewer", "tickets", type_="foreignkey")
    op.drop_constraint("fk_tickets_created_by_user", "tickets", type_="foreignkey")
    for col in ("response_reviewed_by_user_id", "response_sent_at", "technician_response", "created_by_user_id"):
        op.drop_column("tickets", col)
    for col in ("expires_at", "token_hash", "user_id", "id"):
        op.drop_index(f"ix_auth_sessions_{col}", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    for col in ("role", "email", "username", "id"):
        op.drop_index(f"ix_users_{col}", table_name="users")
    op.drop_table("users")
