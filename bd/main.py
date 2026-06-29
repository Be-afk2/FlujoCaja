from sqlmodel import SQLModel, create_engine, Session
import logging
from bd.models.user import User     # uso explícito
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
logger = logging.getLogger(__name__)

def init_db():
    SQLModel.metadata.create_all(engine)

init_db()

with Session(engine) as session:
    user = User(
        name="Benja",
        apellido="Diaz",
        passw="contraseña"
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    logger.debug("Usuario semilla creado con id=%s", user.id)

def CrearUsuario(name: str, apellido: str, passw: str):
    with Session(engine) as session:
        user = User(
            name=name,
            apellido=apellido,
            passw=passw
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return user
