from __future__ import annotations

import logging

from alembic.config import Config
from sqlalchemy import inspect

from alembic import command
from bd.logging import get_console
from config import DATABASE_PATH, DATABASE_URL, RESOURCE_DIR

console = get_console()
logger = logging.getLogger(__name__)

ALEMBIC_INI_PATH = RESOURCE_DIR / "alembic.ini"
ALEMBIC_SCRIPT_LOCATION = RESOURCE_DIR / "alembic"
APP_TABLES = {
    "user",
    "movimiento",
    "tipo",
    "sesion",
    "cuenta",
    "tipocuenta",
    "moneda",
    "subtipo",
    "entidad",
    "deuda",
    "pagodeuda",
}


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


def _has_column(table: str, column: str) -> bool:
    if table not in existing_tables():
        return False

    from bd.database import engine

    return column in {col["name"] for col in inspect(engine).get_columns(table)}


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
        baseline = (
            "20260704_0002_add_descripcion"
            if _has_column("movimiento", "descripcion")
            else "20260629_0001_initial_schema"
        )
        console.print(
            "[cyan]  -> Base legacy detectada; marcando baseline "
            f"{baseline}...[/cyan]"
        )
        command.stamp(config, baseline)
        console.print("[cyan]  -> Aplicando migraciones pendientes...[/cyan]")
        command.upgrade(config, "head")
        console.print("[green]  -> Migraciones aplicadas.[/green]")
        return

    console.print("[cyan]  -> Aplicando migraciones pendientes...[/cyan]")
    command.upgrade(config, "head")
    console.print("[green]  -> Migraciones aplicadas.[/green]")
