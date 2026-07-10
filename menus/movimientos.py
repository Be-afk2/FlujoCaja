import logging
import uuid
from rich.console import Console
import questionary
from bd.crud.movimiento import crear_movimiento, movimientos_paginados
from bd.crud.tipo import get_tipos_bd
from menus.path import *
from datetime import datetime
from rich.table import Table
console = Console()
logger = logging.getLogger(__name__)


def menu_movimientos():
    console.clear()
    path_interno(True, "Movimientos")
    print_path()
    while True:
        answer = questionary.select(
            "¿Qué deseas hacer en Movimientos?",
            choices=[
                "Agregar movimiento",
                "Ver movimientos",
                "Volver al menú principal",
            ]
        ).ask()
        match answer:
            case "Agregar movimiento":
                agregar_movimiento()
                console.clear()
            case "Ver movimientos":
                ver_movimientos()
                console.clear()
            case "Volver al menú principal":
                console.clear()
                path_interno(False, "movimientos")
                break
            case "Configuración":
                logger.info("Funcionalidad de configuración pendiente de implementar")
            case _:
                logger.warning("Opción no válida en menú de movimientos")



def agregar_movimiento():
    while True:
        monto = questionary.text("Ingrese el monto del movimiento:").ask()
        if(monto is None or monto.strip() == "" or monto == "0"):
            break

        tipo = questionary.select(
            "¿Qué tipo de movimiento es?",
            choices=[t.nombre for t in get_tipos_bd()]
        ).ask()

        fecha_str = questionary.text(
            "Ingrese fecha (dd/mm/yyyy)",
        ).ask()
         
        # si es none o cadena vacia dejarlo en none y no parcear    
        if(fecha_str is None or fecha_str.strip() == ""):
            fecha = None
        else:
            fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
        logger.debug("Fecha capturada para movimiento: %s", fecha)
        try:
            monto = float(monto)
            crear_movimiento(monto, tipo, fecha)
        except ValueError:
            console.print("[red]Por favor, ingrese un número válido.[/red]")

def ver_movimientos():
    while True:
        page = questionary.text("Página (número):", default="1").ask()
        try:
            page_num = int(page)
            if page_num < 1:
                raise ValueError
        except ValueError:
            logger.warning("Se ingresó un número de página inválido")
            continue

        movimientos = movimientos_paginados(page=page_num, page_size=5)
        if not movimientos:
            logger.info("No hay más movimientos para mostrar")
            continue
        logger.debug("Movimientos obtenidos: %s", movimientos)
        tabla_movimientos(movimientos)

        otra_pagina = questionary.confirm("¿Deseas ver otra página?").ask()
        if not otra_pagina:
            break

def tabla_movimientos(lista):
    table = Table(title="Movimientos")
    table.add_column("Monto")
    table.add_column("Fecha")
    table.add_column("Tipo")
    for item in lista:
        logger.debug("Procesando movimiento id=%s monto=%s", getattr(item, "id", None), item.monto)
        table.add_row(
            item.monto,  # monto
            item.fecha.strftime("%d/%m/%Y") if item.fecha else "N/A",  # fecha
            item.tipo.nombre  # tipo
        )
    console.print(table)
