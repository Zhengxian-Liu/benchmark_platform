"""add source_file_name and created_by to style_guide

Revision ID: 41e42a4ab87f
Revises: enhance_style_guide_model
Create Date: 2025-02-12 21:05:40.821986

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
# revision identifiers, used by Alembic.
revision: str = '41e42a4ab87f'
down_revision: Union[str, None] = 'enhance_style_guide_model'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Drop dependent tables first
        op.execute('DROP TABLE IF EXISTS evaluation_results')
        op.execute('DROP TABLE IF EXISTS translations')
        op.execute('DROP TABLE IF EXISTS session_languages')
        op.execute('DROP TABLE IF EXISTS session_texts')
        op.execute('DROP TABLE IF EXISTS session_style_guides')
        op.execute('DROP TABLE IF EXISTS style_guides')

        # Create tables with proper schemas
        op.create_table('style_guides',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_name', sa.String(), nullable=False),
            sa.Column('language_code', sa.String(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('source_file_name', sa.String(), nullable=False),
            sa.Column('guide_metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.String(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )

        op.create_table('session_texts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.Integer(), nullable=False),
            sa.Column('text_id', sa.String(), nullable=False),
            sa.Column('source_text', sa.String(), nullable=False),
            sa.Column('extra_data', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id']),
            sa.PrimaryKeyConstraint('id')
        )

        op.create_table('session_languages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.Integer(), nullable=False),
            sa.Column('language_code', sa.String(), nullable=False),
            sa.Column('prompts', sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id']),
            sa.PrimaryKeyConstraint('id')
        )

        op.create_table('translations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_text_id', sa.Integer(), nullable=False),
            sa.Column('session_language_id', sa.Integer(), nullable=False),
            sa.Column('translated_text', sa.String(), nullable=False),
            sa.Column('metrics', sa.JSON(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['session_text_id'], ['session_texts.id']),
            sa.ForeignKeyConstraint(['session_language_id'], ['session_languages.id']),
            sa.PrimaryKeyConstraint('id')
        )

        op.create_table('evaluation_results',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('translation_id', sa.Integer(), nullable=False),
            sa.Column('score', sa.Integer(), nullable=False),
            sa.Column('comments', sa.JSON(), nullable=True),
            sa.Column('metrics', sa.JSON(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['translation_id'], ['translations.id']),
            sa.PrimaryKeyConstraint('id')
        )

        # Update prompts table
        # Add columns to prompts
        op.drop_column('prompts', 'timestamp')
        op.drop_column('prompts', 'change_log')

        # Add new columns to prompts
        op.add_column('prompts', sa.Column('created_by', sa.String(), server_default='system', nullable=False))
        op.add_column('prompts', sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
        op.add_column('prompts', sa.Column('updated_by', sa.String(), nullable=True))
        op.add_column('prompts', sa.Column('updated_at', sa.DateTime(), nullable=True))

def downgrade() -> None:
    # This is a destructive upgrade that changes data formats
    # For safety, we don't implement downgrade
    pass
