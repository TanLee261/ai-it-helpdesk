"""create knowledge tables

Revision ID: 20261013_0002
Revises: 20261013_0001
Create Date: 2026-10-13 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20261013_0002"
down_revision = "20261013_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source", sa.String(length=500), nullable=False),
        sa.Column("service", sa.String(length=80), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=True),
        sa.Column("version", sa.String(length=40), nullable=True),
        sa.Column("access_scope", sa.String(length=80), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", name="uq_knowledge_documents_document_id"),
    )
    op.create_index(op.f("ix_knowledge_documents_id"), "knowledge_documents", ["id"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_document_id"), "knowledge_documents", ["document_id"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_source_type"), "knowledge_documents", ["source_type"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_service"), "knowledge_documents", ["service"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_category"), "knowledge_documents", ["category"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_access_scope"), "knowledge_documents", ["access_scope"], unique=False)

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.String(length=100), nullable=False),
        sa.Column("document_id", sa.String(length=80), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("qdrant_point_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.document_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id", name="uq_knowledge_chunks_chunk_id"),
    )
    op.create_index(op.f("ix_knowledge_chunks_id"), "knowledge_chunks", ["id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunks_chunk_id"), "knowledge_chunks", ["chunk_id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunks_document_id"), "knowledge_chunks", ["document_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_chunks_document_id"), table_name="knowledge_chunks")
    op.drop_index(op.f("ix_knowledge_chunks_chunk_id"), table_name="knowledge_chunks")
    op.drop_index(op.f("ix_knowledge_chunks_id"), table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")

    op.drop_index(op.f("ix_knowledge_documents_access_scope"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_category"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_service"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_source_type"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_document_id"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_id"), table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
