import menus.path as path_interno
import questionary
from bd.crud.user import *
from menus.gastos import menu_gastos
from menus.categorias import menu_categorias
from rich.console import Console
from menus.system import system_menu

console = Console()

def menu_principal():
    while True:
        path_interno.print_path()
        answer = questionary.select(
            "¿Qué deseas hacer?",
            choices=[
                "Gastos",
                "Categorías",
                "Salir",
                "System"
            ]
        ).ask()
        match answer:

            case "Gastos":
                menu_gastos()
            case "Categorías":
                menu_categorias()
            case "System":
                system_menu()
            case "Salir":
                print("Saliendo...")
                break
            case _:
                print("Opción no válida. Inténtalo de nuevo.")

