import logging
import shutil
from bd.database import init_db
from bd.bootstrap import bootstrap_db
from bd.logging import get_console
from bd.migrations import existing_tables, APP_TABLES
from config import DATABASE_PATH, DATA_DIR, EXE_DIR

console = get_console()
logger = logging.getLogger(__name__)


def _migrar_db_legacy():
    """Copia database.db del directorio de la app (junto al exe en prod, raíz en dev)
    a DATA_DIR si existe allá pero no acá."""
    legacy = EXE_DIR / "database.db"
    if legacy.exists() and not DATABASE_PATH.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy, DATABASE_PATH)
        logger.info("Base migrada de %s a %s", legacy, DATABASE_PATH)


def _tablas_completas(tablas: set[str]) -> bool:
    """Retorna True si estan presentes todas las tablas de la aplicacion."""
    return APP_TABLES.issubset(tablas)


def comprobar_y_crear_bd():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _migrar_db_legacy()

    tablas = existing_tables()

    if not tablas:
        console.print("[yellow]Base de datos no encontrada. Creando desde cero...[/yellow]")
        bootstrap_db()
        console.print("[green]Base de datos creada exitosamente.[/green]")
    elif not _tablas_completas(tablas):
        console.print("[yellow]Base de datos incompleta. Ejecutando migraciones pendientes...[/yellow]")
        bootstrap_db()
        console.print("[green]Base de datos actualizada correctamente.[/green]")
    else:
        console.print("[green]Base de datos lista. Continuando normalmente.[/green]")

