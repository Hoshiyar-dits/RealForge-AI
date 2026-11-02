"""add ingest progress to documents

Revision ID: c7d2e8f1a9b3
Revises: b3f1c2d4e5a6
Create Date: 2026-11-02 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d2e8f1a9b3'
down_revision: Union[str, Sequence[str], None] = 'b3f1c2d4e5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('documents', sa.Column('pages_done', sa.Integer(), server_default='0', nullable=False))
    op.add_column('documents', sa.Column('pages_total', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('documents', 'pages_total')
    op.drop_column('documents', 'pages_done')
