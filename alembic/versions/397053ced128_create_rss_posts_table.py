"""create_rss_posts_table

Revision ID: 397053ced128
Revises:
Create Date: 2026-01-10 16:23:16.294603

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "397053ced128"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS rss_posts (
            link VARCHAR(2048) PRIMARY KEY,
            content TEXT NOT NULL,
            pub_date TIMESTAMP,
            media TEXT,
            is_processed BOOLEAN DEFAULT FALSE NOT NULL,
            is_event BOOLEAN,
            classification_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            classified_at TIMESTAMP
        )
    """)

    # Create indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_rss_posts_link ON rss_posts(link)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rss_posts_is_processed ON rss_posts(is_processed)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rss_posts_is_event ON rss_posts(is_event)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rss_posts_created_at ON rss_posts(created_at)")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("rss_posts")
