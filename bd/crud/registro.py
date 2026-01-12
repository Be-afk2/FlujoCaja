from datetime import datetime
from sqlmodel import Session, select
from bd.database import engine
from bd.models import user


def fecha_hoy() -> tuple[int, int, int]:
    hoy = datetime.now()
    return hoy.day, hoy.month, hoy.year


def crear_registro(user:user,monto:float,tipo:str) :


    return 
