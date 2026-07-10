from time import sleep
from bd.database import init_db
from bd.crud.user import *
import questionary
from bd.crud.sesion import *
from bd.crud.tipo import *
from rich.console import Console
import menus.path as path_interno
from menus.principal import menu_principal
import widget.widget as widget
console = Console()
def comprobar_conexion():
    try:
        # Intentar conectarse a la base de datos
        init_db()
        console.print("Conexión a la base de datos exitosa.")
        console.clear()
    except Exception as e:
        console.print(f"Error al conectar a la base de datos: {e}")
comprobar_conexion()
console.print("----------------------------------------")

userId = None
userConnect = get_sesion()

def Login():
    global userId
    global userConnect
    while True:
        name = questionary.text("Nombre:").ask()
        if(name == "exit"):
            console.clear()
            console.print("Saliendo del programa...")
            exit()
        passw = questionary.password("Contraseña:").ask()
        recoradar = questionary.confirm("Recordar Sesion?").ask()

        console.print(recoradar)
        estado, user = login_user(name, passw)
        if estado:
            console.clear()
            console.print(f"Bienvenido {user.name} {user.apellido}")
            if recoradar:
                guardar_sesion_bd(user.id)
            userId = user.id
            userConnect = user
            break
        else:
            console.clear()
            console.print("Nombre o contraseña incorrecta. Inténtalo de nuevo.")




if(userConnect):
    #console.clear()
    widget.cuadro_centro(f"Bienvenido {userConnect.name} {userConnect.apellido}")
    userId = userConnect.id
else:
    #console.clear()
    Login()

path_interno.path_interno(True, "menu")
menu_principal()
