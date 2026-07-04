from __future__ import annotations

import logging

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from config import DATABASE_PATH, DATABASE_URL, PROJECT_ROOT

logger = logging.getLogger(__name__)

ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"
ALEMBIC_SCRIPT_LOCATION = PROJECT_ROOT / "alembic"
APP_TABLES = {"user", "movimiento", "tipo", "sesion", "cuenta", "tipocuenta", "moneda", "subtipo"}


def _build_alembic_config() -> Config:
    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option("script_location", str(ALEMBIC_SCRIPT_LOCATION))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    return config


def _existing_tables() -> set[str]:
    if not DATABASE_PATH.exists():
        return set()

    from bd.database import engine

    return set(inspect(engine).get_table_names())


def apply_database_migrations() -> None:
    """Apply Alembic migrations or stamp a legacy schema."""
    config = _build_alembic_config()
    existing_tables = _existing_tables()

    if not existing_tables:
        logger.info("Aplicando migraciones sobre base vacia")
        command.upgrade(config, "head")
        return

    if "alembic_version" not in existing_tables and existing_tables & APP_TABLES:
        logger.info("Base legacy detectada; marcando baseline de Alembic")
        command.stamp(config, "head")
        return

    logger.info("Aplicando migraciones pendientes")
    command.upgrade(config, "head")
