"""CRUD de deudas mensuales, cuotas y pagos (Fase 10.3).

Las reglas puras (fechas, montos, estados y prioridad) viven en
``bd.domain.deuda_mensual``. Este modulo orquesta la persistencia y reutiliza
los helpers de ``bd.crud.movimiento`` para crear/editar/eliminar movimientos,
actualizando saldo de cuenta y ``ResumenMensual`` en la misma transaccion.
"""

from datetime import date, timedelta
from typing import Optional

from sqlmodel import Session, select

from bd.crud.exceptions import RecursoNoEncontradoError
from bd.crud.movimiento import (
    _actualizar_movimiento_sesion,
    _crear_movimiento_sesion,
    _eliminar_movimiento_sesion,
)
from bd.database import engine
from bd.domain.deuda import monedas_distintas
from bd.domain.deuda_mensual import (
    ESTADO_CUOTA_CANCELADA,
    ESTADO_CUOTA_PAGADA,
    ESTADO_CUOTA_PENDIENTE,
    ESTADO_DEUDA_ACTIVA,
    ESTADO_DEUDA_CANCELADA,
    ESTADOS_DEUDA_MENSUAL,
    MODALIDAD_CUOTAS,
    MODALIDAD_RECURRENTE,
    MODALIDADES,
    MONTO_MODO_CALCULADO,
    MONTO_MODO_FIJO,
    CuotaCalculada,
    clave_prioridad,
    debe_cancelarse,
    es_vencida,
    estado_pago_cuota,
    fechas_cuota,
    generar_cuotas_plan,
    generar_cuotas_recurrente,
    monto_cuota_plan,
    monto_movimiento_pago,
    puede_editarse,
    ultimo_dia_mes,
    validar_monto_cuota,
    validar_monto_pago,
    validar_plantilla,
)
from bd.models import (
    Cuenta,
    CuotaMensual,
    DeudaMensual,
    Entidad,
    Moneda,
    Movimiento,
    PagoCuotaMensual,
    Subtipo,
    Tipo,
    User,
)

DIAS_PROXIMAS_DEFAULT = 7


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------


def _validar_deuda_mensual(
    session: Session, deuda_mensual_id: int, user: User
) -> DeudaMensual:
    deuda = session.get(DeudaMensual, deuda_mensual_id)
    if not deuda or deuda.user_id != str(user.id):
        raise RecursoNoEncontradoError(
            f"Deuda mensual {deuda_mensual_id} no encontrada"
        )
    return deuda


def _validar_cuota(session: Session, cuota_id: int, user: User) -> CuotaMensual:
    cuota = session.get(CuotaMensual, cuota_id)
    if not cuota or cuota.user_id != str(user.id):
        raise RecursoNoEncontradoError(f"Cuota {cuota_id} no encontrada")
    return cuota


def _validar_pago(
    session: Session, cuota_id: int, pago_id: int, user: User
) -> PagoCuotaMensual:
    pago = session.get(PagoCuotaMensual, pago_id)
    if not pago or pago.user_id != str(user.id) or pago.cuota_id != cuota_id:
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


def _validar_tipo(session: Session, tipo_id: int) -> Tipo:
    tipo = session.get(Tipo, tipo_id)
    if not tipo:
        raise ValueError(f"Tipo {tipo_id} no existe")
    return tipo


def _validar_subtipo(
    session: Session, subtipo_id: Optional[int], tipo_id: int
) -> None:
    if subtipo_id is None:
        return
    subtipo = session.get(Subtipo, subtipo_id)
    if not subtipo:
        raise ValueError(f"Subtipo {subtipo_id} no existe")
    if subtipo.tipo_id != tipo_id:
        raise ValueError(f"Subtipo {subtipo_id} no pertenece al tipo {tipo_id}")


def _validar_entidad(
    session: Session, entidad_id: Optional[int], user: User
) -> Optional[Entidad]:
    if entidad_id is None:
        return None
    entidad = session.get(Entidad, entidad_id)
    if not entidad or entidad.user_id != str(user.id):
        raise RecursoNoEncontradoError(f"Entidad {entidad_id} no encontrada")
    return entidad


def _resolver_montos(
    modalidad: str,
    *,
    monto_cuota: Optional[float],
    monto_total: Optional[float],
    cuotas_totales: Optional[int],
) -> tuple[str, float, Optional[float], Optional[int]]:
    if modalidad == MODALIDAD_RECURRENTE:
        if monto_cuota is None:
            raise ValueError("Una deuda recurrente requiere monto_cuota")
        validar_monto_cuota(monto_cuota)
        return MONTO_MODO_FIJO, monto_cuota, None, None

    if modalidad != MODALIDAD_CUOTAS:
        raise ValueError(f"Modalidad invalida: {modalidad!r}")
    if monto_total is None or cuotas_totales is None:
        raise ValueError("Un plan de cuotas requiere monto_total y cuotas_totales")
    return MONTO_MODO_CALCULADO, monto_cuota_plan(
        monto_total, cuotas_totales
    ), monto_total, cuotas_totales


