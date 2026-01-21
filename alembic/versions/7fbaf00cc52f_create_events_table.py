"""create_events_table

Revision ID: 7fbaf00cc52f
Revises: b52b9c7d4e9e
Create Date: 2026-01-17 21:37:52.515826

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7fbaf00cc52f"
down_revision: Union[str, Sequence[str], None] = "b52b9c7d4e9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("post_link", sa.String(2048), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("event_date", sa.DateTime, nullable=True),
        sa.Column("event_date_is_approximate", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("additional_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )

    # Create indexes
    op.create_index("idx_events_post_link", "events", ["post_link"], unique=False)
    op.create_index("idx_events_event_date", "events", ["event_date"], unique=False)
    op.create_index("idx_events_event_type", "events", ["event_type"], unique=False)
    op.create_index("idx_events_created_at", "events", ["created_at"], unique=False)

    # Create foreign key to rss_posts
    op.create_foreign_key(
        "fk_events_post_link", "events", "rss_posts", ["post_link"], ["link"], ondelete="CASCADE"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("events")
