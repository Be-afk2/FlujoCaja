from datetime import datetime
import uuid
from sqlmodel import Session, select
from bd.crud.tipo import get_one_tipo
from bd.database import engine
from bd.models import Registro, Tipo
from bd.crud.sesion import *
from sqlalchemy.orm import selectinload
def fecha_hoy() -> tuple[int, int, int]:
    hoy = datetime.now()
    return hoy.day, hoy.month, hoy.year


def crear_registro(monto:float,tipo:str, fecha:datetime=None) -> Registro:
    ingreso = True if monto > 0 else False
    
    with Session(engine) as session:
        nuevo_registro = Registro(
            monto=monto,
            es_ingreso=ingreso,
            tipo_id=get_one_tipo(tipo).id,
            user_id=str(get_sesion().id),
            fecha=fecha
        )
        session.add(nuevo_registro)
        session.commit()

    return nuevo_registro
def registros_paguinados(page: int = 1, page_size: int = 10):
    offset = (page - 1) * page_size

    with Session(engine) as session:
        statement = (
            select(Registro)
            .options(selectinload(Registro.tipo))
            .where(Registro.user_id == str(get_sesion().id))
            .offset(offset)
            .limit(page_size)
            .order_by(Registro.fecha.desc())
        )

        return session.exec(statement).all()