# ---------------------------------------------------------------------------
# Cuotas
# ---------------------------------------------------------------------------


def _calcular_cuotas(deuda: DeudaMensual, hoy: Optional[date] = None) -> list[CuotaCalculada]:
    if deuda.modalidad == MODALIDAD_RECURRENTE:
        return generar_cuotas_recurrente(
            deuda.fecha_inicio,
            deuda.dia_aparicion,
            deuda.dia_limite,
            deuda.monto_cuota,
            hoy=hoy,
        )
    return generar_cuotas_plan(
        deuda.fecha_inicio,
        deuda.dia_aparicion,
        deuda.dia_limite,
        deuda.monto_total or 0.0,
        deuda.cuotas_totales or 0,
    )


def _crear_cuotas_sesion(
    session: Session,
    deuda: DeudaMensual,
    calculadas: list[CuotaCalculada],
) -> list[CuotaMensual]:
    cuotas: list[CuotaMensual] = []
    for item in calculadas:
        cuota = CuotaMensual(
            user_id=deuda.user_id,
            deuda_mensual_id=deuda.id,
            numero=item.numero,
            anio=item.anio,
            mes=item.mes,
            fecha_aparicion=item.fecha_aparicion,
            fecha_limite=item.fecha_limite,
            monto=item.monto,
            estado=ESTADO_CUOTA_PENDIENTE,
        )
        session.add(cuota)
        cuotas.append(cuota)
    session.flush()
    return cuotas


def _numeros_existentes(session: Session, deuda_mensual_id: int) -> set[int]:
    return _numeros_por_deuda(session, [deuda_mensual_id]).get(
        deuda_mensual_id, set()
    )


def _numeros_por_deuda(
    session: Session, deuda_ids: list[int]
) -> dict[int, set[int]]:
    """Numeros de cuota ya creados para varias plantillas en una sola consulta."""
    if not deuda_ids:
        return {}

    filas = session.exec(
        select(CuotaMensual.deuda_mensual_id, CuotaMensual.numero).where(
            CuotaMensual.deuda_mensual_id.in_(deuda_ids)
        )
    ).all()

    numeros: dict[int, set[int]] = {}
    for deuda_id, numero in filas:
        numeros.setdefault(int(deuda_id), set()).add(int(numero))
    return numeros


def _sincronizar_cuotas_sesion(
    session: Session,
    deuda: DeudaMensual,
    hoy: Optional[date] = None,
    *,
    existentes: Optional[set[int]] = None,
) -> int:
    """Genera las cuotas que falten sin hacer commit."""
    if deuda.estado != ESTADO_DEUDA_ACTIVA:
        return 0

    hoy = hoy or date.today()
    calculadas = _calcular_cuotas(deuda, hoy)
    if existentes is None:
        existentes = _numeros_existentes(session, deuda.id)
    faltantes = [c for c in calculadas if c.numero not in existentes]
    if not faltantes:
        return 0

    _crear_cuotas_sesion(session, deuda, faltantes)
    return len(faltantes)


def sincronizar_cuotas_sesion(
    session: Session,
    deudas: list[DeudaMensual],
    hoy: Optional[date] = None,
) -> int:
    """Genera las cuotas faltantes de varias plantillas sin hacer commit.

    Los numeros existentes se cargan en una sola consulta (`IN (...)`) en
    lugar de una por plantilla.
    """
    hoy = hoy or date.today()
    numeros = _numeros_por_deuda(session, [deuda.id for deuda in deudas])
    total = 0
    for deuda in deudas:
        total += _sincronizar_cuotas_sesion(
            session, deuda, hoy, existentes=numeros.get(deuda.id, set())
        )
    return total


def sincronizar_deudas_mensuales(user: User, hoy: Optional[date] = None) -> int:
    """Genera las cuotas faltantes del usuario y persiste solo si hubo cambios."""
    hoy = hoy or date.today()
    with Session(engine) as session:
        deudas = session.exec(
            select(DeudaMensual).where(
                DeudaMensual.user_id == str(user.id),
                DeudaMensual.estado == ESTADO_DEUDA_ACTIVA,
            )
        ).all()
        creadas = sincronizar_cuotas_sesion(session, deudas, hoy)
        if creadas:
            session.commit()
        return creadas


def _cuotas_por_deuda(
    session: Session, deuda_ids: list[int]
) -> dict[int, list[CuotaMensual]]:
    if not deuda_ids:
        return {}
    cuotas = session.exec(
        select(CuotaMensual)
        .where(CuotaMensual.deuda_mensual_id.in_(deuda_ids))
        .order_by(CuotaMensual.numero)
    ).all()
    agrupadas: dict[int, list[CuotaMensual]] = {}
    for cuota in cuotas:
        agrupadas.setdefault(cuota.deuda_mensual_id, []).append(cuota)
    return agrupadas


# ---------------------------------------------------------------------------
# Agregados
# ---------------------------------------------------------------------------


