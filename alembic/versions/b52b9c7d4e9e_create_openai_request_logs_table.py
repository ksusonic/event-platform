"""create_openai_request_logs_table

Revision ID: b52b9c7d4e9e
Revises: fe1255139807
Create Date: 2026-01-17 18:56:06.252086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b52b9c7d4e9e'
down_revision: Union[str, Sequence[str], None] = 'fe1255139807'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "openai_request_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.String(255), nullable=True),
        sa.Column("custom_id", sa.String(255), nullable=True),
        sa.Column("request_type", sa.String(50), nullable=False),  # 'batch', 'completion', etc.
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("request_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("response_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(50), nullable=False),  # 'pending', 'completed', 'failed'
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("tokens_used", sa.Integer, nullable=True),
        sa.Column("cost_estimate", sa.Numeric(10, 6), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("post_link", sa.String(2048), nullable=True),  # Link to RSS post if applicable
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # Create indexes for common queries
    op.create_index("idx_openai_logs_batch_id", "openai_request_logs", ["batch_id"], unique=False)
    op.create_index("idx_openai_logs_custom_id", "openai_request_logs", ["custom_id"], unique=False)
    op.create_index("idx_openai_logs_status", "openai_request_logs", ["status"], unique=False)
    op.create_index("idx_openai_logs_created_at", "openai_request_logs", ["created_at"], unique=False)
    op.create_index("idx_openai_logs_post_link", "openai_request_logs", ["post_link"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("openai_request_logs")
