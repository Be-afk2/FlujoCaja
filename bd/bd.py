import logging
from rich.console import Console
from bd.database import init_db
from bd.bootstrap import bootstrap_db
from config import DATABASE_PATH

console = Console()
logger = logging.getLogger(__name__)

def comprobar_y_crear_bd():
    if not DATABASE_PATH.exists():
        console.print("[yellow]La base de datos no existe. Creando base de datos...[/yellow]")
        bootstrap_db()
        console.print("[green]Base de datos creada exitosamente.[/green]")
    else:
        console.print("[green]La base de datos ya existe. Continuando normalmente.[/green]")

def comprobar_conexion():
    try:
        # Intentar conectarse a la base de datos
        init_db()
        logger.info("Conexión a la base de datos exitosa")
        console.clear()
    except Exception as e:
        logger.error("Error al conectar a la base de datos: %s", e)