def monto_pendiente(
    deuda: DeudaMensual,
    cuota: CuotaMensual,
    hoy: Optional[date] = None,
) -> float:
    """Pendiente segun la regla de la Fase 10.4.

    Recurrente: solo cuotas ya aparecidas. Plan: todas las impagas.
    """
    hoy = hoy or date.today()
    if cuota.estado != ESTADO_CUOTA_PENDIENTE:
        return 0.0
    if deuda.modalidad == MODALIDAD_RECURRENTE and cuota.fecha_aparicion > hoy:
        return 0.0
    return cuota.monto


def resumen_deuda_mensual(
    deuda: DeudaMensual,
    cuotas: list[CuotaMensual],
    hoy: Optional[date] = None,
) -> dict:
    hoy = hoy or date.today()
    pendientes = [c for c in cuotas if c.estado == ESTADO_CUOTA_PENDIENTE]
    vencidas = [
        c for c in pendientes if es_vencida(c.estado, c.fecha_limite, hoy)
    ]
    proximas = [c for c in pendientes if c.fecha_limite >= hoy]
    proxima = min(proximas, key=lambda c: c.fecha_limite) if proximas else None

    return {
        "pendiente": round(
            sum(monto_pendiente(deuda, c, hoy) for c in cuotas), 2
        ),
        "pagado": round(
            sum(c.monto for c in cuotas if c.estado == ESTADO_CUOTA_PAGADA),
            2,
        ),
        "vencidas": len(vencidas),
        "vencidas_monto": round(sum(c.monto for c in vencidas), 2),
        "proxima": proxima,
    }


# ---------------------------------------------------------------------------
# Plantillas
# ---------------------------------------------------------------------------


def crear_deuda_mensual(
    user: User,
    *,
    modalidad: str,
    tipo_id: int,
    moneda_id: int,
    dia_aparicion: int,
    dia_limite: int,
    descripcion: Optional[str] = None,
    monto_cuota: Optional[float] = None,
    monto_total: Optional[float] = None,
    cuotas_totales: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    entidad_id: Optional[int] = None,
    subtipo_id: Optional[int] = None,
    cuenta_pago_default_id: Optional[int] = None,
) -> DeudaMensual:
    if modalidad not in MODALIDADES:
        raise ValueError(f"Modalidad invalida: {modalidad!r}. Use {MODALIDADES}")

    monto_modo, monto_cuota_final, monto_total_final, cuotas_final = (
        _resolver_montos(
            modalidad,
            monto_cuota=monto_cuota,
            monto_total=monto_total,
            cuotas_totales=cuotas_totales,
        )
    )
    validar_plantilla(
        modalidad=modalidad,
        monto_modo=monto_modo,
        monto_cuota=monto_cuota_final,
        monto_total=monto_total_final,
        cuotas_totales=cuotas_final,
        dia_aparicion=dia_aparicion,
        dia_limite=dia_limite,
    )

    with Session(engine) as session:
        _validar_moneda(session, moneda_id)
        _validar_tipo(session, tipo_id)
        _validar_subtipo(session, subtipo_id, tipo_id)
        _validar_entidad(session, entidad_id, user)
        if cuenta_pago_default_id is not None:
            _validar_cuenta(session, cuenta_pago_default_id, user)

        deuda = DeudaMensual(
            user_id=str(user.id),
            entidad_id=entidad_id,
            tipo_id=tipo_id,
            subtipo_id=subtipo_id,
            moneda_id=moneda_id,
            descripcion=descripcion,
            modalidad=modalidad,
            monto_modo=monto_modo,
            monto_cuota=monto_cuota_final,
            monto_total=monto_total_final,
            cuotas_totales=cuotas_final,
            dia_aparicion=dia_aparicion,
            dia_limite=dia_limite,
            fecha_inicio=fecha_inicio or date.today(),
            estado=ESTADO_DEUDA_ACTIVA,
            cuenta_pago_default_id=cuenta_pago_default_id,
        )
        session.add(deuda)
        session.flush()

        _crear_cuotas_sesion(session, deuda, _calcular_cuotas(deuda))
        session.commit()
        session.refresh(deuda)

    return deuda


