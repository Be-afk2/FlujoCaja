from sqlmodel import Session, select
from bd.database import engine
from bd.models import sesion
from bd.models.sesion import Sesion
from bd.models.user import User
from uuid import UUID, uuid4

def generar_uuid() -> str:
    return str(uuid4())

def guardar_sesion_bd(user_id: str) -> None:
    with Session(engine) as session:

        oldsesion = get_sesion()
        if(oldsesion):
            eliminar_sesion_bd()

        sesion = Sesion(
            idUser=str(user_id),
            token=generar_uuid()
        )
        session.add(sesion)
        session.commit()


def actualizar_token_bd() -> str:
    with Session(engine) as session:
        stmt = select(Sesion)
        sesion = session.exec(stmt).first()

        if sesion:
            sesion.token = generar_uuid()
            session.add(sesion)
            session.commit()
            return sesion.token
        

def get_sesion() -> tuple[User, str] | None:
    with Session(engine) as session:
        stmt = select(Sesion)
        sesion = session.exec(stmt).first()

        if not sesion:
            return None
        actualizar_token_bd()
        user_id = UUID(sesion.idUser)  # 👈 CLAVE
        user = session.get(User, user_id)

        return user, sesion.token
def eliminar_sesion_bd() -> None:
    with Session(engine) as session:
        stmt = select(Sesion)
        sesion = session.exec(stmt).first()

        if sesion:
            session.delete(sesion)
            session.commit()
    return "ok"

