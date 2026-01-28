import questionary
from bd.crud.sesion import eliminar_sesion_bd
from menus.pruebas import pruebas
from rich.console import Console
from bd.crud.user import crear_usuario
import menus.path as path_interno
import time
from widget.widget import cuadro_centro
console = Console()

def system_menu():
    path_interno.path_interno(True, "System")
    console.clear()
    while True:
        path_interno.print_path()
        answer = questionary.select(
            "¿Qué deseas hacer?",
            choices=[
                "Crear usuario",
                "Pruebas",
                "Cerrar sesión",
                "Volver al menú principal"
            ]
        ).ask()

        match answer:
            case "Cerrar sesión":
                eliminar_sesion_bd()
                console.clear()
                print("Sesión cerrada.")
                print("No Volvera a iniciar sesión automaticamente")
            case "Pruebas":
                pruebas()
            case "Crear usuario":
                name = questionary.text("Nombre:").ask()
                apellido = questionary.text("Apellido:").ask()
                passw = questionary.password("Contraseña:").ask()

                user = crear_usuario(name, apellido, passw)
                cuadro_centro(f"Usuario creado: {user.id} - {user.name} {user.apellido}")
                time.sleep(4)
                console.clear()
            case "Volver al menú principal":
                console.clear()
                path_interno.path_interno(False, "System")
                break
            case _:
                print("Opción no válida. Inténtalo de nuevo.")


