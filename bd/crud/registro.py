from datetime import datetime

def fecha_hoy() -> tuple[int, int, int]:
    hoy = datetime.now()
    return hoy.day, hoy.month, hoy.year