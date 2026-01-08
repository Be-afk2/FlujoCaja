from sqlmodel import Session, select
from bd.database import engine
from bd.models.sesion import Sesion
from bd.models.user import User
from uuid import UUID

def guardar_sesion_bd(user_id: str) -> None:
    with Session(engine) as session:
        sesion = Sesion(
            idUser=str(user_id),
        )
        session.add(sesion)
        session.commit()

def get_sesion() -> User | None:
    with Session(engine) as session:
        stmt = select(Sesion)
        sesion = session.exec(stmt).first()

        if not sesion:
            return None

        user_id = UUID(sesion.idUser)  # 👈 CLAVE
        user = session.get(User, user_id)

        return user