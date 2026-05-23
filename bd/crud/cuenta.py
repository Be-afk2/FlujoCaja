from datetime import datetime
import uuid
from sqlmodel import Session, select
from bd.crud.moneda import get_one_moneda
from bd.crud.tipo import get_one_tipo
from bd.database import engine
from bd.crud.sesion import *
from sqlalchemy.orm import selectinload
from bd.models import Cuenta, TipoCuenta

def get_cuentas():
    with Session(engine) as session:
        statement = (
            select(Cuenta)
            .options(selectinload(Cuenta.tipo_cuenta))
            .where(Cuenta.user_id == str(get_sesion().id))
        )

        return session.exec(statement).all()
    
def crear_cuenta(nombre:str, descripcion:str, tipo:int, moneda_id:int) -> Cuenta:
    with Session(engine) as session:
        nuevo_cuenta = Cuenta(
            nombre=nombre,
            descripcion=descripcion,
            tipo_id=tipo,
            user_id=str(get_sesion().id),
            moneda_id= moneda_id,
            saldo=0.0
        )
        session.add(nuevo_cuenta)
        session.commit()
        session.refresh(nuevo_cuenta)   
    return nuevo_cuenta

def get_tipos_cuenta():
    with Session(engine) as session:
        statement = select(TipoCuenta)
        return session.exec(statement).all()
    
def create_tipo_cuenta(nombre:str, descripcion:str) -> TipoCuenta:
    with Session(engine) as session:
        nuevo_tipo_cuenta = TipoCuenta(
            tipo=nombre,
            descripcion=descripcion,
        )
        session.add(nuevo_tipo_cuenta)
        session.commit()
        session.refresh(nuevo_tipo_cuenta)
    return nuevo_tipo_cuenta