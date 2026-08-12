from sqlmodel import Session, select

from bd.database import engine
from bd.models import Cuenta, Moneda


def get_monedas():
    with Session(engine) as session:
        statement = select(Moneda)
        return session.exec(statement).all()
    
def crear_moneda(nombre:str, simbolo:str) -> Moneda:
    with Session(engine) as session:
        nueva_moneda = Moneda(
            nombre=nombre,
            simbolo=simbolo,
        )
        session.add(nueva_moneda)
        session.commit()
        session.refresh(nueva_moneda)
    return nueva_moneda

def get_one_moneda(id: int) -> Moneda:
    with Session(engine) as session:
        statement = select(Moneda).where(Moneda.id == id)
        return session.exec(statement).first()

def actualizar_moneda(id: int, nombre: str, simbolo: str) -> Moneda | None:
    with Session(engine) as session:
        moneda = session.get(Moneda, id)
        if not moneda:
            return None
        moneda.nombre = nombre
        moneda.simbolo = simbolo
        session.add(moneda)
        session.commit()
        session.refresh(moneda)
    return moneda

def eliminar_moneda(id: int) -> bool:
    with Session(engine) as session:
        moneda = session.get(Moneda, id)
        if not moneda:
            return False
        en_uso = session.exec(select(Cuenta).where(Cuenta.moneda_id == id)).first()
        if en_uso:
            raise ValueError("La moneda está en uso por una cuenta y no puede eliminarse")
        session.delete(moneda)
        session.commit()
    return True