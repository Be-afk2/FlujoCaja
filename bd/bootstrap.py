import logging

from bd.models import Cuenta, Moneda, Registro, Sesion, Subtipo, Tipo, TipoCuenta, User
from bd.migrations import apply_database_migrations
from bd.seeds import seed_db

logger = logging.getLogger(__name__)


def bootstrap_db() -> None:
    # Importar los modelos asegura que SQLModel registre todas las tablas para Alembic.
    _ = (User, Registro, Tipo, Sesion, Cuenta, TipoCuenta, Moneda, Subtipo)

    apply_database_migrations()
    seed_db()
    logger.info("Base de datos migrada y sembrada correctamente")
