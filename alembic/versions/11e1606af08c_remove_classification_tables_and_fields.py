"""remove_classification_tables_and_fields

Revision ID: 11e1606af08c
Revises: 7fbaf00cc52f
Create Date: 2026-01-21 22:20:51.956407

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "11e1606af08c"
down_revision: Union[str, Sequence[str], None] = "7fbaf00cc52f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop events table
    op.drop_table("events")

    # Drop openai_request_logs table
    op.drop_table("openai_request_logs")

    # Drop classification-related indexes from rss_posts
    op.drop_index("idx_rss_posts_is_processed", table_name="rss_posts")
    op.drop_index("idx_rss_posts_is_event", table_name="rss_posts")

    # Drop classification-related columns from rss_posts
    op.drop_column("rss_posts", "is_processed")
    op.drop_column("rss_posts", "is_event")
    op.drop_column("rss_posts", "classification_data")
    op.drop_column("rss_posts", "classified_at")


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate classification columns in rss_posts
    op.add_column(
        "rss_posts", sa.Column("is_processed", sa.Boolean, nullable=False, server_default="false")
    )
    op.add_column("rss_posts", sa.Column("is_event", sa.Boolean, nullable=True))
    op.add_column(
        "rss_posts", sa.Column("classification_data", sa.dialects.postgresql.JSONB, nullable=True)
    )
    op.add_column("rss_posts", sa.Column("classified_at", sa.DateTime, nullable=True))

    # Recreate indexes
    op.create_index("idx_rss_posts_is_processed", "rss_posts", ["is_processed"])
    op.create_index("idx_rss_posts_is_event", "rss_posts", ["is_event"])

    # Recreate openai_request_logs table
    op.create_table(
        "openai_request_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.String(255), nullable=True),
        sa.Column("custom_id", sa.String(255), nullable=True),
        sa.Column("request_type", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("request_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("response_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("tokens_used", sa.Integer, nullable=True),
        sa.Column("cost_estimate", sa.Numeric(10, 6), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("post_link", sa.String(2048), nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # Recreate events table
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
