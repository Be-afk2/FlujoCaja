import questionary
import menus.path as path_interno
from rich.console import Console
console = Console()


def pruebas():
    console.clear()
    path_interno.path_interno(True, "Pruebas")
    path_interno.print_path()

    answer = questionary.select(
        "¿Qué deseas hacer?",
        choices=[
            "Prueba 1",
            "Prueba 2",
            "Volver al menú principal",
        ]
    ).ask()
    match  answer:
        case "Prueba 1":
            print("Prueba 1 ejecutada.")
        case "Prueba 2":
            print("Prueba 2 ejecutada.")
        case "Volver al menú principal":
            console.clear()
            path_interno.path_interno(False, "Pruebas")