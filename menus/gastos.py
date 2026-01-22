import uuid
from rich.console import Console
import questionary
from bd.crud.registro import crear_registro
from bd.crud.tipo import get_tipo_lista
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
                agregar_gasto()
                console.clear()
            case "Ver gastos":
                print("Funcionalidad para ver gastos (pendiente de implementar).")
            case "Volver al menú principal":
                console.clear()
                path_interno(False, "gastos")
                break
            case _:
                print("Opción no válida. Inténtalo de nuevo.")



def agregar_gasto():
    while True:
        monto = questionary.text("Ingrese el monto del gasto:").ask()
        if(monto is None or monto.strip() == "" or monto == "0"):
            break

        tipo = questionary.select(
            "¿Qué tipo de gasto es?",
            choices=get_tipo_lista()
        ).ask()
        try:
            monto = float(monto)
            crear_registro(monto, tipo)
        except ValueError:
            console.print("[red]Por favor, ingrese un número válido.[/red]")