def editar_deuda_mensual(
    user: User,
    deuda_mensual_id: int,
    *,
    descripcion: Optional[str] = None,
    entidad_id: Optional[int] = None,
    tipo_id: Optional[int] = None,
    subtipo_id: Optional[int] = None,
    cuenta_pago_default_id: Optional[int] = None,
    dia_aparicion: Optional[int] = None,
    dia_limite: Optional[int] = None,
    monto_cuota: Optional[float] = None,
    monto_total: Optional[float] = None,
    cuotas_totales: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    modalidad: Optional[str] = None,
) -> DeudaMensual:
    """Edita la plantilla.

    Los cambios estructurales (modalidad, fecha_inicio, cuotas_totales,
    monto_total) solo se permiten si no hay pagos. Los demas cambios solo
    afectan cuotas futuras impagas; las pagadas nunca cambian.
    """
    with Session(engine) as session:
        deuda = _validar_deuda_mensual(session, deuda_mensual_id, user)
        hoy = date.today()
        dia_aparicion_anterior = deuda.dia_aparicion
        dia_limite_anterior = deuda.dia_limite

        nuevo_tipo_id = tipo_id if tipo_id is not None else deuda.tipo_id
        nuevo_subtipo_id = (
            subtipo_id if subtipo_id is not None else deuda.subtipo_id
        )
        _validar_tipo(session, nuevo_tipo_id)
        if (
            tipo_id is not None
            and subtipo_id is None
            and deuda.subtipo_id is not None
        ):
            subtipo_actual = session.get(Subtipo, deuda.subtipo_id)
            if subtipo_actual and subtipo_actual.tipo_id != nuevo_tipo_id:
                nuevo_subtipo_id = None
        _validar_subtipo(session, nuevo_subtipo_id, nuevo_tipo_id)

        if entidad_id is not None:
            _validar_entidad(session, entidad_id, user)
        if cuenta_pago_default_id is not None:
            _validar_cuenta(session, cuenta_pago_default_id, user)

        cambios_estructurales = (
            (modalidad is not None and modalidad != deuda.modalidad)
            or (fecha_inicio is not None and fecha_inicio != deuda.fecha_inicio)
            or (
                cuotas_totales is not None
                and cuotas_totales != deuda.cuotas_totales
            )
            or (
                monto_total is not None
                and monto_total != deuda.monto_total
            )
        )
        tiene_pagos = session.exec(
            select(PagoCuotaMensual.id)
            .join(
                CuotaMensual,
                PagoCuotaMensual.cuota_id == CuotaMensual.id,
            )
            .where(CuotaMensual.deuda_mensual_id == deuda.id)
            .limit(1)
        ).first() is not None
        if cambios_estructurales and tiene_pagos:
            raise ValueError(
                "No se puede cambiar modalidad, fecha de inicio, cuotas "
                "totales ni monto total con pagos registrados"
            )

        nueva_modalidad = modalidad or deuda.modalidad
        if modalidad is not None and modalidad not in MODALIDADES:
            raise ValueError(
                f"Modalidad invalida: {modalidad!r}. Use {MODALIDADES}"
            )

        if nueva_modalidad == MODALIDAD_RECURRENTE:
            if monto_total is not None or cuotas_totales is not None:
                raise ValueError(
                    "Una deuda recurrente no usa monto_total ni cuotas_totales"
                )
            nuevo_monto_modo = MONTO_MODO_FIJO
            nuevo_monto_total = None
            nuevas_cuotas_totales = None
            nuevo_monto_cuota = (
                monto_cuota if monto_cuota is not None else deuda.monto_cuota
            )
        else:
            if monto_cuota is not None:
                raise ValueError(
                    "En un plan el monto de la cuota se deriva de "
                    "monto_total y cuotas_totales"
                )
            nuevo_monto_modo = MONTO_MODO_CALCULADO
            nuevo_monto_total = (
                monto_total if monto_total is not None else deuda.monto_total
            )
            nuevas_cuotas_totales = (
                cuotas_totales
                if cuotas_totales is not None
                else deuda.cuotas_totales
            )
            if nuevo_monto_total is None or nuevas_cuotas_totales is None:
                raise ValueError(
                    "Un plan de cuotas requiere monto_total y cuotas_totales"
                )
            nuevo_monto_cuota = monto_cuota_plan(
                nuevo_monto_total, nuevas_cuotas_totales
            )

        nuevo_dia_aparicion = (
            dia_aparicion if dia_aparicion is not None else deuda.dia_aparicion
        )
        nuevo_dia_limite = (
            dia_limite if dia_limite is not None else deuda.dia_limite
        )
        validar_plantilla(
            modalidad=nueva_modalidad,
            monto_modo=nuevo_monto_modo,
            monto_cuota=nuevo_monto_cuota,
            monto_total=nuevo_monto_total,
            cuotas_totales=nuevas_cuotas_totales,
            dia_aparicion=nuevo_dia_aparicion,
            dia_limite=nuevo_dia_limite,
        )

        deuda.modalidad = nueva_modalidad
        deuda.monto_modo = nuevo_monto_modo
        deuda.monto_cuota = nuevo_monto_cuota
        deuda.monto_total = nuevo_monto_total
        deuda.cuotas_totales = nuevas_cuotas_totales
        deuda.dia_aparicion = nuevo_dia_aparicion
        deuda.dia_limite = nuevo_dia_limite
        deuda.tipo_id = nuevo_tipo_id
        deuda.subtipo_id = nuevo_subtipo_id
        if descripcion is not None:
            deuda.descripcion = descripcion
        if entidad_id is not None:
            deuda.entidad_id = entidad_id
        if cuenta_pago_default_id is not None:
            deuda.cuenta_pago_default_id = cuenta_pago_default_id
        if fecha_inicio is not None:
            deuda.fecha_inicio = fecha_inicio
        session.add(deuda)

        if cambios_estructurales:
            for cuota in session.exec(
                select(CuotaMensual).where(
                    CuotaMensual.deuda_mensual_id == deuda.id
                )
            ).all():
                session.delete(cuota)
            session.flush()
            if deuda.estado == ESTADO_DEUDA_ACTIVA:
                _crear_cuotas_sesion(
                    session, deuda, _calcular_cuotas(deuda, hoy)
                )
        else:
            cambio_dias = (
                nuevo_dia_aparicion != dia_aparicion_anterior
                or nuevo_dia_limite != dia_limite_anterior
            )
            cambio_monto = (
                nueva_modalidad == MODALIDAD_RECURRENTE
                and monto_cuota is not None
            )
            if cambio_dias or cambio_monto:
                for cuota in session.exec(
                    select(CuotaMensual).where(
                        CuotaMensual.deuda_mensual_id == deuda.id
                    )
                ).all():
                    if not puede_editarse(
                        cuota.estado, cuota.fecha_aparicion, hoy
                    ):
                        continue
                    if cambio_dias:
                        (
                            cuota.fecha_aparicion,
                            cuota.fecha_limite,
                        ) = fechas_cuota(
                            cuota.anio,
                            cuota.mes,
                            nuevo_dia_aparicion,
                            nuevo_dia_limite,
                        )
                    if cambio_monto:
                        cuota.monto = nuevo_monto_cuota
                    session.add(cuota)

        _sincronizar_cuotas_sesion(session, deuda, hoy)
        session.commit()
        session.refresh(deuda)

    return deuda


