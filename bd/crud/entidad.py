from datetime import date
from typing import Optional

from sqlmodel import Session, select

from bd.crud.deuda import abonos_por_deuda, pendiente_y_estado
from bd.crud.deudaMensual import resumen_deuda_mensual
from bd.crud.exceptions import RecursoNoEncontradoError
from bd.database import engine
from bd.domain.deuda import calcular_saldos_por_moneda, validar_tipo_entidad
from bd.models import (
    CuotaMensual,
    Deuda,
    DeudaMensual,
    Entidad,
    PagoCuotaMensual,
    PagoDeuda,
    User,
)


def _validar_entidad(session: Session, entidad_id: int, user: User) -> Entidad:
    entidad = session.get(Entidad, entidad_id)
    if not entidad or entidad.user_id != str(user.id):
        raise RecursoNoEncontradoError(f"Entidad {entidad_id} no encontrada")
    return entidad


def _normalizar_nombre(nombre: str) -> str:
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El nombre de la entidad no puede estar vacio")
    return nombre


def crear_entidad(
    user: User,
    nombre: str,
    tipo: str = "persona",
    descripcion: Optional[str] = None,
) -> Entidad:
    nombre = _normalizar_nombre(nombre)
    validar_tipo_entidad(tipo)

    with Session(engine) as session:
        entidad = Entidad(
            user_id=str(user.id),
            nombre=nombre,
            tipo=tipo,
            descripcion=descripcion,
        )
        session.add(entidad)
        session.commit()
        session.refresh(entidad)

    return entidad


def editar_entidad(
    user: User,
    entidad_id: int,
    *,
    nombre: Optional[str] = None,
    tipo: Optional[str] = None,
    descripcion: Optional[str] = None,
) -> Entidad:
    if tipo is not None:
        validar_tipo_entidad(tipo)
    if nombre is not None:
        nombre = _normalizar_nombre(nombre)

    with Session(engine) as session:
        entidad = _validar_entidad(session, entidad_id, user)
        if nombre is not None:
            entidad.nombre = nombre
        if tipo is not None:
            entidad.tipo = tipo
        if descripcion is not None:
            entidad.descripcion = descripcion

        session.add(entidad)
        session.commit()
        session.refresh(entidad)

    return entidad


def eliminar_entidad(user: User, entidad_id: int) -> bool:
    with Session(engine) as session:
        entidad = _validar_entidad(session, entidad_id, user)
        deuda = session.exec(
            select(Deuda).where(Deuda.entidad_id == entidad.id)
        ).first()
        if deuda is not None:
            raise ValueError("No se puede eliminar una entidad con deudas")

        deuda_mensual = session.exec(
            select(DeudaMensual).where(
                DeudaMensual.entidad_id == entidad.id
            )
        ).first()
        if deuda_mensual is not None:
            raise ValueError(
                "No se puede eliminar una entidad con deudas mensuales"
            )

        session.delete(entidad)
        session.commit()

    return True


def _deudas_mensuales_por_entidad(
    session: Session,
    user_id: str,
    hoy: date,
    incluir_pagos: bool = False,
) -> dict[int, list[dict]]:
    """Carga las plantillas mensuales asociadas y sus cuotas por entidad."""
    deudas = session.exec(
        select(DeudaMensual).where(
            DeudaMensual.user_id == user_id,
            DeudaMensual.entidad_id.is_not(None),
        )
    ).all()
    if not deudas:
        return {}

    cuotas = session.exec(
        select(CuotaMensual)
        .where(
            CuotaMensual.deuda_mensual_id.in_(
                [deuda.id for deuda in deudas]
            )
        )
        .order_by(CuotaMensual.numero)
    ).all()
    cuotas_por_deuda: dict[int, list[CuotaMensual]] = {}
    for cuota in cuotas:
        cuotas_por_deuda.setdefault(cuota.deuda_mensual_id, []).append(cuota)

    pagos_por_cuota: dict[int, list[PagoCuotaMensual]] = {}
    if incluir_pagos and cuotas:
        pagos = session.exec(
            select(PagoCuotaMensual)
            .where(
                PagoCuotaMensual.cuota_id.in_(
                    [cuota.id for cuota in cuotas]
                )
            )
            .order_by(PagoCuotaMensual.fecha)
        ).all()
        for pago in pagos:
            pagos_por_cuota.setdefault(pago.cuota_id, []).append(pago)

    resultado: dict[int, list[dict]] = {}
    for deuda in deudas:
        cuotas_deuda = cuotas_por_deuda.get(deuda.id, [])
        if incluir_pagos:
            detalle = [
                {"cuota": cuota, "pagos": pagos_por_cuota.get(cuota.id, [])}
                for cuota in cuotas_deuda
            ]
        else:
            detalle = cuotas_deuda
        resultado.setdefault(deuda.entidad_id, []).append(
            {
                "deuda_mensual": deuda,
                "cuotas": detalle,
                **resumen_deuda_mensual(deuda, cuotas_deuda, hoy),
            }
        )
    return resultado


