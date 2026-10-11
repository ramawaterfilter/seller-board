from alembic import context
from app.settings import Settings
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

settings = Settings()
if settings.database_url is None:
    raise RuntimeError("RCI_DATABASE_URL is required for migrations.")
url = settings.database_url.get_secret_value()

if context.is_offline_mode():
    context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=NullPool, hide_parameters=True,
                           connect_args={"connect_timeout": 5})
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
