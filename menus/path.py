from rich.console import Console
console = Console()

path_app = ""


def path_interno(agregar: bool, ruta: str):
    global path_app
    if agregar:
        path_app = path_app + "/" + ruta
    else:
        path_app = "/".join(path_app.split("/")[:-1])


def print_path():
    console.print(path_app)

def get_path():
    return path_app