import menus.path as path_interno
import questionary
from bd.crud.user import *
from menus.gastos import menu_gastos
from menus.categorias import menu_categorias
from bd.crud.sesion import eliminar_sesion_bd
from rich.console import Console
from menus.pruebas import pruebas
console = Console()

def menu_principal():
    while True:
        path_interno.print_path()
        answer = questionary.select(
            "¿Qué deseas hacer?",
            choices=[
                "Crear usuario",
                "Gastos",
                "Categorías",
                "Pruebas",
                "Salir",
                "Cerrar sesión"
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
            case "Cerrar sesión":
                eliminar_sesion_bd()
                console.clear()
                print("Sesión cerrada.")
                print("No Volvera a iniciar sesión automaticamente")
            case "Pruebas":
                pruebas()
            case _:
                print("Opción no válida. Inténtalo de nuevo.")

