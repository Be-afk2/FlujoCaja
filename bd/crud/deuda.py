from datetime import date
from typing import Optional

from sqlmodel import Session, func, select

from bd.crud.exceptions import RecursoNoEncontradoError
from bd.crud.movimiento import (
    _actualizar_movimiento_sesion,
    _crear_movimiento_sesion,
    _eliminar_movimiento_sesion,
)
from bd.database import engine
from bd.domain.deuda import (
    EVENTO_DESEMBOLSO,
    EVENTO_PAGO,
    TIPO_DEUDAS,
    calcular_pendiente,
    es_pago_final,
    estado_deuda,
    monedas_distintas,
    signo_cuenta,
    subtipo_deuda,
    validar_abono,
    validar_direccion,
    validar_monto_original,
)
from bd.models import Cuenta, Deuda, Entidad, Moneda, Movimiento, PagoDeuda, Subtipo, Tipo, User


def _validar_entidad(session: Session, entidad_id: int, user: User) -> Entidad:
    entidad = session.get(Entidad, entidad_id)
    if not entidad or entidad.user_id != str(user.id):
        raise RecursoNoEncontradoError(f"Entidad {entidad_id} no encontrada")
    return entidad


def _validar_deuda(session: Session, deuda_id: int, user: User) -> Deuda:
    deuda = session.get(Deuda, deuda_id)
    if not deuda or deuda.user_id != str(user.id):
        raise RecursoNoEncontradoError(f"Deuda {deuda_id} no encontrada")
    return deuda


def _validar_pago(
    session: Session, deuda_id: int, pago_id: int, user: User
) -> PagoDeuda:
    pago = session.get(PagoDeuda, pago_id)
    if not pago or pago.user_id != str(user.id) or pago.deuda_id != deuda_id:
        raise RecursoNoEncontradoError(f"Pago {pago_id} no encontrado")
    return pago


def _validar_cuenta(session: Session, cuenta_id: int, user: User) -> Cuenta:
    cuenta = session.get(Cuenta, cuenta_id)
    if not cuenta:
        raise ValueError(f"Cuenta {cuenta_id} no existe")
    if cuenta.user_id != str(user.id):
        raise ValueError(f"Cuenta {cuenta_id} no pertenece al usuario")
    return cuenta


def _validar_moneda(session: Session, moneda_id: int) -> Moneda:
    moneda = session.get(Moneda, moneda_id)
    if not moneda:
        raise ValueError(f"Moneda {moneda_id} no existe")
    return moneda


def moneda_distinta(user: User, deuda_id: int, cuenta_id: int) -> bool:
    """True si la cuenta del pago usa otra moneda que la deuda."""
    with Session(engine) as session:
        deuda = _validar_deuda(session, deuda_id, user)
        cuenta = _validar_cuenta(session, cuenta_id, user)
        return monedas_distintas(deuda.moneda_id, cuenta.moneda_id)


def _tipo_deudas_id(session: Session) -> int:
    tipo = session.exec(select(Tipo).where(Tipo.nombre == TIPO_DEUDAS)).first()
    if tipo is None:
        raise ValueError(f"Falta el tipo '{TIPO_DEUDAS}' en la base de datos")
    return tipo.id


def _subtipo_id(session: Session, tipo_id: int, nombre: str) -> int:
    subtipo = session.exec(
        select(Subtipo).where(
            Subtipo.tipo_id == tipo_id,
            Subtipo.nombre == nombre,
        )
    ).first()
    if subtipo is None:
        raise ValueError(f"Falta el subtipo '{nombre}' en la base de datos")
    return subtipo.id


def total_abonos(session: Session, deuda_id: int, excluir_pago_id: Optional[int] = None) -> float:
    condiciones = [PagoDeuda.deuda_id == deuda_id]
    if excluir_pago_id is not None:
        condiciones.append(PagoDeuda.id != excluir_pago_id)
    total = session.exec(
        select(func.coalesce(func.sum(PagoDeuda.monto), 0.0)).where(*condiciones)
    ).one()
    return float(total or 0.0)


