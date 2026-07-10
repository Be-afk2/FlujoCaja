from datetime import date
from typing import Optional
from sqlmodel import Session, select, and_
from bd.database import engine
from bd.models import Movimiento, Cuenta, Subtipo, User
from bd.crud.cuenta import actualizar_saldo
from bd.crud.resumen import actualizar_por_movimiento
from sqlalchemy.orm import selectinload


def fecha_hoy() -> tuple[int, int, int]:
    hoy = date.today()
    return hoy.day, hoy.month, hoy.year


def _validar_cuenta(cuenta_id: int, user: User, session: Session) -> None:
    cuenta = session.get(Cuenta, cuenta_id)
    if not cuenta:
        raise ValueError(f"Cuenta {cuenta_id} no existe")
    if cuenta.user_id != str(user.id):
        raise ValueError(f"Cuenta {cuenta_id} no pertenece al usuario")


def _validar_subtipo(subtipo_id: int, tipo_id: int, session: Session) -> None:
    subtipo = session.get(Subtipo, subtipo_id)
    if not subtipo:
        raise ValueError(f"Subtipo {subtipo_id} no existe")
    if subtipo.tipo_id != tipo_id:
        raise ValueError(
            f"Subtipo {subtipo_id} no pertenece al tipo {tipo_id}"
        )


def crear_movimiento(
    monto: float,
    tipo_id: int,
    cuenta_id: int,
    user: User,
    subtipo_id: Optional[int] = None,
    descripcion: Optional[str] = None,
    fecha: Optional[date] = None,
) -> Movimiento:
    ingreso = monto > 0

    with Session(engine) as session:
        _validar_cuenta(cuenta_id, user, session)
        if subtipo_id is not None:
            _validar_subtipo(subtipo_id, tipo_id, session)
        nuevo_movimiento = Movimiento(
            monto=monto,
            es_ingreso=ingreso,
            tipo_id=tipo_id,
            subtipo_id=subtipo_id,
            cuenta_id=cuenta_id,
            user_id=str(user.id),
            descripcion=descripcion,
            fecha=fecha or date.today(),
        )
        session.add(nuevo_movimiento)
        session.flush()
        actualizar_saldo(cuenta_id, monto, session=session)
        actualizar_por_movimiento(session, str(user.id), cuenta_id, monto, nuevo_movimiento.fecha)
        session.commit()
        session.refresh(nuevo_movimiento)

    return nuevo_movimiento


def get_movimiento(movimiento_id: int, user: User) -> Movimiento | None:
    with Session(engine) as session:
        mov = session.get(Movimiento, movimiento_id)
        if mov and mov.user_id != str(user.id):
            return None
        return mov


def update_movimiento(
    movimiento_id: int,
    user: User,
    monto: Optional[float] = None,
    tipo_id: Optional[int] = None,
    subtipo_id: Optional[int] = None,
    cuenta_id: Optional[int] = None,
    descripcion: Optional[str] = None,
    fecha: Optional[date] = None,
) -> Movimiento | None:
    with Session(engine) as session:
        mov = session.get(Movimiento, movimiento_id)
        if not mov or mov.user_id != str(user.id):
            return None

        if cuenta_id is not None:
            _validar_cuenta(cuenta_id, user, session)
        if subtipo_id is not None:
            _validar_subtipo(subtipo_id, tipo_id or mov.tipo_id, session)

        saldo_anterior = mov.monto
        cuenta_anterior = mov.cuenta_id
        fecha_anterior = mov.fecha

        if monto is not None:
            mov.monto = monto
            mov.es_ingreso = monto > 0
        if tipo_id is not None:
            mov.tipo_id = tipo_id
        if subtipo_id is not None:
            mov.subtipo_id = subtipo_id
        if cuenta_id is not None:
            mov.cuenta_id = cuenta_id
        if descripcion is not None:
            mov.descripcion = descripcion
        if fecha is not None:
            mov.fecha = fecha

        session.add(mov)
        session.flush()
        actualizar_saldo(cuenta_anterior, -saldo_anterior, session=session)
        actualizar_saldo(mov.cuenta_id, mov.monto, session=session)
        actualizar_por_movimiento(
            session,
            str(user.id),
            mov.cuenta_id,
            mov.monto,
            mov.fecha,
            old_monto=saldo_anterior,
            old_cuenta_id=cuenta_anterior,
            old_fecha=fecha_anterior,
        )
        session.commit()

    return mov


def delete_movimiento(movimiento_id: int, user: User) -> bool:
    with Session(engine) as session:
        mov = session.get(Movimiento, movimiento_id)
        if not mov or mov.user_id != str(user.id):
            return False

        monto = mov.monto
        cuenta_id = mov.cuenta_id
        user_id = mov.user_id
        fecha = mov.fecha
        session.delete(mov)
        session.flush()
        actualizar_saldo(cuenta_id, -monto, session=session)
        actualizar_por_movimiento(
            session,
            user_id,
            cuenta_id,
            0.0,
            fecha,
            old_monto=monto,
        )
        session.commit()

    return True


def movimientos_filtrados(
    user: User,
    pagina: int = 1,
    cantidad: int = 10,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    cuenta_id: Optional[int] = None,
    tipo_id: Optional[int] = None,
    subtipo_id: Optional[int] = None,
    es_ingreso: Optional[bool] = None,
):
    offset = (pagina - 1) * cantidad

    with Session(engine) as session:
        condiciones = [Movimiento.user_id == str(user.id)]

        if fecha_desde:
            condiciones.append(Movimiento.fecha >= fecha_desde)
        if fecha_hasta:
            condiciones.append(Movimiento.fecha <= fecha_hasta)
        if cuenta_id is not None:
            condiciones.append(Movimiento.cuenta_id == cuenta_id)
        if tipo_id is not None:
            condiciones.append(Movimiento.tipo_id == tipo_id)
        if subtipo_id is not None:
            condiciones.append(Movimiento.subtipo_id == subtipo_id)
        if es_ingreso is not None:
            condiciones.append(Movimiento.es_ingreso == es_ingreso)
        statement = (
            select(Movimiento)
            .options(selectinload(Movimiento.tipo))
            .where(and_(*condiciones))
            .offset(offset)
            .limit(cantidad)
            .order_by(Movimiento.fecha.desc())
        )

        total = session.exec(select(Movimiento.id).where(and_(*condiciones))).all()
        resultados = session.exec(statement).all()

    return resultados, len(total)   
