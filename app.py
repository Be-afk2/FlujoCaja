from re import match
from sqlalchemy import case
from bd.database import init_db
from bd.crud.user import *
import questionary
from bd.crud.sesion import *
from rich.panel import Panel
from rich.align import Align
from bd.crud.tipo import *
from rich.console import Console
import menus.path as path_interno
from menus.principal import menu_principal
import widget.widget as widget
console = Console()


userId = None
userConnect = get_sesion()


def guardarsesion(user_id: str):
    guardar_sesion_bd(user_id)

def comprobar_conexion():
    try:
        # Intentar conectarse a la base de datos
        init_db()
        print("Conexión a la base de datos exitosa.")
        console.clear()
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")

def Login():
    while True:
        name = questionary.text("Nombre:").ask()
        passw = questionary.password("Contraseña:").ask()
        recoradar =questionary.confirm("Recordar Sesion?").ask()

        print(recoradar)
        estado , user = login_user(name, passw)
        if estado:
            console.clear()
            print(f"Bienvenido {user.name} {user.apellido}")
            if recoradar:
                guardarsesion(user.id)
            userId = user.id
            userConnect = user
            break
        else:
            console.clear()
            print("Nombre o contraseña incorrecta. Inténtalo de nuevo.")



comprobar_conexion()

if(userConnect):
    #console.clear()
    widget.cuadro_centro(f"Bienvenido {userConnect.name} {userConnect.apellido}")
    userId = userConnect.id
else:
    #console.clear()
    Login()

path_interno.path_interno(True, "menu")
menu_principal()