def cancelar_deuda_mensual(
    user: User,
    deuda_mensual_id: int,
    hoy: Optional[date] = None,
) -> DeudaMensual:
    hoy = hoy or date.today()
    with Session(engine) as session:
        deuda = _validar_deuda_mensual(session, deuda_mensual_id, user)
        if deuda.estado != ESTADO_DEUDA_CANCELADA:
            deuda.estado = ESTADO_DEUDA_CANCELADA
            deuda.fecha_cancelacion = hoy
            session.add(deuda)

            for cuota in session.exec(
                select(CuotaMensual).where(
                    CuotaMensual.deuda_mensual_id == deuda.id
                )
            ).all():
                if debe_cancelarse(
                    cuota.estado, cuota.fecha_aparicion, hoy
                ):
                    cuota.estado = ESTADO_CUOTA_CANCELADA
                    session.add(cuota)

            session.commit()
            session.refresh(deuda)

    return deuda


def eliminar_deuda_mensual(user: User, deuda_mensual_id: int) -> bool:
    with Session(engine) as session:
        deuda = _validar_deuda_mensual(session, deuda_mensual_id, user)
        cuotas = session.exec(
            select(CuotaMensual).where(
                CuotaMensual.deuda_mensual_id == deuda.id
            )
        ).all()

        for cuota in cuotas:
            pagos = session.exec(
                select(PagoCuotaMensual).where(
                    PagoCuotaMensual.cuota_id == cuota.id
                )
            ).all()
            for pago in pagos:
                _eliminar_pago_sesion(session, pago)
            session.delete(cuota)
            session.flush()

        session.delete(deuda)
        session.commit()

    return True


# ---------------------------------------------------------------------------
# Lecturas
# ---------------------------------------------------------------------------


def _condiciones_listado(
    user: User,
    *,
    moneda_id: Optional[int],
    tipo_id: Optional[int],
    estado: Optional[str],
    modalidad: Optional[str],
    busqueda: Optional[str],
) -> list:
    condiciones = [DeudaMensual.user_id == str(user.id)]
    if moneda_id is not None:
        condiciones.append(DeudaMensual.moneda_id == moneda_id)
    if tipo_id is not None:
        condiciones.append(DeudaMensual.tipo_id == tipo_id)
    if estado is not None:
        if estado not in ESTADOS_DEUDA_MENSUAL:
            raise ValueError(f"Estado invalido: {estado!r}")
        condiciones.append(DeudaMensual.estado == estado)
    if modalidad is not None:
        if modalidad not in MODALIDADES:
            raise ValueError(f"Modalidad invalida: {modalidad!r}")
        condiciones.append(DeudaMensual.modalidad == modalidad)
    if busqueda:
        condiciones.append(DeudaMensual.descripcion.ilike(f"%{busqueda}%"))
    return condiciones


