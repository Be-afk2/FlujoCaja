from bd.database import init_db
from rich.console import Console
import os

console = Console()

def comprobar_y_crear_bd():
    db_path = "database.db"
    if not os.path.exists(db_path):
        console.print("[yellow]La base de datos no existe. Creando base de datos...[/yellow]")
        init_db()
        console.print("[green]Base de datos creada exitosamente.[/green]")
    else:
        console.print("[green]La base de datos ya existe. Continuando normalmente.[/green]")

def comprobar_conexion():
    try:
        # Intentar conectarse a la base de datos
        init_db()
        print("Conexión a la base de datos exitosa.")
        console.clear()
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")

comprobar_y_crear_bd()
print("----------------------------------------")