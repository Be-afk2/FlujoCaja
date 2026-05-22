from sqlmodel import Session, select

from bd.database import engine
from bd.models import Moneda    


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