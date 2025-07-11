import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import dotenv_values
import os
from models import SQLModel
from models import Contact,MessageRequest,Message,WhatsAppConfig,MessageStatus,Template,TemplateType,TemplateCreate,SendMessageRequest,CampaignCreate,MessageDirection
target_metadata = SQLModel.metadata
from dotenv import load_dotenv
load_dotenv()
env = dotenv_values(".env")
os.environ.update(env)

# ---------------- CONFIG ------------------
config = context.config
fileConfig(config.config_file_name)

# ✅ Use sync DB URL (not asyncpg, Alembic can’t use async engines)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set in .env")

sync_url = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
config.set_main_option("sqlalchemy.url", sync_url)

# ---------------- METADATA ------------------

# ---------------- OFFLINE MODE ------------------
def run_migrations_offline():
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

# ---------------- ONLINE MODE ------------------
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

# ---------------- ENTRYPOINT ------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

