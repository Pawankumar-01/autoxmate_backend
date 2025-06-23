"""Initial migration

Revision ID: 8240886b63a1
Revises: d2bf685339e0
Create Date: 2025-06-19 18:32:31.130871

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8240886b63a1'
down_revision: Union[str, Sequence[str], None] = 'd2bf685339e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
