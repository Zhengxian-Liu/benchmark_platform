"""enhance_style_guide_model

Revision ID: enhance_style_guide_model
Revises: d087ef7a61fc
Create Date: 2025-02-11 10:29:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enhance_style_guide_model'
down_revision = 'd087ef7a61fc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to style_guides table
    op.add_column('style_guides', sa.Column('file_name', sa.String(), nullable=True))
    op.add_column('style_guides', sa.Column('file_hash', sa.String(), nullable=True))
    op.add_column('style_guides', sa.Column('status', sa.String(), nullable=True))
    op.add_column('style_guides', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('style_guides', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('style_guides', sa.Column('created_by', sa.String(), nullable=True))
    
    # Create unique index for project_name, language_code, version
    op.create_index('ix_style_guides_project_lang_ver', 'style_guides',
                    ['project_name', 'language_code', 'version'], unique=True)
    
    # Create session_style_guides association table
    op.create_table('session_style_guides',
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('style_guide_id', sa.Integer(), nullable=False),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.ForeignKeyConstraint(['style_guide_id'], ['style_guides.id'], ),
        sa.PrimaryKeyConstraint('session_id', 'style_guide_id')
    )


def downgrade() -> None:
    # Drop session_style_guides table
    op.drop_table('session_style_guides')
    
    # Drop index
    op.drop_index('ix_style_guides_project_lang_ver', table_name='style_guides')
    
    # Drop new columns from style_guides
    op.drop_column('style_guides', 'created_by')
    op.drop_column('style_guides', 'updated_at')
    op.drop_column('style_guides', 'created_at')
    op.drop_column('style_guides', 'status')
    op.drop_column('style_guides', 'file_hash')
    op.drop_column('style_guides', 'file_name')