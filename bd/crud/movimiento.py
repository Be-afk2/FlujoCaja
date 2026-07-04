from datetime import datetime
from sqlmodel import Session, select
from bd.crud.tipo import get_one_tipo
from bd.database import engine
from bd.models import Movimiento, Tipo
from bd.crud.sesion import *
from sqlalchemy.orm import selectinload
def fecha_hoy() -> tuple[int, int, int]:
    hoy = datetime.now()
    return hoy.day, hoy.month, hoy.year


def crear_movimiento(monto:float,tipo:str, fecha:datetime=None) -> Movimiento:
    ingreso = True if monto > 0 else False
    
    with Session(engine) as session:
        nuevo_movimiento = Movimiento(
            monto=monto,
            es_ingreso=ingreso,
            tipo_id=get_one_tipo(tipo).id,
            user_id=str(obtener_sesion().id),
            fecha=fecha
        )
        session.add(nuevo_movimiento)
        session.commit()

    return nuevo_movimiento
def movimientos_paginados(page: int = 1, page_size: int = 10):
    offset = (page - 1) * page_size

    with Session(engine) as session:
        statement = (
            select(Movimiento)
            .options(selectinload(Movimiento.tipo))
            .where(Movimiento.user_id == str(obtener_sesion().id))
            .offset(offset)
            .limit(page_size)
            .order_by(Movimiento.fecha.desc())
        )

        return session.exec(statement).all()
