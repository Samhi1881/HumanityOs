"""initial database schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-06-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Since there are no application models in app/models (only Base/TimestampMixin),
    # this acts as a baseline migration.
    pass


def downgrade() -> None:
    pass
