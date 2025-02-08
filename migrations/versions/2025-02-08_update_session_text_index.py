"""update session text index

Revision ID: update_session_text_index
Revises: add_text_id_index
Create Date: 2025-02-08 19:04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'update_session_text_index'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

from sqlalchemy import text, Column, Integer, String, Text, ForeignKey, JSON

def upgrade() -> None:
    # Create sessions table first
    op.create_table(
        'sessions',
        Column('id', Integer, primary_key=True, index=True),
        Column('project_name', String, index=True),
        Column('created_at', Text),
        Column('source_file_name', String),
        Column('status', String)
    )
    
    # Create session_texts table
    op.create_table(
        'session_texts',
        Column('id', Integer, primary_key=True, index=True),
        Column('session_id', Integer, ForeignKey('sessions.id')),
        Column('text_id', String, nullable=False),
        Column('source_text', Text),
        Column('extra_data', Text),
        Column('ground_truth', JSON)
    )
    
    # Create composite unique index
    op.create_index(
        'ix_session_texts_session_text_id',
        'session_texts',
        ['session_id', 'text_id'],
        unique=True
    )

def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_session_texts_session_text_id', table_name='session_texts')
    op.drop_table('session_texts')
    op.drop_table('sessions')