def listar_deudas_mensuales(
    user: User,
    *,
    moneda_id: Optional[int] = None,
    tipo_id: Optional[int] = None,
    estado: Optional[str] = None,
    modalidad: Optional[str] = None,
    busqueda: Optional[str] = None,
) -> list[dict]:
    hoy = date.today()
    with Session(engine) as session:
        condiciones = _condiciones_listado(
            user,
            moneda_id=moneda_id,
            tipo_id=tipo_id,
            estado=estado,
            modalidad=modalidad,
            busqueda=busqueda,
        )
        deudas = session.exec(
            select(DeudaMensual)
            .where(*condiciones)
            .order_by(DeudaMensual.created_at.desc(), DeudaMensual.id.desc())
        ).all()

        cuotas_por_deuda = _cuotas_por_deuda(
            session, [deuda.id for deuda in deudas]
        )
        resultados = []
        for deuda in deudas:
            cuotas = cuotas_por_deuda.get(deuda.id, [])
            resultados.append(
                {
                    "deuda_mensual": deuda,
                    "cuotas": cuotas,
                    **resumen_deuda_mensual(deuda, cuotas, hoy),
                }
            )
    return resultados


def obtener_deuda_mensual(user: User, deuda_mensual_id: int) -> dict:
    hoy = date.today()
    with Session(engine) as session:
        deuda = _validar_deuda_mensual(session, deuda_mensual_id, user)
        cuotas = session.exec(
            select(CuotaMensual)
            .where(CuotaMensual.deuda_mensual_id == deuda.id)
            .order_by(CuotaMensual.numero)
        ).all()
        pagos = session.exec(
            select(PagoCuotaMensual)
            .join(
                CuotaMensual,
                PagoCuotaMensual.cuota_id == CuotaMensual.id,
            )
            .where(CuotaMensual.deuda_mensual_id == deuda.id)
            .order_by(PagoCuotaMensual.fecha)
        ).all()
        pagos_por_cuota: dict[int, list[PagoCuotaMensual]] = {}
        for pago in pagos:
            pagos_por_cuota.setdefault(pago.cuota_id, []).append(pago)

        detalle = [
            {"cuota": cuota, "pagos": pagos_por_cuota.get(cuota.id, [])}
            for cuota in cuotas
        ]
        resumen = resumen_deuda_mensual(deuda, cuotas, hoy)

    return {
        "deuda_mensual": deuda,
        "cuotas": detalle,
        **resumen,
    }


def proximas_cuotas(
    user: User,
    *,
    dias: int = DIAS_PROXIMAS_DEFAULT,
    moneda_id: Optional[int] = None,
    hoy: Optional[date] = None,
) -> list[dict]:
    if dias < 0:
        raise ValueError("El numero de dias no puede ser negativo")

    hoy = hoy or date.today()
    limite = hoy + timedelta(days=dias)
    with Session(engine) as session:
        condiciones_deuda = [DeudaMensual.user_id == str(user.id)]
        if moneda_id is not None:
            condiciones_deuda.append(DeudaMensual.moneda_id == moneda_id)
        deudas = session.exec(
            select(DeudaMensual).where(*condiciones_deuda)
        ).all()

        deudas_por_id = {deuda.id: deuda for deuda in deudas}
        condiciones_cuota = [
            CuotaMensual.user_id == str(user.id),
            CuotaMensual.estado == ESTADO_CUOTA_PENDIENTE,
            CuotaMensual.fecha_limite <= limite,
        ]
        # Las cuotas ya pertenecen al usuario; solo hace falta acotar por
        # moneda, y se resuelve con una subconsulta en vez de un IN con todos
        # los ids de las plantillas (que es lo que encarecia esta lectura).
        if moneda_id is not None:
            condiciones_cuota.append(
                CuotaMensual.deuda_mensual_id.in_(
                    select(DeudaMensual.id).where(*condiciones_deuda)
                )
            )

        cuotas = session.exec(
            select(CuotaMensual)
            .where(*condiciones_cuota)
            .order_by(CuotaMensual.fecha_limite)
        ).all()

        resultados = [
            {
                "cuota": cuota,
                "deuda_mensual": deudas_por_id[cuota.deuda_mensual_id],
                "dias_restantes": (cuota.fecha_limite - hoy).days,
                "vencida": cuota.fecha_limite < hoy,
            }
            for cuota in cuotas
        ]
        resultados.sort(
            key=lambda item: clave_prioridad(
                item["cuota"].estado, item["cuota"].fecha_limite, hoy
            )
        )
    return resultados


