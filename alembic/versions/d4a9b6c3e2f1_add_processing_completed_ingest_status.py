"""add processing and completed ingest status

Revision ID: d4a9b6c3e2f1
Revises: c7d2e8f1a9b3
Create Date: 2026-11-02 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4a9b6c3e2f1'
down_revision: Union[str, Sequence[str], None] = 'c7d2e8f1a9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

old_status = sa.Enum('pending', 'ingested', 'failed')
all_status = sa.Enum('pending', 'ingested', 'processing', 'completed', 'failed')
new_status = sa.Enum('pending', 'processing', 'completed', 'failed')


def upgrade() -> None:
    """Upgrade schema."""
    # widen first so existing "ingested" rows can be renamed to "completed"
    op.alter_column('documents', 'ingest_status', existing_type=old_status, type_=all_status, existing_nullable=False)
    op.execute("UPDATE documents SET ingest_status = 'completed' WHERE ingest_status = 'ingested'")
    op.alter_column('documents', 'ingest_status', existing_type=all_status, type_=new_status, existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('documents', 'ingest_status', existing_type=new_status, type_=all_status, existing_nullable=False)
    op.execute("UPDATE documents SET ingest_status = 'ingested' WHERE ingest_status = 'completed'")
    op.execute("UPDATE documents SET ingest_status = 'pending' WHERE ingest_status = 'processing'")
    op.alter_column('documents', 'ingest_status', existing_type=all_status, type_=old_status, existing_nullable=False)
