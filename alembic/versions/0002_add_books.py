"""add books and book_uploads tables

Revision ID: 0002_add_books
Revises: 0001_init_documents
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_books"
down_revision = "0001_init_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("isbn", sa.String(50), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("author", sa.String(500), nullable=True),
        sa.Column("publisher", sa.String(500), nullable=True),
        sa.Column("edition", sa.String(100), nullable=True),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("upload_count", sa.Integer(), default=1),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash"),
    )
    op.create_index("ix_books_isbn", "books", ["isbn"])
    op.create_index("ix_books_content_hash", "books", ["content_hash"])

    op.create_table(
        "book_uploads",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("pdf_id", sa.String(255), nullable=False),
        sa.Column("book_id", sa.String(36), nullable=False),
        sa.Column("pdf_url", sa.Text(), nullable=True),
        sa.Column("txt_url", sa.Text(), nullable=True),
        sa.Column("upload_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pdf_id"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
    )
    op.create_index("ix_book_uploads_pdf_id", "book_uploads", ["pdf_id"])
    op.create_index("ix_book_uploads_book_id", "book_uploads", ["book_id"])
    op.create_index("ix_book_uploads_upload_date", "book_uploads", ["upload_date"])


def downgrade() -> None:
    op.drop_table("book_uploads")
    op.drop_table("books")
