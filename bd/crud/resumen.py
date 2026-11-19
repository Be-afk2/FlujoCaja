from datetime import date
from typing import Optional

from sqlalchemy import case, delete
from sqlmodel import Session, and_, func, select

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


def _rango_mes(anio: int, mes: int) -> tuple[date, date]:
    """Primer dia del mes y primer dia del mes siguiente (rango half-open)."""
    inicio = date(anio, mes, 1)
    fin = date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)
    return inicio, fin


def recalcular_mes(session: Session, user_id: str, cuenta_id: int, anio: int, mes: int) -> ResumenMensual | None:
    inicio, fin = _rango_mes(anio, mes)
    resultados = session.exec(
        select(Movimiento.monto, Movimiento.es_deuda).where(
            Movimiento.user_id == user_id,
            Movimiento.cuenta_id == cuenta_id,
            Movimiento.fecha >= inicio,
            Movimiento.fecha < fin,
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
    """Recalcula todos los resumenes del usuario en una sola pasada.

    Agrega los movimientos con un unico GROUP BY por (cuenta, anio, mes) y
    reescribe la tabla de resumenes. Antes se hacia una consulta por cada
    combinacion (N+1), lo que hacia el costo cuadratico con la cantidad de
    movimientos.
    """
    user_id = str(user.id)
    anio = func.extract("year", Movimiento.fecha)
    mes = func.extract("month", Movimiento.fecha)
    ingresos = func.sum(
        case((Movimiento.monto > 0, Movimiento.monto), else_=0.0)
    )
    gastos = func.sum(
        case((Movimiento.monto < 0, -Movimiento.monto), else_=0.0)
    )
    ingresos_deuda = func.sum(
        case(
            (and_(Movimiento.es_deuda, Movimiento.monto > 0), Movimiento.monto),
            else_=0.0,
        )
    )
    gastos_deuda = func.sum(
        case(
            (and_(Movimiento.es_deuda, Movimiento.monto < 0), -Movimiento.monto),
            else_=0.0,
        )
    )

    with Session(engine) as session:
        filas = session.exec(
            select(
                Movimiento.cuenta_id,
                anio,
                mes,
                ingresos,
                gastos,
                ingresos_deuda,
                gastos_deuda,
            )
            .where(Movimiento.user_id == user_id)
            .group_by(Movimiento.cuenta_id, anio, mes)
        ).all()

        session.execute(delete(ResumenMensual).where(ResumenMensual.user_id == user_id))

        creados = 0
        for cuenta_id, f_anio, f_mes, ing, gas, ing_deuda, gas_deuda in filas:
            ing = float(ing or 0.0)
            gas = float(gas or 0.0)
            ing_deuda = float(ing_deuda or 0.0)
            gas_deuda = float(gas_deuda or 0.0)
            if (
                ing == 0
                and gas == 0
                and ing_deuda == 0
                and gas_deuda == 0
            ):
                continue

            session.add(
                ResumenMensual(
                    user_id=user_id,
                    cuenta_id=int(cuenta_id),
                    anio=int(f_anio),
                    mes=int(f_mes),
                    total_ingresos=ing,
                    total_gastos=gas,
                    total_ingresos_deuda=ing_deuda,
                    total_gastos_deuda=gas_deuda,
                    neto=ing - gas,
                )
            )
            creados += 1

        session.commit()

    return creados


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
