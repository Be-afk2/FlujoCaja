from sqlmodel import Session, select
from bd.database import engine
from bd.models.user import User
from passlib.hash import bcrypt
from typing import Optional, Tuple
from uuid import UUID
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
    
def login_user(name: str, passw: str):
    with Session(engine) as session:
        stmt = select(User).where(User.name == name)
        user = session.exec(stmt).first()

        if not user:
            return None

        if not bcrypt.verify(passw, user.passw):
            return None

        return user
    
    
def obtener_usuario(user_id: str) -> Optional[User]:
    with Session(engine) as session:
        user = session.get(User, user_id)
        return user


def actualizar_perfil(user_id: str, name: str | None = None, apellido: str | None = None) -> Optional[User]:
    with Session(engine) as session:
        user = session.get(User, UUID(user_id))

        if not user:
            return None

        if name is not None:
            user.name = name
        if apellido is not None:
            user.apellido = apellido

        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def cambiar_contrasena(user_id: str, passw_actual: str, passw_nueva: str) -> bool:
    with Session(engine) as session:
        user = session.get(User, UUID(user_id))

        if not user:
            return False

        if not bcrypt.verify(passw_actual, user.passw):
            return False

        user.passw = bcrypt.hash(passw_nueva)
        session.add(user)
        session.commit()
        return True
