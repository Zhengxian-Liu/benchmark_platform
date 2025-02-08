from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_index('ix_session_texts_text_id', 'session_texts', ['text_id'], unique=False)

def downgrade():
    op.drop_index('ix_session_texts_text_id', 'session_texts')