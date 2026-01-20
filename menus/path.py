path_app =""
def path_interno(agregar: bool, ruta : str):
    global path_app
    if(agregar):
        path_app = path_app + "/" + ruta
    else:
        #eliminar la ultima parte del path
        path_app = "/".join(path_app.split("/")[:-1])
def print_path():
    print(path_app)