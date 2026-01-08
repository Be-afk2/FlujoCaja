from sqlmodel import Session, select
from bd.database import engine
from bd.models.user import User
from passlib.hash import bcrypt
from typing import Optional, Tuple
import logging

def crear_usuario(name: str, apellido: str, passw: str) -> User:
    with Session(engine) as session:
        user = User(
            name=name,
            apellido=apellido,
            passw=bcrypt.hash(passw)
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

def borrar_usuario(user_id: str) -> bool:
    with Session(engine) as session:
        user = session.get(User, user_id)

        if not user:
            return False  # no existe

        session.delete(user)
        session.commit()
        return True
    
def login_user(name: str, passw: str) -> Tuple[bool, Optional[User]]:
    """Authenticate a user by name and password.

    Returns a tuple (success: bool, user: User|None).
    """
    try:
        with Session(engine) as session:
            stmt = select(User).where(User.name == name)
            user = session.exec(stmt).first()

            if not user:
                return False, None

            # verify password hash
            if not bcrypt.verify(passw, user.passw):
                return False, None

            return True, user
    except Exception as exc:
        logging.exception("Error authenticating user %s", name)
        return False, None
    
def obtener_usuario(user_id: str) -> Optional[User]:
    with Session(engine) as session:
        user = session.get(User, user_id)
        return user
    