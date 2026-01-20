import questionary
from sqlalchemy import Table
from bd.crud.tipo import crear_tipo_bd , get_tipos_bd
from rich.console import Console
import menus.path as path_interno       
console = Console()

def formulario_agregar_categoria():
    nombre = questionary.text("Nombre de la categoría:").ask()
    descripcion = questionary.text("Descripción de la categoría (opcional):").ask()

    nuevo_tipo = crear_tipo_bd(nombre, descripcion)
    print(f"Categoría creada: {nuevo_tipo.id} - {nuevo_tipo.nombre}")

def tabla_categorias(lista):
    table = Table(title="Tipos")
    table.add_column("ID")
    table.add_column("Nombre")
    table.add_column("Descripción")

    for item in lista:
        table.add_row(
            str(item.id),
            item.nombre,
            item.descripcion if item.descripcion else "N/A",
        )
    console.print(table)

def vista_categorias():
    while True:
        page = questionary.text("Página (número):", default="1").ask()
        try:
            page_num = int(page)
            if page_num < 1:
                raise ValueError
        except ValueError:
            print("Por favor, ingresa un número de página válido.")
            continue

        categorias = get_tipos_bd(page=page_num, page_size=5)
        if not categorias:
            print("No hay más categorías para mostrar.")
            continue

        tabla_categorias(categorias)

        otra_pagina = questionary.confirm("¿Deseas ver otra página?").ask()
        if not otra_pagina:
            break

def menu_categorias():
    console.clear()
    path_interno(True, "Categorías")
    path_interno.print_path()
    
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
                formulario_agregar_categoria()
            case "Ver categorías":
                vista_categorias()
            case "Volver al menú principal":
                console.clear()
                path_interno(False, "Categorías")

                break
            case _:
                print("Opción no válida. Inténtalo de nuevo.")