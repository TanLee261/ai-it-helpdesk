"""create tickets table

Revision ID: 20261013_0001
Revises:
Create Date: 2026-10-13 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20261013_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.String(length=32), nullable=False),
        sa.Column("source_ticket_id", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("service", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("raw_category", sa.String(length=80), nullable=True),
        sa.Column("sub_category", sa.String(length=120), nullable=True),
        sa.Column("priority", sa.String(length=8), nullable=False),
        sa.Column("impact", sa.String(length=16), nullable=False),
        sa.Column("urgency", sa.String(length=16), nullable=False),
        sa.Column("assigned_team", sa.String(length=120), nullable=True),
        sa.Column("auto_resolve", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("requester_email_redacted", sa.String(length=255), nullable=True),
        sa.Column("verified_root_cause", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id", name="uq_tickets_ticket_id"),
    )
    op.create_index(op.f("ix_tickets_id"), "tickets", ["id"], unique=False)
    op.create_index(op.f("ix_tickets_ticket_id"), "tickets", ["ticket_id"], unique=False)
    op.create_index(op.f("ix_tickets_service"), "tickets", ["service"], unique=False)
    op.create_index(op.f("ix_tickets_category"), "tickets", ["category"], unique=False)
    op.create_index(op.f("ix_tickets_priority"), "tickets", ["priority"], unique=False)
    op.create_index(op.f("ix_tickets_status"), "tickets", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tickets_status"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_priority"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_category"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_service"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_ticket_id"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_id"), table_name="tickets")
    op.drop_table("tickets")
