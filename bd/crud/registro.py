from datetime import datetime
import uuid
from sqlmodel import Session, select
from bd.database import engine
from bd.models import user
from bd.crud.sesion import *

def fecha_hoy() -> tuple[int, int, int]:
    hoy = datetime.now()
    return hoy.day, hoy.month, hoy.year


def crear_registro(monto:float,tipo:str) :
    ingreso = True if monto > 0 else False
    
    with Session(engine) as session:
        nuevo_registro = user(
            monto=monto,
            ingreso=ingreso,
            tipo=tipo,
            user_id=get_sesion().id,
        )
        session.add(nuevo_registro)
        session.commit()

    return  