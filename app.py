from bd.database import init_db
from bd.crud.user import *
import questionary
from rich.console import Console
from bd.crud.sesion import *
from rich.panel import Panel
from rich.align import Align
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

def cuadro_centro(name : str):
    width, height = console.size

    panel = Panel(
        Align.center(
            f"Hello, {name}",
            vertical="middle"
        ),
        width=width - 4,
        height=5 ,
        border_style="green",
        title="Welcome"
    )
    console.print(Align.center(panel))


comprobar_conexion()



if(userConnect):
    #console.clear()
    cuadro_centro(f"Bienvenido {userConnect.name} {userConnect.apellido}")
    userId = userConnect.id
else:
    #console.clear()
    Login()


def menu_gastos():    
    while True:
        answer = questionary.select(
            "¿Qué deseas hacer en Gastos?",
            choices=[
                "Agregar gasto",
                "Ver gastos",
                "Volver al menú principal",
            ]
        ).ask()
        match answer:
            case "Agregar gasto":
                print("Funcionalidad para agregar gasto (pendiente de implementar).")
            case "Ver gastos":
                print("Funcionalidad para ver gastos (pendiente de implementar).")
            case "Volver al menú principal":
                console.clear()
                break
            case _:
                print("Opción no válida. Inténtalo de nuevo.")

def menu_categorias():
    while True:
        answer = questionary.select(
            "¿Qué deseas hacer en Categorías?",
            choices=[
                "Agregar categoría",
                "Ver categorías",
                "Volver al menú principal",
            ]
        ).ask()
        match answer:
            case "Agregar categoría":
                print("Funcionalidad para agregar categoría (pendiente de implementar).")
            case "Ver categorías":
                print("Funcionalidad para ver categorías (pendiente de implementar).")
            case "Volver al menú principal":
                console.clear()
                break
            case _:
                print("Opción no válida. Inténtalo de nuevo.")

def menu_principal():
    while True:
        answer = questionary.select(
            "¿Qué deseas hacer?",
            choices=[
                "Crear usuario",
                "Gastos",
                "Categorías",
                "Salir",
            ]
        ).ask()
        match answer:
            case "Crear usuario":
                name = questionary.text("Nombre:").ask()
                apellido = questionary.text("Apellido:").ask()
                passw = questionary.password("Contraseña:").ask()

                user = crear_usuario(name, apellido, passw)
                print(f"Usuario creado: {user.id} - {user.name} {user.apellido}")
            case "Gastos":
                menu_gastos()
            case "Categorías":
                menu_categorias()
            case "Salir":
                print("Saliendo...")
                break
            case _:
                print("Opción no válida. Inténtalo de nuevo.")
#####################################################################################################

menu_principal()


