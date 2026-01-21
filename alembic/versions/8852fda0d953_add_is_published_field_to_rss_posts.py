"""add_is_published_field_to_rss_posts

Revision ID: 8852fda0d953
Revises: 11e1606af08c
Create Date: 2026-01-21 23:16:05.846464

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8852fda0d953"
down_revision: Union[str, Sequence[str], None] = "11e1606af08c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_published column
    op.add_column(
        "rss_posts",
        sa.Column("is_published", sa.Boolean, nullable=False, server_default="false"),
    )

    # Add published_at column to track when post was published
    op.add_column(
        "rss_posts",
        sa.Column("published_at", sa.DateTime, nullable=True),
    )

    # Create index for faster filtering of unpublished posts
    op.create_index("idx_rss_posts_is_published", "rss_posts", ["is_published"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.drop_index("idx_rss_posts_is_published", table_name="rss_posts")

    # Drop columns
    op.drop_column("rss_posts", "published_at")
    op.drop_column("rss_posts", "is_published")
