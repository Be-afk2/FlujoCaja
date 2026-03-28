from sqlmodel import Session, select
from bd.crud.tipo import get_sub_tipos
from bd.database import engine
from bd.models.subTipo import Subtipo


def crear_subTipo_bd(nombre: str, descripcion: str = None , tipoid =int) -> Subtipo:
    print("----------------------")
    print(nombre, descripcion,tipoid)
    print("----------------------")

    tipo = get_sub_tipos(tipoid)
    nuevo_tipo = Subtipo(nombre=nombre, descripcion=descripcion,tipo=tipo)
    with Session(engine) as session:
        session.add(nuevo_tipo)
        session.commit()
        session.refresh(nuevo_tipo)
    return nuevo_tipo