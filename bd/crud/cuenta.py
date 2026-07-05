from typing import Optional
from sqlmodel import Session, select
from bd.database import engine
from bd.crud.sesion import obtener_sesion
from sqlalchemy.orm import selectinload
from bd.models import Cuenta, TipoCuenta, User

def get_cuentas(user: User):
    with Session(engine) as session:
        statement = (
            select(Cuenta)
            .options(selectinload(Cuenta.tipo_cuenta))
            .where(Cuenta.user_id == str(user.id))
        )

        return session.exec(statement).all()

def get_cuenta(cuenta_id: int) -> Cuenta | None:
    with Session(engine) as session:
        return session.get(Cuenta, cuenta_id)

def _aplicar_delta(session: Session, cuenta_id: int, delta: float) -> float:
    cuenta = session.get(Cuenta, cuenta_id)
    if not cuenta:
        raise ValueError(f"Cuenta {cuenta_id} no existe")
    cuenta.saldo += delta
    session.add(cuenta)
    return cuenta.saldo

def actualizar_saldo(cuenta_id: int, delta: float, *, session: Optional[Session] = None) -> float:
    if session is not None:
        return _aplicar_delta(session, cuenta_id, delta)
    with Session(engine) as session:
        return _aplicar_delta(session, cuenta_id, delta)

def crear_cuenta(nombre:str, descripcion:str, tipo:int, moneda_id:int, user: User) -> Cuenta:
    with Session(engine) as session:
        nuevo_cuenta = Cuenta(
            nombre=nombre,
            descripcion=descripcion,
            tipo_id=tipo,
            user_id=str(user.id),
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