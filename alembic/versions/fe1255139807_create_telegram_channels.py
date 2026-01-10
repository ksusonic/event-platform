"""create_telegram_channels

Revision ID: fe1255139807
Revises: 397053ced128
Create Date: 2026-01-10 17:12:48.741333

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fe1255139807"
down_revision: Union[str, Sequence[str], None] = "397053ced128"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "telegram_channels",
        sa.Column("channel_id", sa.BigInteger, primary_key=True),
        sa.Column("channel_name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("url", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_telegram_channels_channel_name", "telegram_channels", ["channel_name"], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_telegram_channels_channel_name", table_name="telegram_channels")
    op.drop_table("telegram_channels")
