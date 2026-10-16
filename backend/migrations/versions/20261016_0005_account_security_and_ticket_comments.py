"""add lockout controls and ticket comments

Revision ID: 20261016_0005
Revises: 20261016_0004
Create Date: 2026-10-16 13:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20261016_0005"
down_revision = "20261016_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "ticket_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("user_name", sa.String(length=160), nullable=False),
        sa.Column("user_role", sa.String(length=24), nullable=False),
        sa.Column("comment_type", sa.String(length=32), nullable=False, server_default="comment"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.ticket_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_comments_id", "ticket_comments", ["id"], unique=False)
    op.create_index("ix_ticket_comments_ticket_id", "ticket_comments", ["ticket_id"], unique=False)
    op.create_index("ix_ticket_comments_user_id", "ticket_comments", ["user_id"], unique=False)
    op.create_index("ix_ticket_comments_created_at", "ticket_comments", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ticket_comments_created_at", table_name="ticket_comments")
    op.drop_index("ix_ticket_comments_user_id", table_name="ticket_comments")
    op.drop_index("ix_ticket_comments_ticket_id", table_name="ticket_comments")
    op.drop_index("ix_ticket_comments_id", table_name="ticket_comments")
    op.drop_table("ticket_comments")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