def _resumen_entidad(
    entidad: Entidad,
    deudas: list[Deuda],
    abonos: dict[int, float],
    deudas_mensuales: Optional[list[dict]] = None,
    hoy: Optional[date] = None,
) -> dict:
    deudas_mensuales = deudas_mensuales or []
    hoy = hoy or date.today()
    deudas_detalle = []
    pendientes = 0
    proximo_vencimiento = None

    for deuda in deudas:
        total_deuda = abonos.get(deuda.id, 0.0)
        pendiente, estado = pendiente_y_estado(deuda, total_deuda, hoy)
        if estado != "pagada":
            pendientes += 1
            if deuda.vencimiento is not None and (
                proximo_vencimiento is None or deuda.vencimiento < proximo_vencimiento
            ):
                proximo_vencimiento = deuda.vencimiento
        deudas_detalle.append(
            {
                "deuda": deuda,
                "total_abonos": total_deuda,
                "pendiente": pendiente,
                "estado": estado,
            }
        )

    for item in deudas_mensuales:
        if item["pendiente"] > 0:
            pendientes += 1
        for entry in item["cuotas"]:
            cuota = entry["cuota"] if isinstance(entry, dict) else entry
            if cuota.estado != "pendiente":
                continue
            if (
                proximo_vencimiento is None
                or cuota.fecha_limite < proximo_vencimiento
            ):
                proximo_vencimiento = cuota.fecha_limite

    saldos = calcular_saldos_por_moneda(
        [
            (item["deuda"].moneda_id, item["deuda"].direccion, item["pendiente"])
            for item in deudas_detalle
            if item["estado"] != "pagada"
        ]
        + [
            (item["deuda_mensual"].moneda_id, "pagar", item["pendiente"])
            for item in deudas_mensuales
            if item["pendiente"] > 0
        ]
    )

    return {
        "entidad": entidad,
        "deudas": deudas_detalle,
        "deudas_mensuales": deudas_mensuales,
        "saldos": saldos,
        "deudas_pendientes": pendientes,
        "proximo_vencimiento": proximo_vencimiento,
    }


def listar_entidades(user: User) -> list[dict]:
    hoy = date.today()
    with Session(engine) as session:
        entidades = session.exec(
            select(Entidad)
            .where(Entidad.user_id == str(user.id))
            .order_by(Entidad.nombre)
        ).all()
        deudas = session.exec(
            select(Deuda).where(Deuda.user_id == str(user.id))
        ).all()
        abonos = abonos_por_deuda(session, str(user.id))
        deudas_mensuales = _deudas_mensuales_por_entidad(
            session, str(user.id), hoy
        )

        deudas_por_entidad: dict[int, list[Deuda]] = {}
        for deuda in deudas:
            deudas_por_entidad.setdefault(deuda.entidad_id, []).append(deuda)

        return [
            _resumen_entidad(
                entidad,
                deudas_por_entidad.get(entidad.id, []),
                abonos,
                deudas_mensuales.get(entidad.id, []),
                hoy,
            )
            for entidad in entidades
        ]


def obtener_entidad(user: User, entidad_id: int) -> dict:
    hoy = date.today()
    with Session(engine) as session:
        entidad = _validar_entidad(session, entidad_id, user)
        deudas = session.exec(
            select(Deuda)
            .where(Deuda.entidad_id == entidad.id)
            .order_by(Deuda.fecha.desc(), Deuda.id.desc())
        ).all()
        abonos = abonos_por_deuda(session, str(user.id))
        deudas_mensuales = _deudas_mensuales_por_entidad(
            session, str(user.id), hoy, incluir_pagos=True
        ).get(entidad.id, [])

        resumen = _resumen_entidad(
            entidad, deudas, abonos, deudas_mensuales, hoy
        )
        pagos_por_deuda: dict[int, list[PagoDeuda]] = {}
        for pago in session.exec(
            select(PagoDeuda)
            .where(PagoDeuda.user_id == str(user.id))
            .order_by(PagoDeuda.fecha)
        ).all():
            pagos_por_deuda.setdefault(pago.deuda_id, []).append(pago)

        for item in resumen["deudas"]:
            item["pagos"] = pagos_por_deuda.get(item["deuda"].id, [])

        return resumen
