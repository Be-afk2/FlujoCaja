from sqlmodel import Session, select
from bd.database import engine
from bd.models.tipo import Tipo

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

