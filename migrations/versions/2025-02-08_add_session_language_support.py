"""add session language support

Revision ID: add_session_language_support
Revises: update_session_text_index
Create Date: 2025-02-08 21:26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
# revision identifiers
revision: str = 'add_session_language_support'
down_revision: Union[str, None] = 'update_session_text_index'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add new columns to sessions table
    op.add_column('sessions',
        sa.Column('languages_config', sa.JSON(), nullable=True)
    )
    op.add_column('sessions',
        sa.Column('source_languages', sa.JSON(), nullable=True)
    )
    op.add_column('sessions',
        sa.Column('target_languages', sa.JSON(), nullable=True)
    )

def downgrade() -> None:
    # Remove columns in reverse order
    op.drop_column('sessions', 'target_languages')
    op.drop_column('sessions', 'source_languages')
    op.drop_column('sessions', 'languages_config')
