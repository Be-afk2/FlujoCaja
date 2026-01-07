from bd.database import init_db
from bd.crud.user import *
import questionary
import bcrypt
from rich.console import Console

console = Console()

def comprobar_conexion():
    try:
        # Intentar conectarse a la base de datos
        init_db()
        print("Conexión a la base de datos exitosa.")
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")

comprobar_conexion()

userId = None
userConnect = None

while True:
    name = questionary.text("Nombre:").ask()
    passw = questionary.password("Contraseña:").ask()
    estado , user = login_user(name, passw)
    if estado:
        console.clear()
        print(f"Bienvenido {user.name} {user.apellido}")
        userId = user.id
        userConnect = user
        break
    else:
        console.clear()
        print("Nombre o contraseña incorrecta. Inténtalo de nuevo.")



while True:
    answer = questionary.select(
        "¿Qué deseas hacer?",
        choices=[
            "Crear usuario",
            "Salir"
        ]
    ).ask()

    if answer == "Crear usuario":
        name = questionary.text("Nombre:").ask()
        apellido = questionary.text("Apellido:").ask()
        passw = questionary.password("Contraseña:").ask()

        user = crear_usuario(name, apellido, passw)
        print(f"Usuario creado: {user.id} - {user.name} {user.apellido}")

    elif answer == "Salir":
        print("Saliendo...")
        break

#
#from rich.table import Table
#from rich.console import Console

#console = Console()

#table = Table(title="Usuarios")

#table.add_column("ID", justify="right")
#table.add_column("Nombre")
#table.add_column("Edad", justify="center")

#table.add_row("1", "Ana", "28")
#table.add_row("2", "Benja", "32")

#console.print(table)#