def abonos_por_deuda(session: Session, user_id: str) -> dict[int, float]:
    filas = session.exec(
        select(PagoDeuda.deuda_id, func.sum(PagoDeuda.monto))
        .where(PagoDeuda.user_id == user_id)
        .group_by(PagoDeuda.deuda_id)
    ).all()
    return {int(deuda_id): float(total) for deuda_id, total in filas}


def pendiente_y_estado(
    deuda: Deuda,
    total_abonos_deuda: float,
    hoy: Optional[date] = None,
) -> tuple[float, str]:
    pendiente = calcular_pendiente(deuda.monto_original, total_abonos_deuda)
    estado = estado_deuda(
        deuda.monto_original,
        total_abonos_deuda,
        deuda.vencimiento,
        hoy,
    )
    return pendiente, estado


def crear_deuda(
    user: User,
    entidad_id: int,
    direccion: str,
    monto_original: float,
    moneda_id: int,
    descripcion: Optional[str] = None,
    fecha: Optional[date] = None,
    vencimiento: Optional[date] = None,
    cuenta_inicial_id: Optional[int] = None,
) -> Deuda:
    validar_direccion(direccion)
    validar_monto_original(monto_original)

    with Session(engine) as session:
        _validar_entidad(session, entidad_id, user)
        _validar_moneda(session, moneda_id)

        deuda = Deuda(
            user_id=str(user.id),
            entidad_id=entidad_id,
            direccion=direccion,
            monto_original=monto_original,
            moneda_id=moneda_id,
            descripcion=descripcion,
            fecha=fecha or date.today(),
            vencimiento=vencimiento,
        )
        session.add(deuda)
        session.flush()

        if cuenta_inicial_id is not None:
            cuenta = _validar_cuenta(session, cuenta_inicial_id, user)
            tipo_id = _tipo_deudas_id(session)
            subtipo_id = _subtipo_id(
                session,
                tipo_id,
                subtipo_deuda(direccion, EVENTO_DESEMBOLSO),
            )
            movimiento = _crear_movimiento_sesion(
                session,
                monto=monto_original * signo_cuenta(direccion, EVENTO_DESEMBOLSO),
                tipo_id=tipo_id,
                cuenta_id=cuenta.id,
                user=user,
                subtipo_id=subtipo_id,
                descripcion=descripcion,
                fecha=deuda.fecha,
                es_deuda=True,
            )
            deuda.movimiento_inicial_id = movimiento.id
            session.add(deuda)

        session.commit()
        session.refresh(deuda)

    return deuda


def registrar_pago(
    user: User,
    deuda_id: int,
    monto: float,
    cuenta_id: int,
    fecha: Optional[date] = None,
    descripcion: Optional[str] = None,
) -> PagoDeuda:
    with Session(engine) as session:
        deuda = _validar_deuda(session, deuda_id, user)
        pendiente = calcular_pendiente(
            deuda.monto_original, total_abonos(session, deuda.id)
        )
        validar_abono(monto, pendiente)
        _validar_cuenta(session, cuenta_id, user)

        pendiente_restante = pendiente - monto
        tipo_id = _tipo_deudas_id(session)
        subtipo_id = _subtipo_id(
            session,
            tipo_id,
            subtipo_deuda(
                deuda.direccion,
                EVENTO_PAGO,
                es_pago_final(pendiente_restante),
            ),
        )
        fecha_pago = fecha or date.today()
        movimiento = _crear_movimiento_sesion(
            session,
            monto=monto * signo_cuenta(deuda.direccion, EVENTO_PAGO),
            tipo_id=tipo_id,
            cuenta_id=cuenta_id,
            user=user,
            subtipo_id=subtipo_id,
            descripcion=descripcion,
            fecha=fecha_pago,
            es_deuda=True,
        )
        pago = PagoDeuda(
            user_id=str(user.id),
            deuda_id=deuda.id,
            monto=monto,
            fecha=fecha_pago,
            cuenta_id=cuenta_id,
            movimiento_id=movimiento.id,
            descripcion=descripcion,
        )
        session.add(pago)
        session.commit()
        session.refresh(pago)

    return pago


