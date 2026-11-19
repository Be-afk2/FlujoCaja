from datetime import date
from typing import Iterator, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import Session, and_, func, select

from bd.crud.cuenta import actualizar_saldo
from bd.crud.resumen import actualizar_por_movimiento
from bd.database import engine
from bd.models import Cuenta, Movimiento, Subtipo, Tipo, User


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


def _crear_movimiento_sesion(
    session: Session,
    *,
    monto: float,
    tipo_id: int,
    cuenta_id: int,
    user: User,
    subtipo_id: Optional[int] = None,
    descripcion: Optional[str] = None,
    fecha: Optional[date] = None,
    es_deuda: bool = False,
) -> Movimiento:
    """Crea el movimiento sin hacer commit (lo usan movimientos y deudas)."""
    _validar_cuenta(cuenta_id, user, session)
    if subtipo_id is not None:
        _validar_subtipo(subtipo_id, tipo_id, session)

    nuevo_movimiento = Movimiento(
        monto=monto,
        es_ingreso=monto > 0,
        es_deuda=es_deuda,
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
    actualizar_por_movimiento(
        session,
        str(user.id),
        cuenta_id,
        monto,
        nuevo_movimiento.fecha,
        es_deuda=es_deuda,
    )
    return nuevo_movimiento


def _actualizar_movimiento_sesion(
    session: Session,
    mov: Movimiento,
    *,
    monto: Optional[float] = None,
    tipo_id: Optional[int] = None,
    subtipo_id: Optional[int] = None,
    cuenta_id: Optional[int] = None,
    descripcion: Optional[str] = None,
    fecha: Optional[date] = None,
) -> Movimiento:
    """Actualiza el movimiento sin hacer commit (lo usan movimientos y deudas)."""
    if cuenta_id is not None:
        cuenta = session.get(Cuenta, cuenta_id)
        if not cuenta:
            raise ValueError(f"Cuenta {cuenta_id} no existe")
        if cuenta.user_id != mov.user_id:
            raise ValueError(f"Cuenta {cuenta_id} no pertenece al usuario")
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
        mov.user_id,
        mov.cuenta_id,
        mov.monto,
        mov.fecha,
        old_monto=saldo_anterior,
        old_cuenta_id=cuenta_anterior,
        old_fecha=fecha_anterior,
        es_deuda=mov.es_deuda,
        old_es_deuda=mov.es_deuda,
    )
    return mov


def _eliminar_movimiento_sesion(session: Session, mov: Movimiento) -> None:
    """Elimina el movimiento y revierte saldo/resumen sin hacer commit."""
    monto = mov.monto
    cuenta_id = mov.cuenta_id
    user_id = mov.user_id
    fecha = mov.fecha
    es_deuda = mov.es_deuda

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
        old_es_deuda=es_deuda,
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
    with Session(engine) as session:
        nuevo_movimiento = _crear_movimiento_sesion(
            session,
            monto=monto,
            tipo_id=tipo_id,
            cuenta_id=cuenta_id,
            user=user,
            subtipo_id=subtipo_id,
            descripcion=descripcion,
            fecha=fecha,
        )
        session.commit()
        session.refresh(nuevo_movimiento)

    return nuevo_movimiento


def get_movimiento(movimiento_id: int, user: User) -> Movimiento | None:
    with Session(engine) as session:
        mov = session.get(Movimiento, movimiento_id)
        if mov and mov.user_id != str(user.id):
            return None
        return mov


def crear_movimientos_bulk(filas: list[dict], user: User) -> dict:
    """Inserta varios movimientos en una sola transacción.

    Valida cada fila por separado; las inválidas se reportan en `errores`
    sin abortar la importación del resto. Devuelve:
    {"importados": int, "errores": [{"fila": int, "error": str}]}
    """
    importados = 0
    errores: list[dict] = []

    with Session(engine) as session:
        for idx, fila in enumerate(filas, start=1):
            try:
                _crear_movimiento_sesion(
                    session,
                    monto=fila["monto"],
                    tipo_id=fila["tipo_id"],
                    cuenta_id=fila["cuenta_id"],
                    user=user,
                    subtipo_id=fila.get("subtipo_id"),
                    descripcion=fila.get("descripcion"),
                    fecha=fila.get("fecha"),
                )
                importados += 1
            except (ValueError, KeyError, TypeError) as e:
                errores.append({"fila": idx, "error": str(e)})

        session.commit()

    return {"importados": importados, "errores": errores}


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
        if mov.es_deuda:
            raise ValueError(
                "Los movimientos de deuda se gestionan desde el modulo de deudas"
            )

        _actualizar_movimiento_sesion(
            session,
            mov,
            monto=monto,
            tipo_id=tipo_id,
            subtipo_id=subtipo_id,
            cuenta_id=cuenta_id,
            descripcion=descripcion,
            fecha=fecha,
        )
        session.commit()
        session.refresh(mov)

    return mov


