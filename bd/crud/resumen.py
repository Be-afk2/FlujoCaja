from datetime import date
from typing import Optional

from sqlmodel import Session, func, select

from bd.database import engine
from bd.models import Cuenta, Movimiento, ResumenMensual, User


def _get_o_crear(session: Session, user_id: str, cuenta_id: int, anio: int, mes: int) -> ResumenMensual | None:
    resumen = session.exec(
        select(ResumenMensual).where(
            ResumenMensual.user_id == user_id,
            ResumenMensual.cuenta_id == cuenta_id,
            ResumenMensual.anio == anio,
            ResumenMensual.mes == mes,
        )
    ).first()

    if resumen is None:
        return None

    return resumen


def _crear_resumen(session: Session, user_id: str, cuenta_id: int, anio: int, mes: int) -> ResumenMensual:
    resumen = ResumenMensual(
        user_id=user_id,
        cuenta_id=cuenta_id,
        anio=anio,
        mes=mes,
    )
    session.add(resumen)
    return resumen


def _limpiar_si_cero(session: Session, r: ResumenMensual) -> None:
    if (
        r.total_ingresos == 0
        and r.total_gastos == 0
        and r.total_ingresos_deuda == 0
        and r.total_gastos_deuda == 0
    ):
        session.delete(r)


def actualizar_por_movimiento(
    session: Session,
    user_id: str,
    cuenta_id: int,
    monto: float,
    fecha: date,
    *,
    old_monto: Optional[float] = None,
    old_cuenta_id: Optional[int] = None,
    old_fecha: Optional[date] = None,
    es_deuda: bool = False,
    old_es_deuda: bool = False,
) -> None:
    if old_monto is not None:
        old_cid = old_cuenta_id if old_cuenta_id is not None else cuenta_id
        old_y = old_fecha.year if old_fecha is not None else fecha.year
        old_m = old_fecha.month if old_fecha is not None else fecha.month
        r = _get_o_crear(session, user_id, old_cid, old_y, old_m)
        if r is not None:
            if old_monto > 0:
                r.total_ingresos -= old_monto
                if old_es_deuda:
                    r.total_ingresos_deuda -= old_monto
            else:
                r.total_gastos -= abs(old_monto)
                if old_es_deuda:
                    r.total_gastos_deuda -= abs(old_monto)
            r.neto = r.total_ingresos - r.total_gastos
            _limpiar_si_cero(session, r)

    if monto != 0:
        r = _get_o_crear(session, user_id, cuenta_id, fecha.year, fecha.month)
        if r is None:
            r = _crear_resumen(session, user_id, cuenta_id, fecha.year, fecha.month)
        if monto > 0:
            r.total_ingresos += monto
            if es_deuda:
                r.total_ingresos_deuda += monto
        else:
            r.total_gastos += abs(monto)
            if es_deuda:
                r.total_gastos_deuda += abs(monto)
        r.neto = r.total_ingresos - r.total_gastos


def recalcular_mes(session: Session, user_id: str, cuenta_id: int, anio: int, mes: int) -> ResumenMensual | None:
    resultados = session.exec(
        select(Movimiento.monto, Movimiento.es_deuda).where(
            Movimiento.user_id == user_id,
            Movimiento.cuenta_id == cuenta_id,
            func.extract("year", Movimiento.fecha) == anio,
            func.extract("month", Movimiento.fecha) == mes,
        )
    ).all()

    total_ingresos = sum(m for m, _ in resultados if m > 0)
    total_gastos = sum(abs(m) for m, _ in resultados if m < 0)
    total_ingresos_deuda = sum(m for m, es_deuda in resultados if es_deuda and m > 0)
    total_gastos_deuda = sum(abs(m) for m, es_deuda in resultados if es_deuda and m < 0)

    resumen = _get_o_crear(session, user_id, cuenta_id, anio, mes)

    if resumen is None:
        if (
            total_ingresos == 0
            and total_gastos == 0
            and total_ingresos_deuda == 0
            and total_gastos_deuda == 0
        ):
            return None
        resumen = _crear_resumen(session, user_id, cuenta_id, anio, mes)

    resumen.total_ingresos = total_ingresos
    resumen.total_gastos = total_gastos
    resumen.total_ingresos_deuda = total_ingresos_deuda
    resumen.total_gastos_deuda = total_gastos_deuda
    resumen.neto = total_ingresos - total_gastos

    if total_ingresos == 0 and total_gastos == 0:
        session.delete(resumen)
        return None

    return resumen


def recalcular_todos(user: User) -> int:
    with Session(engine) as session:
        filas = session.exec(
            select(
                Movimiento.cuenta_id,
                func.extract("year", Movimiento.fecha),
                func.extract("month", Movimiento.fecha),
            )
            .where(Movimiento.user_id == str(user.id))
            .distinct()
        ).all()

        for r in session.exec(select(ResumenMensual).where(ResumenMensual.user_id == str(user.id))).all():
            session.delete(r)
        session.flush()

        count = 0
        for cuenta_id, anio, mes in filas:
            recalcular_mes(session, str(user.id), int(cuenta_id), int(anio), int(mes))
            count += 1

        session.commit()

    return count


def _filtro_moneda(moneda_id: Optional[int], user_id: str) -> list:
    """Devuelve condiciones extra para filtrar resúmenes por moneda de la cuenta."""
    if moneda_id is None:
        return []
    subquery = select(Cuenta.id).where(
        Cuenta.moneda_id == moneda_id,
        Cuenta.user_id == user_id,
    )
    return [ResumenMensual.cuenta_id.in_(subquery)]


def get_resumenes_anual(user: User, anio: int, moneda_id: Optional[int] = None) -> list[ResumenMensual]:
    with Session(engine) as session:
        condiciones = [
            ResumenMensual.user_id == str(user.id),
            ResumenMensual.anio == anio,
            *_filtro_moneda(moneda_id, str(user.id)),
        ]
        return session.exec(select(ResumenMensual).where(*condiciones)).all()


def get_resumen_mensual(
    user: User, anio: int, mes: int, moneda_id: Optional[int] = None
) -> list[ResumenMensual]:
    with Session(engine) as session:
        condiciones = [
            ResumenMensual.user_id == str(user.id),
            ResumenMensual.anio == anio,
            ResumenMensual.mes == mes,
            *_filtro_moneda(moneda_id, str(user.id)),
        ]
        return session.exec(select(ResumenMensual).where(*condiciones)).all()


def get_resumen_rango(
    user: User,
    desde_anio: int,
    desde_mes: int,
    hasta_anio: int,
    hasta_mes: int,
    moneda_id: Optional[int] = None,
) -> list[ResumenMensual]:
    with Session(engine) as session:
        condiciones = [
            ResumenMensual.user_id == str(user.id),
            *_filtro_moneda(moneda_id, str(user.id)),
        ]

        if desde_anio == hasta_anio:
            condiciones.append(ResumenMensual.anio == desde_anio)
            condiciones.append(ResumenMensual.mes >= desde_mes)
            condiciones.append(ResumenMensual.mes <= hasta_mes)
        else:
            condiciones.append(
                ((ResumenMensual.anio == desde_anio) & (ResumenMensual.mes >= desde_mes))
                | ((ResumenMensual.anio > desde_anio) & (ResumenMensual.anio < hasta_anio))
                | ((ResumenMensual.anio == hasta_anio) & (ResumenMensual.mes <= hasta_mes))
            )

        return session.exec(select(ResumenMensual).where(*condiciones)).all()
