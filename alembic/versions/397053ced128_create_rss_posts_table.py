"""create_rss_posts_table

Revision ID: 397053ced128
Revises:
Create Date: 2026-01-10 16:23:16.294603

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "397053ced128"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "rss_posts",
        sa.Column("link", sa.String(2048), primary_key=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("pub_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("media", sa.Text, nullable=True),
        sa.Column("is_processed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_event", sa.Boolean, nullable=True),
        sa.Column("classification_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("classified_at", sa.DateTime, nullable=True),
    )

    op.create_index("idx_rss_posts_link", "rss_posts", ["link"], unique=False)
    op.create_index("idx_rss_posts_is_processed", "rss_posts", ["is_processed"], unique=False)
    op.create_index("idx_rss_posts_is_event", "rss_posts", ["is_event"], unique=False)
    op.create_index("idx_rss_posts_created_at", "rss_posts", ["created_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("rss_posts")
