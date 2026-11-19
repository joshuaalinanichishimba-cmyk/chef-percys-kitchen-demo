from alembic import context

from app.database import get_engine
from app.models import Base


def run_migrations() -> None:
    engine = get_engine()
    if context.is_offline_mode():
        context.configure(url=engine.url, target_metadata=Base.metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
        return

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations()
