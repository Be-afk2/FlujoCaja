from sqlmodel import SQLModel, create_engine, Session
from bd.models.user import User     # uso explícito

DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL, echo=False)

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

    print(user.id)

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