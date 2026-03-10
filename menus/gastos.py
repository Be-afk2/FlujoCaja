import uuid
from rich.console import Console
import questionary
from bd.crud.registro import crear_registro, registros_paguinados
from bd.crud.tipo import get_tipo_lista
from menus.path import *
from datetime import datetime
from rich.table import Table
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
                VerGastos()
                console.clear()
            case "Volver al menú principal":
                console.clear()
                path_interno(False, "gastos")
                break
            case "Configuración":
                print("Funcionalidad de configuración (pendiente de implementar).")
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

        fecha_str = questionary.text(
            "Ingrese fecha (dd/mm/yyyy)",
        ).ask()
         
        # si es none o cadena vacia dejarlo en none y no parcear    
        if(fecha_str is None or fecha_str.strip() == ""):
            fecha = None
        else:
            fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
        print(fecha)
        print("----------------------")
        try:
            monto = float(monto)
            crear_registro(monto, tipo, fecha)
        except ValueError:
            console.print("[red]Por favor, ingrese un número válido.[/red]")

def VerGastos():
    while True:
        page = questionary.text("Página (número):", default="1").ask()
        try:
            page_num = int(page)
            if page_num < 1:
                raise ValueError
        except ValueError:
            print("Por favor, ingresa un número de página válido.")
            continue

        gastos = registros_paguinados(page=page_num, page_size=5)
        if not gastos:
            print("No hay más categorías para mostrar.")
            continue
        print("-------------------------------")
        print(gastos)
        print("-------------------------------")
        tabla_gastos(gastos)

        otra_pagina = questionary.confirm("¿Deseas ver otra página?").ask()
        if not otra_pagina:
            break

def tabla_gastos(lista):
    table = Table(title="Gastos")
    table.add_column("Monto")
    table.add_column("Fecha")
    table.add_column("Tipo")
    for item in lista:
        print("-----------------------")
        print(item)
        print(item.monto)
        print("-------------------------")
        table.add_row(
            item.monto,  # monto
            item.fecha.strftime("%d/%m/%Y") if item.fecha else "N/A",  # fecha
            item.tipo.nombre  # tipo
        )
    console.print(table)