def resumen_deudas_mensuales(
    user: User,
    *,
    moneda_id: Optional[int] = None,
    hoy: Optional[date] = None,
) -> dict:
    hoy = hoy or date.today()
    inicio_mes = date(hoy.year, hoy.month, 1)
    fin_mes = date(hoy.year, hoy.month, ultimo_dia_mes(hoy.year, hoy.month))
    limite_proximas = hoy + timedelta(days=DIAS_PROXIMAS_DEFAULT)

    with Session(engine) as session:
        condiciones_deuda = [DeudaMensual.user_id == str(user.id)]
        if moneda_id is not None:
            condiciones_deuda.append(DeudaMensual.moneda_id == moneda_id)
        deudas = session.exec(
            select(DeudaMensual).where(*condiciones_deuda)
        ).all()

        deudas_por_id = {deuda.id: deuda for deuda in deudas}
        condiciones_cuota = [CuotaMensual.user_id == str(user.id)]
        if moneda_id is not None:
            condiciones_cuota.append(
                CuotaMensual.deuda_mensual_id.in_(
                    select(DeudaMensual.id).where(*condiciones_deuda)
                )
            )

        cuotas = session.exec(
            select(CuotaMensual)
            .where(*condiciones_cuota)
            .order_by(CuotaMensual.fecha_limite)
        ).all()

        pagos_mes = session.exec(
            select(PagoCuotaMensual).where(
                PagoCuotaMensual.user_id == str(user.id),
                PagoCuotaMensual.fecha >= inicio_mes,
                PagoCuotaMensual.fecha <= fin_mes,
            )
        ).all()
        cuota_a_deuda = {
            cuota.id: deudas_por_id[cuota.deuda_mensual_id] for cuota in cuotas
        }

        activas = [c for c in cuotas if c.estado != ESTADO_CUOTA_CANCELADA]
        cuotas_mes = [
            c for c in activas if c.anio == hoy.year and c.mes == hoy.month
        ]
        pendientes = [
            c for c in cuotas if c.estado == ESTADO_CUOTA_PENDIENTE
        ]
        vencidas = [
            c for c in pendientes if es_vencida(c.estado, c.fecha_limite, hoy)
        ]
        proximas = [
            c
            for c in pendientes
            if hoy <= c.fecha_limite <= limite_proximas
        ]

        resultado = {
            "compromiso_mensual": round(
                sum(c.monto for c in cuotas_mes), 2
            ),
            "pendiente_total": round(
                sum(
                    monto_pendiente(
                        deudas_por_id[c.deuda_mensual_id], c, hoy
                    )
                    for c in cuotas
                ),
                2,
            ),
            "vencidas": {
                "cantidad": len(vencidas),
                "monto": round(sum(c.monto for c in vencidas), 2),
            },
            "proximas": {
                "cantidad": len(proximas),
                "monto": round(sum(c.monto for c in proximas), 2),
            },
            "pagado_mes": round(
                sum(
                    pago.monto
                    for pago in pagos_mes
                    if cuota_a_deuda.get(pago.cuota_id) is not None
                    and (
                        moneda_id is None
                        or cuota_a_deuda[pago.cuota_id].moneda_id
                        == moneda_id
                    )
                ),
                2,
            ),
            "cuotas_mes": len(cuotas_mes),
        }
    return resultado


# ---------------------------------------------------------------------------
# Pagos
# ---------------------------------------------------------------------------


def _pagar_cuota_sesion(
    session: Session,
    deuda: DeudaMensual,
    cuota: CuotaMensual,
    user: User,
    *,
    cuenta_id: Optional[int],
    fecha: Optional[date],
    descripcion: Optional[str],
    monto: Optional[float],
) -> PagoCuotaMensual:
    if cuota.estado != ESTADO_CUOTA_PENDIENTE:
        raise ValueError(
            f"La cuota {cuota.numero} no esta pendiente (estado "
            f"{cuota.estado})"
        )

    cuenta_final = (
        cuenta_id if cuenta_id is not None else deuda.cuenta_pago_default_id
    )
    if cuenta_final is None:
        raise ValueError("Debe indicar una cuenta de pago")
    _validar_cuenta(session, cuenta_final, user)

    monto_final = monto if monto is not None else cuota.monto
    validar_monto_pago(monto_final, cuota.monto)
    fecha_pago = fecha or date.today()

    movimiento = _crear_movimiento_sesion(
        session,
        monto=monto_movimiento_pago(monto_final),
        tipo_id=deuda.tipo_id,
        cuenta_id=cuenta_final,
        user=user,
        subtipo_id=deuda.subtipo_id,
        descripcion=(
            descripcion if descripcion is not None else deuda.descripcion
        ),
        fecha=fecha_pago,
        es_deuda=True,
    )

    pago = PagoCuotaMensual(
        user_id=str(user.id),
        cuota_id=cuota.id,
        monto=monto_final,
        fecha=fecha_pago,
        cuenta_id=cuenta_final,
        movimiento_id=movimiento.id,
        descripcion=descripcion,
    )
    session.add(pago)

    cuota.estado = ESTADO_CUOTA_PAGADA
    cuota.estado_pago = estado_pago_cuota(
        fecha_pago, cuota.fecha_aparicion, cuota.fecha_limite
    )
    session.add(cuota)
    session.flush()
    return pago


def _eliminar_pago_sesion(
    session: Session, pago: PagoCuotaMensual
) -> None:
    movimiento = session.get(Movimiento, pago.movimiento_id)
    session.delete(pago)
    session.flush()
    if movimiento is not None:
        _eliminar_movimiento_sesion(session, movimiento)


