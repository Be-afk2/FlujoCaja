from sqlmodel import Session, select
from bd.database import engine
from bd.models.subTipo import Subtipo


def get_tipos_bd(page: int = 1, page_size: int = 10):
    offset = (page - 1) * page_size
    with Session(engine) as session:
        statement = (
            select(Subtipo)
            .offset(offset)
            .limit(page_size)
        )
        return session.exec(statement).all()