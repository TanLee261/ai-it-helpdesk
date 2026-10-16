"""add persisted approval and audit records

Revision ID: 20261016_0003
Revises: 20261013_0002
Create Date: 2026-10-16 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20261016_0003"
down_revision = "20261013_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("approval_id", sa.String(length=40), nullable=False),
        sa.Column("ticket_id", sa.String(length=32), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("requested_by", sa.String(length=120), nullable=False),
        sa.Column("decided_by", sa.String(length=120), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("approval_id", name="uq_approval_requests_approval_id"),
    )
    for column in ("id", "approval_id", "ticket_id", "status"):
        op.create_index(f"ix_approval_requests_{column}", "approval_requests", [column], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=40), nullable=False),
        sa.Column("actor_id", sa.String(length=120), nullable=False),
        sa.Column("actor_role", sa.String(length=24), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=40), nullable=False),
        sa.Column("resource_id", sa.String(length=120), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    for column in ("id", "event_id", "actor_id", "action", "resource_type", "resource_id", "created_at"):
        op.create_index(f"ix_audit_events_{column}", "audit_events", [column], unique=False)


def downgrade() -> None:
    for column in ("created_at", "resource_id", "resource_type", "action", "actor_id", "event_id", "id"):
        op.drop_index(f"ix_audit_events_{column}", table_name="audit_events")
    op.drop_table("audit_events")
    for column in ("status", "ticket_id", "approval_id", "id"):
        op.drop_index(f"ix_approval_requests_{column}", table_name="approval_requests")
    op.drop_table("approval_requests")
