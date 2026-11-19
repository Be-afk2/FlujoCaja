from sqlalchemy import event
from sqlmodel import SQLModel, create_engine

from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 5},
)


@event.listens_for(engine, "connect")
def _configurar_sqlite(dbapi_connection, _connection_record) -> None:
    """Configura cada conexión SQLite usada por el threadpool de Uvicorn."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def init_db():
    SQLModel.metadata.create_all(engine)