def delete_movimiento(movimiento_id: int, user: User) -> bool:
    with Session(engine) as session:
        mov = session.get(Movimiento, movimiento_id)
        if not mov or mov.user_id != str(user.id):
            return False
        if mov.es_deuda:
            raise ValueError(
                "Los movimientos de deuda se gestionan desde el modulo de deudas"
            )

        _eliminar_movimiento_sesion(session, mov)
        session.commit()

    return True


def _condiciones_movimientos(
    user: User,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    cuenta_id: Optional[int] = None,
    moneda_id: Optional[int] = None,
    tipo_id: Optional[int] = None,
    subtipo_id: Optional[int] = None,
    es_ingreso: Optional[bool] = None,
    es_deuda: Optional[bool] = None,
) -> list:
    """Filtros compartidos por el listado paginado y la exportacion CSV."""
    condiciones = [Movimiento.user_id == str(user.id)]

    if fecha_desde:
        condiciones.append(Movimiento.fecha >= fecha_desde)
    if fecha_hasta:
        condiciones.append(Movimiento.fecha <= fecha_hasta)
    if cuenta_id is not None:
        condiciones.append(Movimiento.cuenta_id == cuenta_id)
    if moneda_id is not None:
        subquery = select(Cuenta.id).where(
            Cuenta.moneda_id == moneda_id,
            Cuenta.user_id == str(user.id),
        )
        condiciones.append(Movimiento.cuenta_id.in_(subquery))
    if tipo_id is not None:
        condiciones.append(Movimiento.tipo_id == tipo_id)
    if subtipo_id is not None:
        condiciones.append(Movimiento.subtipo_id == subtipo_id)
    if es_ingreso is not None:
        condiciones.append(Movimiento.es_ingreso == es_ingreso)
    if es_deuda is not None:
        condiciones.append(Movimiento.es_deuda == es_deuda)

    return condiciones


def movimientos_filtrados(
    user: User,
    pagina: int = 1,
    cantidad: int = 10,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    cuenta_id: Optional[int] = None,
    moneda_id: Optional[int] = None,
    tipo_id: Optional[int] = None,
    subtipo_id: Optional[int] = None,
    es_ingreso: Optional[bool] = None,
    es_deuda: Optional[bool] = None,
):
    offset = (pagina - 1) * cantidad
    condiciones = _condiciones_movimientos(
        user,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cuenta_id=cuenta_id,
        moneda_id=moneda_id,
        tipo_id=tipo_id,
        subtipo_id=subtipo_id,
        es_ingreso=es_ingreso,
        es_deuda=es_deuda,
    )

    with Session(engine) as session:
        statement = (
            select(Movimiento)
            .options(selectinload(Movimiento.tipo))
            .where(and_(*condiciones))
            .offset(offset)
            .limit(cantidad)
            .order_by(Movimiento.fecha.desc())
        )

        # count(*) lo resuelve SQLite con el indice (user_id, fecha) sin
        # materializar todas las filas como hacia `select(Movimiento.id).all()`.
        total = session.exec(
            select(func.count()).select_from(Movimiento).where(and_(*condiciones))
        ).one()
        resultados = session.exec(statement).all()

    return resultados, int(total)


def _csv_escape(valor) -> str:
    texto = "" if valor is None else str(valor)
    if any(caracter in texto for caracter in (",", '"', "\n", "\r")):
        return '"' + texto.replace('"', '""') + '"'
    return texto


def exportar_movimientos_csv(
    user: User,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    cuenta_id: Optional[int] = None,
    moneda_id: Optional[int] = None,
    tipo_id: Optional[int] = None,
    subtipo_id: Optional[int] = None,
    es_ingreso: Optional[bool] = None,
    es_deuda: Optional[bool] = None,
) -> Iterator[str]:
    """Genera el CSV completo de los movimientos filtrados, sin paginar.

    Se resuelve en el servidor con un JOIN a tipo y cuenta, asi el frontend no
    necesita pedir `cantidad=100000` ni cruzar los nombres en memoria.
    """
    condiciones = _condiciones_movimientos(
        user,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cuenta_id=cuenta_id,
        moneda_id=moneda_id,
        tipo_id=tipo_id,
        subtipo_id=subtipo_id,
        es_ingreso=es_ingreso,
        es_deuda=es_deuda,
    )
    statement = (
        select(
            Movimiento.fecha,
            Movimiento.monto,
            Tipo.nombre,
            Cuenta.nombre,
            Movimiento.descripcion,
        )
        .join(Tipo, Tipo.id == Movimiento.tipo_id)
        .join(Cuenta, Cuenta.id == Movimiento.cuenta_id)
        .where(and_(*condiciones))
        .order_by(Movimiento.fecha.desc(), Movimiento.id.desc())
    )

    def generar() -> Iterator[str]:
        yield "\ufefffecha,monto,tipo,cuenta,descripcion\r\n"
        with Session(engine) as session:
            for fecha, monto, tipo, cuenta, descripcion in session.exec(
                statement
            ).yield_per(1000):
                yield (
                    ",".join(
                        [
                            _csv_escape(fecha.isoformat()),
                            f"{float(monto):.2f}",
                            _csv_escape(tipo),
                            _csv_escape(cuenta),
                            _csv_escape(descripcion),
                        ]
                    )
                    + "\r\n"
                )

    return generar()
