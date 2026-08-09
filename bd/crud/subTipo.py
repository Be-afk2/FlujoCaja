import logging
from sqlmodel import Session, select
from bd.database import engine
from bd.models import Subtipo, Movimiento

logger = logging.getLogger(__name__)


def crear_subTipo_bd(nombre: str, tipoid: int) -> Subtipo:
    nuevo_tipo = Subtipo(nombre=nombre, tipo_id=tipoid)
    with Session(engine) as session:
        session.add(nuevo_tipo)
        session.commit()
        session.refresh(nuevo_tipo)
    return nuevo_tipo


def update_subtipo_bd(subtipo_id: int, nombre: str) -> Subtipo | None:
    with Session(engine) as session:
        subtipo = session.get(Subtipo, subtipo_id)
        if not subtipo:
            return None
        subtipo.nombre = nombre
        session.add(subtipo)
        session.commit()
        session.refresh(subtipo)
    return subtipo


def delete_subtipo_bd(subtipo_id: int) -> bool:
    with Session(engine) as session:
        subtipo = session.get(Subtipo, subtipo_id)
        if not subtipo:
            return False
        usos = session.exec(select(Movimiento).where(Movimiento.subtipo_id == subtipo_id)).all()
        if usos:
            raise ValueError(f"El subtipo '{subtipo.nombre}' está en uso por movimientos")
        session.delete(subtipo)
        session.commit()
    return True
