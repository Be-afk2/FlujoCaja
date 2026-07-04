from __future__ import annotations

import logging

from alembic import command
from alembic.config import Config
from rich.console import Console
from sqlalchemy import inspect

from config import DATABASE_PATH, DATABASE_URL, PROJECT_ROOT

console = Console()
logger = logging.getLogger(__name__)

ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"
ALEMBIC_SCRIPT_LOCATION = PROJECT_ROOT / "alembic"
APP_TABLES = {"user", "movimiento", "tipo", "sesion", "cuenta", "tipocuenta", "moneda", "subtipo"}


def _build_alembic_config() -> Config:
    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option("script_location", str(ALEMBIC_SCRIPT_LOCATION))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    return config


def existing_tables() -> set[str]:
    if not DATABASE_PATH.exists():
        return set()

    from bd.database import engine

    return set(inspect(engine).get_table_names())


def apply_database_migrations() -> None:
    """Apply Alembic migrations or stamp a legacy schema."""
    config = _build_alembic_config()
    tablas = existing_tables()

    if not tablas:
        console.print("[cyan]  -> Aplicando migraciones sobre base vacia...[/cyan]")
        command.upgrade(config, "head")
        console.print("[green]  -> Migraciones aplicadas.[/green]")
        return

    if "alembic_version" not in tablas and tablas & APP_TABLES:
        console.print("[cyan]  -> Base legacy detectada; marcando baseline de Alembic...[/cyan]")
        command.stamp(config, "head")
        console.print("[green]  -> Baseline marcado.[/green]")
        return

    console.print("[cyan]  -> Aplicando migraciones pendientes...[/cyan]")
    command.upgrade(config, "head")
    console.print("[green]  -> Migraciones aplicadas.[/green]")
