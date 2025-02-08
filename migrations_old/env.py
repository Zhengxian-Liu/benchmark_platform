from logging.config import fileConfig
from sqlalchemy import create_engine
import sys
from pathlib import Path
from alembic import context
sys.path.append(str(Path(__file__).resolve().parent.parent))
from models import Base

config = context.config
target_metadata = Base.metadata
fileConfig(config.config_file_name)
engine = create_engine(config.get_main_option("sqlalchemy.url"))

def run_migrations_online():
    connectable = engine
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()