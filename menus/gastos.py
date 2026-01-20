from rich.console import Console
import questionary
from menus.path import *
console = Console()

        
def menu_gastos():  
    console.clear() 
    path_interno(True, "Gastos")
    print_path()
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
                path_interno(False, "gastos")
                break
            case _:
                print("Opción no válida. Inténtalo de nuevo.")

