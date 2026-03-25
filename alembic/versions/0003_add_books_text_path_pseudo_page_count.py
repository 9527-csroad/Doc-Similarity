"""add books text_path and pseudo_page_count

Revision ID: 0003_books_text_path
Revises: 0002_add_books
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa

revision = "0003_books_text_path"
down_revision = "0002_add_books"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("books", sa.Column("text_path", sa.String(512), nullable=True))
    op.add_column("books", sa.Column("pseudo_page_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("books", "pseudo_page_count")
    op.drop_column("books", "text_path")