def pagar_cuota(
    user: User,
    cuota_id: int,
    *,
    cuenta_id: Optional[int] = None,
    fecha: Optional[date] = None,
    descripcion: Optional[str] = None,
    monto: Optional[float] = None,
) -> PagoCuotaMensual:
    with Session(engine) as session:
        cuota = _validar_cuota(session, cuota_id, user)
        deuda = _validar_deuda_mensual(
            session, cuota.deuda_mensual_id, user
        )
        pago = _pagar_cuota_sesion(
            session,
            deuda,
            cuota,
            user,
            cuenta_id=cuenta_id,
            fecha=fecha,
            descripcion=descripcion,
            monto=monto,
        )
        session.commit()
        session.refresh(pago)

    return pago


def pagar_cuotas(
    user: User,
    cuota_ids: list[int],
    *,
    cuenta_id: Optional[int] = None,
    fecha: Optional[date] = None,
    descripcion: Optional[str] = None,
) -> list[PagoCuotaMensual]:
    """Paga varias cuotas en una sola transaccion (todo o nada)."""
    if not cuota_ids:
        raise ValueError("Debe indicar al menos una cuota")

    with Session(engine) as session:
        pagos: list[PagoCuotaMensual] = []
        for cuota_id in cuota_ids:
            cuota = _validar_cuota(session, cuota_id, user)
            deuda = _validar_deuda_mensual(
                session, cuota.deuda_mensual_id, user
            )
            pagos.append(
                _pagar_cuota_sesion(
                    session,
                    deuda,
                    cuota,
                    user,
                    cuenta_id=cuenta_id,
                    fecha=fecha,
                    descripcion=descripcion,
                    monto=None,
                )
            )

        session.commit()
        for pago in pagos:
            session.refresh(pago)

    return pagos


def editar_pago(
    user: User,
    cuota_id: int,
    pago_id: int,
    *,
    cuenta_id: Optional[int] = None,
    fecha: Optional[date] = None,
    descripcion: Optional[str] = None,
    monto: Optional[float] = None,
) -> PagoCuotaMensual:
    with Session(engine) as session:
        cuota = _validar_cuota(session, cuota_id, user)
        pago = _validar_pago(session, cuota_id, pago_id, user)
        _validar_deuda_mensual(session, cuota.deuda_mensual_id, user)

        monto_final = monto if monto is not None else pago.monto
        validar_monto_pago(monto_final, cuota.monto)
        cuenta_final = (
            cuenta_id if cuenta_id is not None else pago.cuenta_id
        )
        if cuenta_id is not None:
            _validar_cuenta(session, cuenta_id, user)
        fecha_final = fecha if fecha is not None else pago.fecha
        descripcion_final = (
            descripcion if descripcion is not None else pago.descripcion
        )

        movimiento = session.get(Movimiento, pago.movimiento_id)
        if movimiento is None:
            raise ValueError(
                f"Movimiento {pago.movimiento_id} no encontrado"
            )

        _actualizar_movimiento_sesion(
            session,
            movimiento,
            monto=monto_movimiento_pago(monto_final),
            cuenta_id=cuenta_final,
            descripcion=descripcion_final,
            fecha=fecha_final,
        )

        pago.monto = monto_final
        pago.cuenta_id = cuenta_final
        pago.fecha = fecha_final
        pago.descripcion = descripcion_final
        session.add(pago)

        cuota.estado_pago = estado_pago_cuota(
            fecha_final, cuota.fecha_aparicion, cuota.fecha_limite
        )
        session.add(cuota)

        session.commit()
        session.refresh(pago)

    return pago


def eliminar_pago(user: User, cuota_id: int, pago_id: int) -> bool:
    with Session(engine) as session:
        cuota = _validar_cuota(session, cuota_id, user)
        pago = _validar_pago(session, cuota_id, pago_id, user)
        _validar_deuda_mensual(session, cuota.deuda_mensual_id, user)

        _eliminar_pago_sesion(session, pago)
        cuota.estado = ESTADO_CUOTA_PENDIENTE
        cuota.estado_pago = None
        session.add(cuota)
        session.commit()

    return True


def moneda_distinta(
    user: User, cuota_id: int, cuenta_id: int
) -> bool:
    """True si la cuenta del pago usa otra moneda que la deuda mensual."""
    with Session(engine) as session:
        cuota = _validar_cuota(session, cuota_id, user)
        deuda = _validar_deuda_mensual(
            session, cuota.deuda_mensual_id, user
        )
        cuenta = _validar_cuenta(session, cuenta_id, user)
        return monedas_distintas(deuda.moneda_id, cuenta.moneda_id)


def monedas_por_cuenta(user: User) -> dict[int, int]:
    """Mapa ``cuenta_id -> moneda_id`` del usuario en una sola consulta.

    Lo usan las respuestas de detalle para no abrir una sesion por cada pago
    al calcular ``moneda_distinta``.
    """
    with Session(engine) as session:
        filas = session.exec(
            select(Cuenta.id, Cuenta.moneda_id).where(
                Cuenta.user_id == str(user.id)
            )
        ).all()
    return {int(cuenta_id): int(moneda_id) for cuenta_id, moneda_id in filas}
