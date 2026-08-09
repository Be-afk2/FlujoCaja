import uuid
from sqlmodel import Session, select
from bd.database import engine
from bd.models.tipo import Tipo
from bd.models import Movimiento, Subtipo
from sqlmodel import select
from sqlalchemy.orm import selectinload

def get_tipos_bd(page: int = 1, page_size: int = 10):
    offset = (page - 1) * page_size
    with Session(engine) as session:
        statement = (
            select(Tipo)
            .offset(offset)
            .limit(page_size)
        )
        return session.exec(statement).all()

def crear_tipo_bd(nombre: str, descripcion: str = None) -> Tipo:
    nuevo_tipo = Tipo(nombre=nombre, descripcion=descripcion)
    with Session(engine) as session:
        session.add(nuevo_tipo)
        session.commit()
        session.refresh(nuevo_tipo)
    return nuevo_tipo

def get_one_tipo(nombre: str) -> Tipo | None:
    with Session(engine) as session:
        statement = select(Tipo).where(Tipo.nombre == nombre)
        tipo = session.exec(statement).first()
        return tipo

def get_sub_tipos(tipoId : int):

    with Session(engine) as session:
        statement = (
            select(Tipo)
            .where(Tipo.id == tipoId)
            .options(
                selectinload(Tipo.subtipos),
            )
        )
        result = session.exec(statement).first()
        return result


def update_tipo_bd(tipo_id: int, nombre: str = None, descripcion: str = None) -> Tipo | None:
    with Session(engine) as session:
        tipo = session.get(Tipo, tipo_id)
        if not tipo:
            return None
        if nombre is not None:
            tipo.nombre = nombre
        if descripcion is not None:
            tipo.descripcion = descripcion
        session.add(tipo)
        session.commit()
        session.refresh(tipo)
    return tipo


def delete_tipo_bd(tipo_id: int) -> bool:
    with Session(engine) as session:
        tipo = session.get(Tipo, tipo_id)
        if not tipo:
            return False
        usos = session.exec(select(Movimiento).where(Movimiento.tipo_id == tipo_id)).all()
        if usos:
            raise ValueError(f"El tipo '{tipo.nombre}' está en uso por movimientos")
        for sub in session.exec(select(Subtipo).where(Subtipo.tipo_id == tipo_id)).all():
            session.delete(sub)
        session.delete(tipo)
        session.commit()
    return True