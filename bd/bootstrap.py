import logging

from bd.migrations import apply_database_migrations
from bd.models import (
    Cuenta,
    Deuda,
    Entidad,
    Moneda,
    Movimiento,
    PagoDeuda,
    Sesion,
    Subtipo,
    Tipo,
    TipoCuenta,
    User,
)
from bd.seeds import seed_db

logger = logging.getLogger(__name__)


def bootstrap_db() -> None:
    # Importar los modelos asegura que SQLModel registre todas las tablas para Alembic.
    _ = (
        User,
        Movimiento,
        Tipo,
        Sesion,
        Cuenta,
        TipoCuenta,
        Moneda,
        Subtipo,
        Entidad,
        Deuda,
        PagoDeuda,
    )

    apply_database_migrations()
    seed_db()
    logger.info("Base de datos migrada y sembrada correctamente")