def editar_deuda(
    user: User,
    deuda_id: int,
    *,
    descripcion: Optional[str] = None,
    vencimiento: Optional[date] = None,
    fecha: Optional[date] = None,
    monto_original: Optional[float] = None,
    moneda_id: Optional[int] = None,
    direccion: Optional[str] = None,
) -> Deuda:
    with Session(engine) as session:
        deuda = _validar_deuda(session, deuda_id, user)
        abonos = total_abonos(session, deuda.id)
        cambia_estructura = (
            monto_original is not None
            or moneda_id is not None
            or direccion is not None
        )
        if cambia_estructura and abonos > 0:
            raise ValueError(
                "No se puede cambiar monto, moneda o direccion con abonos registrados"
            )

        if direccion is not None:
            validar_direccion(direccion)
        if monto_original is not None:
            validar_monto_original(monto_original)
        if moneda_id is not None:
            _validar_moneda(session, moneda_id)

        nuevo_monto = monto_original if monto_original is not None else deuda.monto_original
        nueva_direccion = direccion if direccion is not None else deuda.direccion
        nueva_descripcion = descripcion if descripcion is not None else deuda.descripcion
        nueva_fecha = fecha if fecha is not None else deuda.fecha

        estructura_cambiada = (
            nuevo_monto != deuda.monto_original
            or nueva_direccion != deuda.direccion
        )

        deuda.monto_original = nuevo_monto
        deuda.direccion = nueva_direccion
        deuda.descripcion = nueva_descripcion
        deuda.fecha = nueva_fecha
        if moneda_id is not None:
            deuda.moneda_id = moneda_id
        if vencimiento is not None:
            deuda.vencimiento = vencimiento
        session.add(deuda)

        movimiento_id = deuda.movimiento_inicial_id
        if movimiento_id is not None and (
            estructura_cambiada
            or descripcion is not None
            or fecha is not None
        ):
            movimiento = session.get(Movimiento, movimiento_id)
            if movimiento is not None:
                tipo_id = _tipo_deudas_id(session)
                subtipo_id = _subtipo_id(
                    session,
                    tipo_id,
                    subtipo_deuda(nueva_direccion, EVENTO_DESEMBOLSO),
                )
                _actualizar_movimiento_sesion(
                    session,
                    movimiento,
                    monto=nuevo_monto
                    * signo_cuenta(nueva_direccion, EVENTO_DESEMBOLSO),
                    tipo_id=tipo_id,
                    subtipo_id=subtipo_id,
                    descripcion=nueva_descripcion,
                    fecha=nueva_fecha,
                )

        session.commit()
        session.refresh(deuda)

    return deuda


def editar_pago(
    user: User,
    deuda_id: int,
    pago_id: int,
    *,
    monto: Optional[float] = None,
    cuenta_id: Optional[int] = None,
    fecha: Optional[date] = None,
    descripcion: Optional[str] = None,
) -> PagoDeuda:
    with Session(engine) as session:
        deuda = _validar_deuda(session, deuda_id, user)
        pago = _validar_pago(session, deuda_id, pago_id, user)

        nuevo_monto = monto if monto is not None else pago.monto
        total_otros = total_abonos(session, deuda.id, excluir_pago_id=pago.id)
        pendiente_maximo = calcular_pendiente(deuda.monto_original, total_otros)
        if nuevo_monto != pago.monto:
            validar_abono(nuevo_monto, pendiente_maximo)

        nueva_cuenta = cuenta_id if cuenta_id is not None else pago.cuenta_id
        if cuenta_id is not None:
            _validar_cuenta(session, cuenta_id, user)
        nueva_fecha = fecha if fecha is not None else pago.fecha
        nueva_descripcion = (
            descripcion if descripcion is not None else pago.descripcion
        )

        pendiente_restante = pendiente_maximo - nuevo_monto
        tipo_id = _tipo_deudas_id(session)
        subtipo_id = _subtipo_id(
            session,
            tipo_id,
            subtipo_deuda(
                deuda.direccion,
                EVENTO_PAGO,
                es_pago_final(pendiente_restante),
            ),
        )

        movimiento = session.get(Movimiento, pago.movimiento_id)
        if movimiento is None:
            raise ValueError(f"Movimiento {pago.movimiento_id} no encontrado")

        _actualizar_movimiento_sesion(
            session,
            movimiento,
            monto=nuevo_monto * signo_cuenta(deuda.direccion, EVENTO_PAGO),
            tipo_id=tipo_id,
            subtipo_id=subtipo_id,
            cuenta_id=nueva_cuenta,
            descripcion=nueva_descripcion,
            fecha=nueva_fecha,
        )

        pago.monto = nuevo_monto
        pago.cuenta_id = nueva_cuenta
        pago.fecha = nueva_fecha
        pago.descripcion = nueva_descripcion
        session.add(pago)
        session.commit()
        session.refresh(pago)

    return pago


def eliminar_pago(user: User, deuda_id: int, pago_id: int) -> bool:
    with Session(engine) as session:
        _validar_deuda(session, deuda_id, user)
        pago = _validar_pago(session, deuda_id, pago_id, user)

        movimiento = session.get(Movimiento, pago.movimiento_id)
        session.delete(pago)
        session.flush()
        if movimiento is not None:
            _eliminar_movimiento_sesion(session, movimiento)

        session.commit()

    return True


def eliminar_deuda(user: User, deuda_id: int) -> bool:
    with Session(engine) as session:
        deuda = _validar_deuda(session, deuda_id, user)
        pagos = session.exec(
            select(PagoDeuda).where(PagoDeuda.deuda_id == deuda.id)
        ).all()

        for pago in pagos:
            movimiento = session.get(Movimiento, pago.movimiento_id)
            session.delete(pago)
            session.flush()
            if movimiento is not None:
                _eliminar_movimiento_sesion(session, movimiento)

        if deuda.movimiento_inicial_id is not None:
            movimiento = session.get(Movimiento, deuda.movimiento_inicial_id)
            deuda.movimiento_inicial_id = None
            session.add(deuda)
            session.flush()
            if movimiento is not None:
                _eliminar_movimiento_sesion(session, movimiento)

        session.delete(deuda)
        session.commit()

    return True


def listar_deudas(
    user: User,
    entidad_id: Optional[int] = None,
    direccion: Optional[str] = None,
    estado: Optional[str] = None,
) -> list[dict]:
    with Session(engine) as session:
        condiciones = [Deuda.user_id == str(user.id)]
        if entidad_id is not None:
            condiciones.append(Deuda.entidad_id == entidad_id)
        if direccion is not None:
            validar_direccion(direccion)
            condiciones.append(Deuda.direccion == direccion)

        deudas = session.exec(
            select(Deuda)
            .where(*condiciones)
            .order_by(Deuda.fecha.desc(), Deuda.id.desc())
        ).all()
        abonos = abonos_por_deuda(session, str(user.id))

        resultados = []
        for deuda in deudas:
            total_deuda = abonos.get(deuda.id, 0.0)
            pendiente, estado_actual = pendiente_y_estado(deuda, total_deuda)
            if estado is not None and estado_actual != estado:
                continue
            resultados.append(
                {
                    "deuda": deuda,
                    "total_abonos": total_deuda,
                    "pendiente": pendiente,
                    "estado": estado_actual,
                }
            )

    return resultados
